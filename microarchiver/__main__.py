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


# Constants.
# ......................................................................

_URL_ARTICLES_LIST = 'https://www.micropublication.org/archive-list/'


# Main program.
# ......................................................................

@plac.annotations(
    articles   = ('get articles listed in file A (default: use network)', 'option', 'a'),
    output_dir = ('write results to directory O (default: current dir)',  'option', 'o'),
    quiet      = ('do not print informational messages while working',    'flag',   'q'),
    no_color   = ('do not color-code terminal output',                    'flag',   'C'),
    version    = ('print version info and exit',                          'flag',   'V'),
    debug      = ('turn on debugging',                                    'flag',   'Z'),
)

def main(articles = 'A', output_dir = 'O', quiet = False,
         no_color = False, version = False, debug = False):

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
    elif not readable(articles):
        exit(say.fatal_text('File not readable: {}', articles))
    elif not articles.endswith('.xml'):
        exit(say.fatal_text('Does not appear to be an XML file: {}', articles))

    if output_dir == 'O':
        output_dir = '.'
    if not path.isabs(output_dir):
        output_dir = path.realpath(path.join(os.getcwd(), output_dir))
    if path.isdir(output_dir):
        if not writable(output_dir):
            exit(say.fatal_text('Directory not writable: {}', output_dir))
    else:
        exit(say.fatal_text('Not a directory: {}', output_dir))

    # Do the real work --------------------------------------------------------

    if not network_available():
        exit(say.fatal_text('No network.'))

    try:
        if articles:
            say.info('Reading articles list from XML file {}', articles)
            articles_list = articles_from_xml(articles)
        else:
            say.info('Fetching articles list from ', _URL_ARTICLES_LIST)
            articles_list = articles_from_xml(_URL_ARTICLES_LIST)

        say.info('Output will be written under directory "{}"', output_dir)
        import pdb; pdb.set_trace()

    except (KeyboardInterrupt, UserCancelled) as ex:
        exit(say.msg('Quitting.', 'error'))
    except Exception as ex:
        if debug:
            say.error('{}\n{}', str(ex), traceback.format_exc())
            import pdb; pdb.set_trace()
        else:
            exit(say.error_text('{}', str(ex)))



# If this is windows, we want the command-line args to use slash intead
# of hyphen.

if sys.platform.startswith('win'):
    main.prefix_chars = '/'


# Miscellaneous utilities.
# ......................................................................

def print_version():
    print('{} version {}'.format(microarchiver.__title__, microarchiver.__version__))
    print('Author: {}'.format(microarchiver.__author__))
    print('URL: {}'.format(microarchiver.__url__))
    print('License: {}'.format(microarchiver.__license__))


def articles_from_xml(file_or_url):
    '''Returns a list of tuples (doi, date, pdf-url).'''
    # Read the XML.
    if file_or_url.startswith('http'):
        (response, error) = net('get', file_or_url)
        if not error and response and response.text:
            # The micropublication xml declaration explicit uses ascii encoding.
            xml = response.text.encode('ascii')
        elif error:
            if isinstance(error, NoContent):
                say.fatal('Server returned no content')
                raise
            elif isinstance(error, ServiceFailure):
                say.fatal('Server failure -- try again later')
                raise
            else:
                raise error
        else:
            raise InternalError('Unexpected response from server')
    else: # Assume it's a file.
        with open(file_or_url, 'rb') as xml_file:
            xml = xml_file.readlines()

    # Parse the XML.
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
        articles.append((doi, date, pdf))

    return articles


# Main entry point.
# ......................................................................
# The following allows users to invoke this using "python3 -m microarchiver".

if __name__ == '__main__':
    plac.call(main)


# For Emacs users
# ......................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:
