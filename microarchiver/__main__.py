'''
__main__: main command-line interface to Microarchiver

Authors
-------

Tom Morrell <tmorrell@caltech.edu> -- Caltech Library
Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2019 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

from   collections import namedtuple
import humanize
from   lxml import etree
import os
import os.path as path
import plac
import sys
import traceback

import microarchiver
from microarchiver.debug import set_debug, log
from microarchiver.exceptions import *
from microarchiver.files import readable, writable, make_dir
from microarchiver.messages import MessageHandler
from microarchiver.network import net, network_available


# Simple data type definitions.
# .............................................................................

Article = namedtuple('Article', 'doi date url')


# Constants.
# .............................................................................

_URL_ARTICLES_LIST = 'https://www.micropublication.org/archive-list/'


# Main program.
# .............................................................................

@plac.annotations(
    articles = ('get articles list from file A (default: from network)', 'option', 'a'),
    dest_dir = ('write archive in directory D (default: current dir)',   'option', 'd'),
    dry_run  = ('only print the articles list; do not create archive',   'flag',   'n'),
    report   = ('write report to file R (default: print to terminal)',   'option', 'r'),
    quiet    = ('do not print informational messages while working',     'flag',   'q'),
    no_color = ('do not color-code terminal output',                     'flag',   'C'),
    version  = ('print version info and exit',                           'flag',   'V'),
    debug    = ('turn on debugging',                                     'flag',   'Z'),
)

def main(articles = 'A', dest_dir = 'D', report = 'R', dry_run = False,
         quiet = False, no_color = False, version = False, debug = False):

    # Initial setup -----------------------------------------------------------

    say = MessageHandler(not no_color, quiet)
    prefix = '/' if sys.platform.startswith('win') else '-'
    hint = '(Hint: use {}h for help.)'.format(prefix)

    # Process arguments -------------------------------------------------------

    if debug:
        set_debug(True)
    if version:
        print_version()
        exit()

    # We use default values that provide more intuitive help text printed by
    # plac.  Rewrite the values to things we actually use.
    if articles == 'A':
        articles = None
    if dest_dir == 'D':
        dest_dir = '.'
    if report == 'R':
        report = None

    # Do the real work --------------------------------------------------------

    try:
        MainBody(articles, dest_dir, report, dry_run, say).run()
    except (KeyboardInterrupt, UserCancelled) as ex:
        exit(say.error_text('Quitting'))
    except Exception as ex:
        if debug:
            say.error('{}\n{}', str(ex), traceback.format_exc())
            import pdb; pdb.set_trace()
        else:
            exit(say.error_text('{}', str(ex)))


class MainBody(object):
    '''Main body for Microarchiver.'''

    def __init__(self, articles, dest_dir, report, dry_run, say):
        '''Initialize internal variables.'''
        self._articles = articles
        self._dest_dir = dest_dir
        self._report   = report
        self._dry_run  = dry_run
        self._say      = say


    def run(self):
        '''Execute the control logic.'''

        # Set shortcut variables for better code readability below.
        articles = self._articles
        dest_dir = self._dest_dir
        dry_run  = self._dry_run
        say      = self._say

        # Preliminary sanity checks.
        if not network_available():
            exit(say.fatal_text('No network.'))
        if articles and not readable(articles):
            exit(say.fatal_text('File not readable: {}', articles))
        if articles and not articles.endswith('.xml'):
            exit(say.fatal_text('Does not appear to be an XML file: {}', articles))
        if not path.isabs(dest_dir):
            dest_dir = path.realpath(path.join(os.getcwd(), dest_dir))
        if path.isdir(dest_dir):
            if not writable(dest_dir):
                exit(say.fatal_text('Directory not writable: {}', dest_dir))
        else:
            exit(say.fatal_text('Not a directory: {}', dest_dir))

        # If we get this far, we're ready to do this thing.
        if articles:
            say.info('Reading articles list from XML file {}', articles)
            articles_list = self.articles_from_xml(articles)
        else:
            say.info('Fetching articles list from {}', _URL_ARTICLES_LIST)
            articles_list = self.articles_from_xml(_URL_ARTICLES_LIST)

        say.info('Total articles: {}', humanize.intcomma(len(articles_list)))
        if dry_run:
            self.print_articles(articles_list)
        else:
            say.info('Output will be written under directory "{}"', dest_dir)


    def articles_from_xml(self, file_or_url):
        '''Returns a list of tuples (doi, date, pdf-url).'''
        # Read the XML.
        if file_or_url.startswith('http'):
            (response, error) = net('get', file_or_url)
            if not error and response and response.text:
                # The micropublication xml declaration explicit uses ascii encoding.
                xml = response.text.encode('ascii')
            elif error:
                if __debug__: log('error reading from micropublication.org server')
                if isinstance(error, NoContent):
                    self._say.fatal('Server returned no content')
                    raise
                elif isinstance(error, ServiceFailure):
                    self._say.fatal('Server failure -- try again later')
                    raise
                else:
                    raise error
            else:
                raise InternalError('Unexpected response from server')
        else: # Assume it's a file.
            if __debug__: log('reading {}', file_or_url)
            with open(file_or_url, 'rb') as xml_file:
                xml = xml_file.readlines()

        # Parse the XML.
        if __debug__: log('parsing XML data')
        nodes = etree.fromstring(xml)
        articles = []
        for element in nodes.findall('article'):
            pdf   = element.find('pdf-url').text
            doi   = element.find('doi').text
            title = element.find('article-title').text
            date  = element.find('date-published')
            if date != None:
                year = date.find('year').text
                month = date.find('month').text
                day = date.find('day').text
                date = year + '-' + month + '-' + day
            else:
                date = ''
            articles.append(Article(doi, date, pdf))

        return articles


    def print_articles(self, articles_list):
        self._say.info('-'*79)
        self._say.info('[{:3}] {:<32}  {:10}  {:20}'.format('  #', 'DOI', 'Date', 'URL'))
        self._say.info('-'*79)
        count = 0
        for article in articles_list:
            count += 1
            self._say.info('[{:3}] {:<32}  {:10}  {:20}'.format(
                count,
                article.doi if article.doi else self._say.warn_text('missing'),
                article.date if article.date else self._say.warn_text('missing'),
                article.url if article.url else self._say.warn_text('missing')))
        self._say.info('-'*79)


# Miscellaneous utilities.
# .............................................................................

def print_version():
    print('{} version {}'.format(microarchiver.__title__, microarchiver.__version__))
    print('Author: {}'.format(microarchiver.__author__))
    print('URL: {}'.format(microarchiver.__url__))
    print('License: {}'.format(microarchiver.__license__))


# Main entry point.
# .............................................................................
# The following allows users to invoke this using "python3 -m microarchiver".

if sys.platform.startswith('win'):
    # When running on Windows, we want the command-line args to use the slash
    # character intead of hyphen.
    main.prefix_chars = '/'

if __name__ == '__main__':
    plac.call(main)


# For Emacs users
# .............................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:
