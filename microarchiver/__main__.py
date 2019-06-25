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

import base64
from   collections import namedtuple
import csv
import datetime
import humanize
import json as jsonlib
from   lxml import etree
import os
import os.path as path
import plac
import sys
import traceback
import xmltodict

import microarchiver
from microarchiver.debug import set_debug, log
from microarchiver.exceptions import *
from microarchiver.files import readable, writable, file_in_use, rename_existing
from microarchiver.files import make_dir, create_archive, verify_archive
from microarchiver.messages import MessageHandler
from microarchiver.network import net, network_available


# Simple data type definitions.
# .............................................................................

Article = namedtuple('Article', 'doi date title url status')
'''
Named tuple used internally to communicate information about articles in the
article list.  The value of the "status" field can be as follows, and will
be different at different times in the process of getting information from
micropublication.org and writing out information for portico:

  'complete'   -- the info in the XML article list is complete
  'incomplete' -- something is missing in the XML article list entry
  'failed'     -- failed to download the article from the server
'''


# Constants.
# .............................................................................

_URL_ARTICLES_LIST = 'https://www.micropublication.org/archive-list/'

_DATACITE_API_URL = 'https://api.datacite.org/dois/'

_MICROPUBLICATION_ISSN = '2578-9430'


# Main program.
# .............................................................................

@plac.annotations(
    articles   = ('get articles list from file A (default: from network)', 'option', 'a'),
    dest_dir   = ('write archive in directory D (default: current dir)',   'option', 'd'),
    dry_run    = ('only print the articles list; do not create archive',   'flag',   'n'),
    report     = ('write report to file R (default: print to terminal)',   'option', 'r'),
    quiet      = ('do not print informational messages while working',     'flag',   'q'),
    no_archive = ('do not zip up the output directory (default: do)',      'flag',   'A'),
    no_color   = ('do not color-code terminal output',                     'flag',   'C'),
    version    = ('print version info and exit',                           'flag',   'V'),
    debug      = ('turn on debugging',                                     'flag',   'Z'),
)

def main(articles = 'A', dest_dir = 'D', report = 'R', dry_run = False,
         quiet = False, no_archive = False, no_color = False,
         version = False, debug = False):
    '''Archive micropublication.org publications for Portico.

By default, this program will contact micropublication.org to get a list of
current articles. If given the argument -a (or /a on Windows) followed by a
file name, the given file will be read instead instead of getting the list from
the server. The contents of the file must be in the same XML format as the list
obtain from micropublication.org.

The output will be written to the directory indicated by the value of the
argument -d (or /d on Windows). If no -d is given, the output will be written
to the current directory instead. The output directory will also be put into
a single-file archive in ZIP format unless the argument -A (or /A on Windows)
is given to prevent creation of the compressed archive file.

As it works, microarchiver writes information to the terminal about the archives
it puts into the archive, including whether any problems are encountered. To
save this info to a file, use the argument -r (or /r on Windows).

Additional command-line arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If given the argument -n (or /n on Windows), microarchiver will ONLY display a
list of articles it will archive and stop short of creating the archive. This
is useful to see what would be produced without actually doing it.

Microarchiver will print informational messages as it works. To reduce messages
to only warnings and errors, use the argument -q (or /q on Windows). Also,
output is color-coded by default unless the -C argument (or /C on Windows) is
given; this argument can be helpful if the color control signals create
problems for your terminal emulator.

If given the -V argument (/V on Windows), this program will print version
information and exit without doing anything else.

Command-line arguments summary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
'''
    # Initial setup -----------------------------------------------------------

    say = MessageHandler(not no_color, quiet)
    prefix = '/' if sys.platform.startswith('win') else '-'
    hint = '(Use {}h for help.)'.format(prefix)
    do_archive = not no_archive

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
        dest_dir = 'micropublication-org'
    if report == 'R':
        report = None
    if dry_run and quiet:
        exit(say.error_text('Option {}q is incompatible with {}n. {}'.format(
            prefix, prefix, hint)))

    # Do the real work --------------------------------------------------------

    try:
        MainBody(articles, dest_dir, report, do_archive, dry_run, say).run()
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

    def __init__(self, articles, dest_dir, report_file, do_archive, dry_run, say):
        '''Initialize internal variables.'''
        self._articles    = articles
        self._dest_dir    = dest_dir
        self._report_file = report_file
        self._do_archive  = do_archive
        self._dry_run     = dry_run
        self._say         = say


    def run(self):
        '''Execute the control logic.'''

        # Set shortcut variables for better code readability below.
        articles    = self._articles
        dest_dir    = self._dest_dir
        report_file = self._report_file
        do_archive  = self._do_archive
        dry_run     = self._dry_run
        say         = self._say

        # Preliminary sanity checks.
        if not network_available():
            raise ServiceFailure('No network.')
        if articles and not readable(articles):
            raise RuntimeError('File not readable: {}', articles)
        if articles and not articles.endswith('.xml'):
            raise RuntimeError('Does not appear to be an XML file: {}', articles)
        if not path.isabs(dest_dir):
            dest_dir = path.realpath(path.join(os.getcwd(), dest_dir))
        if path.isdir(dest_dir):
            if not writable(dest_dir):
                raise RuntimeError('Directory not writable: {}', dest_dir)
        else:
            if path.exists(dest_dir):
                raise ValueError('Not a directory: {}', dest_dir)
            elif not dry_run:
                make_dir(dest_dir)
        if report_file and file_in_use(report_file):
            raise RuntimeError("Cannot write file becase it's in use: {}", report_file)

        # If we get this far, we're ready to do this thing.
        if articles:
            say.info('Reading articles list from XML file {}', articles)
            articles_list = self.articles_from_xml(articles)
        else:
            say.info('Fetching articles list from {}', _URL_ARTICLES_LIST)
            articles_list = self.articles_from_xml(_URL_ARTICLES_LIST)

        num_articles = len(articles_list)
        say.info('Total articles: {}', humanize.intcomma(num_articles))
        if dry_run:
            self.print_articles(articles_list)
        else:
            say.info('Output will be written under directory "{}"', dest_dir)
            self.write_articles(dest_dir, articles_list)
            if do_archive:
                archive_file = dest_dir + '.zip'
                say.info('Creating ZIP archive file "{}"', archive_file)
                comments = file_comments(num_articles)
                create_archive(archive_file, '.zip', dest_dir, comments)
        if report_file:
            if path.exists(report_file):
                rename_existing(report_file)
            say.info('Writing report to ' + report_file)
            self.write_report(report_file, articles_list)


    def articles_from_xml(self, file_or_url):
        '''Returns a list of `Article` tuples from the given URL or file.'''
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
        return self._article_tuples(xml)


    def _article_tuples(self, xml):
        '''Parse the XML input, assumed to be from micropublication.org, and
        create a list of `Article` named tuples.
        '''
        if __debug__: log('parsing XML data')
        articles = []
        for element in etree.fromstring(xml).findall('article'):
            pdf   = (element.find('pdf-url').text or '').strip()
            doi   = (element.find('doi').text or '').strip()
            title = (element.find('article-title').text or '').strip()
            date  = element.find('date-published')
            if date != None:
                year  = (date.find('year').text or '').strip()
                month = (date.find('month').text or '').strip()
                day   = (date.find('day').text or '').strip()
                date  = year + '-' + month + '-' + day
            else:
                date = ''
            status = 'incomplete' if not(all([pdf, doi, title, date])) else 'complete'
            articles.append(Article(doi, date, title, pdf, status))
        return articles


    def print_articles(self, articles_list):
        self._say.info('-'*89)
        self._say.info('{:3}  {:<32}  {:10}  {:20}'.format(
            '?', 'DOI', 'Date', 'URL (https://micropublication.org)'))
        self._say.info('-'*89)
        count = 0
        for article in articles_list:
            count += 1
            self._say.info('{:3}  {:<32}  {:10}  {:20}'.format(
                self._say.error_text('err') if article.status == 'incomplete' else 'OK',
                article.doi if article.doi else self._say.error_text('missing DOI'),
                article.date if article.date else self._say.error_text('missing date'),
                short(article.url) if article.url else self._say.error_text('missing URL')))
        self._say.info('-'*89)


    def write_report(self, report_file, articles_list):
        if __debug__: log('writing report file {}', report_file)
        try:
            with open(report_file, 'w', newline='') as file:
                file.write('Status,DOI,Date,URL\n')
                csvwriter = csv.writer(file, delimiter=',')
                for article in articles_list:
                    row = [article.status, article.doi, article.date, article.url]
                    csvwriter.writerow(row)
        except Exception as ex:
            if __debug__: log('error writing csv file: {}', str(ex))
            raise


    def write_articles(self, dest_dir, article_list):
        for article in article_list:
            if not article.doi:
                self._say.warn('Skipping article with missing DOI: ' + article.title)
                article.status = 'missing-doi'
                continue
            xml = self._metadata_xml(article)
            if not xml:
                self._say.warn('Skipping article with no DataCite entry: ' + article.doi)
                article.status = 'failed-datacite'
                continue
            article_dir = path.join(dest_dir, tail_of_doi(article))
            try:
                os.makedirs(article_dir)
            except FileExistsError:
                pass
            dest_file = path.join(article_dir, xml_filename(article))
            self._say.info('Writing ' + article.doi)
            with open(dest_file, 'w', encoding = 'utf8') as xml_file:
                if __debug__: log('writing XML to {}', dest_file)
                xml_file.write(xmltodict.unparse(xml))
        return article_list


    def _metadata_xml(self, article):
        (response, error) = net('get', _DATACITE_API_URL + article.doi)
        if error:
            if __debug__: log('error reading from datacite for {}', article.doi)
            raise error
        elif not response:
            if __debug__: log('empty response from datacite for {}', article.doi)
            raise InternalError('Unexpected response from datacite server')

        json = response.json()
        xml = xmltodict.parse(base64.b64decode(json['data']['attributes']['xml']))
        date = json['data']['attributes']['registered']
        if 'dates' in xml['resource']:
            xml['resource']['dates']['date']['#text'] = date
        else:
            xml['resource']['dates'] = {'date': article.date}
        xml['resource']['volume']  = volume_for_year(xml['resource']['publicationYear'])
        xml['resource']['file']    = pdf_filename(article)
        xml['resource']['journal'] = xml['resource'].pop('publisher')
        xml['resource']['e-issn']  = _MICROPUBLICATION_ISSN
        xml['resource']["rightsList"] = [{
            "rights": "Creative Commons Attribution 4.0",
            "rightsURI": "https://creativecommons.org/licenses/by/4.0/legalcode"}]
        xml['resource'].pop('@xmlns')
        xml['resource'].pop('@xsi:schemaLocation')
        return xml


# Miscellaneous utilities.
# .............................................................................

def print_version():
    print('{} version {}'.format(microarchiver.__title__, microarchiver.__version__))
    print('Author: {}'.format(microarchiver.__author__))
    print('URL: {}'.format(microarchiver.__url__))
    print('License: {}'.format(microarchiver.__license__))


def short(url):
    return url.replace('https://www.micropublication.org', '')


def volume_for_year(year):
    return int(year) - 2014


def tail_of_doi(article):
    slash = article.doi.rfind('/')
    return article.doi[slash + 1:]


def pdf_filename(article):
    return tail_of_doi(article) + '.pdf'


def xml_filename(article):
    return tail_of_doi(article) + '.xml'


def file_comments(num_articles):
    text  = '~ '*35
    text += '\n'
    text += 'About this ZIP archive file:\n'
    text += '\n'
    text += 'This archive contains a directory of articles from microPublication.org\n'
    text += 'created on {}. There are {} articles in this archive.'.format(
        str(datetime.date.today()), num_articles)
    text += '\n'
    text += software_comments()
    text += '\n'
    text += '~ '*35
    text += '\n'
    return text


def software_comments():
    text  = '\n'
    text += 'The software used to create this archive file was:\n'
    text += '{} version {} <{}>'.format(
        microarchiver.__title__, microarchiver.__version__, microarchiver.__url__)
    return text


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
