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
import dateparser
import datetime
import humanize
import json as jsonlib
from   lxml import etree
import os
import os.path as path
import plac
from   recordclass import recordclass
import shutil
import sys
import traceback
import xmltodict

import microarchiver
from microarchiver.debug import set_debug, log
from microarchiver.exceptions import *
from microarchiver.files import readable, writable, file_in_use, rename_existing
from microarchiver.files import make_dir, create_archive, verify_archive
from microarchiver.messages import MessageHandler
from microarchiver.network import net, network_available, download


# Simple data type definitions.
# .............................................................................

Article = recordclass('Article', 'doi date title pdf status')
'''
Record class used internally to communicate information about articles in the
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

_ARCHIVE_DIR_NAME = 'micropublication-org'

_DATE_PRINT_FORMAT = '%b %d %Y %H:%M:%S %Z'
'''Format in which lastmod date is printed back to the user. The value is used
with datetime.strftime().'''


# Main program.
# .............................................................................

@plac.annotations(
    articles   = ('get articles list from file A (default: from network)',  'option', 'a'),
    no_color   = ('do not color-code terminal output',                      'flag',   'C'),
    after_date = ('only get articles published after date "D"',             'option', 'd'),
    get_xml    = ('print the current archive list from the server & exit',  'flag',   'g'),
    output_dir = ('write archive in directory O (default: current dir)',    'option', 'o'),
    preview    = ('preview the list of articles that would be downloaded',  'flag',   'p'),
    quiet      = ('only print important diagnostic messages while working', 'flag',   'q'),
    report     = ('write report to file R (default: print to terminal)',    'option', 'r'),
    version    = ('print version information and exit',                     'flag',   'V'),
    no_zip     = ('do not zip up the output directory (default: do)',       'flag',   'Z'),
    debug      = ('write detailed trace to "OUT" (use "-" for console)',    'option', '@'),
)

def main(articles = 'A', no_color = False, after_date = 'D', get_xml = False,
         output_dir = 'O', preview = False, quiet = False, report = 'R',
         version = False, no_zip = False, debug = 'OUT'):
    '''Archive micropublication.org publications for Portico.

By default, this program will contact micropublication.org to get a list of
current articles. If given the argument -a (or /a on Windows) followed by a
file name, the given file will be read instead instead of getting the list from
the server. The contents of the file must be in the same XML format as the list
obtain from micropublication.org; see option -g, described below, for a way to
get the current article list from the server.

The output will be written to the directory indicated by the value of the
argument -o (or /o on Windows). If no -o is given, the output will be written
to the current directory instead. The output will be put into a single-file
archive in ZIP format unless the argument -Z (or /Z on Windows) is given to
prevent creation of the compressed archive file.

If the option -d is given, microarchiver will download only articles whose
publication dates are AFTER the given date.  Valid date descriptors are those
accepted by the Python dateparser library.  Make sure to enclose descriptions
within single or double quotes.  Examples:

  microarchiver -d "2014-08-29"   ....
  microarchiver -d "12 Dec 2014"  ....
  microarchiver -d "July 4, 2013"  ....
  microarchiver -d "2 weeks ago"  ....

As it works, microarchiver writes information to the terminal about the archives
it puts into the archive, including whether any problems are encountered. To
save this info to a file, use the argument -r (or /r on Windows).

Additional command-line arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If given the argument -g (or /g on Windows), microarchiver will write to
standard output the complete current article list from the micropublication.org
server, in XML format, and exit without doing anything else.  This is useful
as a starting point for creating the file used by option -a.  It's probably a
good idea to redirect the output to a file; e.g.,

  microarchiver -g > article-list.xml

If given the argument -p (or /p on Windows), microarchiver will ONLY display a
list of articles it will archive and stop short of creating the archive. This
is useful to see what would be produced without actually doing it.

Microarchiver will print informational messages as it works. To reduce messages
to only warnings and errors, use the argument -q (or /q on Windows). Also,
output is color-coded by default unless the -C argument (or /C on Windows) is
given; this argument can be helpful if the color control signals create
problems for your terminal emulator.

If given the -V argument (/V on Windows), this program will print version
information and exit without doing anything else.

If given the -@ argument (/@ on Windows), this program will output a detailed
trace of what it is doing to the terminal window, and will also drop into a
debugger upon the occurrence of any errors.  The debug trace will be sent to
the given destination, which can be '-' to indicate console output, or a file
path to send the output to a file.

Command-line arguments summary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
'''
    # Initial setup -----------------------------------------------------------

    say    = MessageHandler(not no_color, quiet)
    prefix = '/' if sys.platform.startswith('win') else '-'
    hint   = '(Use {}h for help.)'.format(prefix)
    do_zip = not no_zip

    # Process arguments -------------------------------------------------------

    # We use default values that provide more intuitive help text printed by
    # plac.  Rewrite the values to things we actually use.
    source     = articles if articles != 'A' else None
    after      = None if after_date == 'D' else after_date
    output_dir = '.' if output_dir == 'O' else output_dir
    report     = None if report == 'R' else report

    if debug != 'OUT':
        set_debug(True, debug)
    if version:
        print_version()
        exit()
    if preview and quiet:
        text = 'Option {}q is incompatible with {}n. {}'.format(prefix, prefix, hint)
        exit(say.error_text(text))

    # Do the real work --------------------------------------------------------

    try:
        MainBody(source, after, output_dir, do_zip, report, get_xml, preview, say).run()
    except (KeyboardInterrupt, UserCancelled) as ex:
        exit(say.error_text('Quitting'))
    except Exception as ex:
        if debug:
            say.error('{}\n{}', str(ex), traceback.format_exc())
            import pdb; pdb.set_trace()
        else:
            exit(say.error_text('{}'.format(str(ex))))


class MainBody(object):
    '''Main body for Microarchiver.'''

    def __init__(self, source, after_date, output_dir, do_zip, report, get_xml, preview, say):
        '''Initialize internal state and prepare for running services.'''

        # Preliminary sanity checks.
        if not network_available():
            raise ServiceFailure('No network.')

        if get_xml:
            if __debug__: log('Fetching articles from server')
            print(self.get_articles_list())
            exit()

        if source and not readable(source):
            raise RuntimeError('File not readable: {}'.format(source))
        if source and not source.endswith('.xml'):
            raise RuntimeError('Does not appear to be an XML file: {}'.format(source))

        if not path.isabs(output_dir):
            output_dir = path.realpath(path.join(os.getcwd(), output_dir))
        if path.isdir(output_dir):
            if not writable(output_dir):
                raise RuntimeError('Directory not writable: {}'.format(output_dir))
        else:
            if path.exists(output_dir):
                raise ValueError('Not a directory: {}'.format(output_dir))
        dest_dir = path.join(output_dir, _ARCHIVE_DIR_NAME)

        if report and file_in_use(report):
            raise RuntimeError("File is in use by another process: {}".format(report))

        if after_date:
            try:
                after_date = parse_datetime(after_date)
                if __debug__: log('Parsed after_date as {}', after_date)
            except Exception as ex:
                raise RuntimeError('Unable to parse date: {}'.format(str(ex)))

        # Store the values we'll use.
        self._source     = source
        self._after_date = after_date
        self._dest_dir   = dest_dir
        self._do_zip     = do_zip
        self._report     = report
        self._preview    = preview
        self._say        = say


    def run(self):
        '''Execute the control logic.'''

        # Set shortcut variables for better code readability below.
        source     = self._source
        after_date = self._after_date
        dest_dir   = self._dest_dir
        report     = self._report
        do_zip     = self._do_zip
        preview = self._preview
        say        = self._say

        # Read the article list, then do optional filtering for date.
        if source:
            say.info('Reading articles list from XML file {}', source)
            articles = self.articles_from_xml(source)
        else:
            say.info('Fetching articles list from {}', _URL_ARTICLES_LIST)
            articles = self.articles_from_xml(_URL_ARTICLES_LIST)

        if after_date:
            after_date_str = after_date.strftime(_DATE_PRINT_FORMAT)
            say.info('Will only keep articles published after {}', after_date_str)
            articles = [x for x in articles if parse_datetime(x.date) > after_date]

        num_articles = len(articles)
        say.info('Total articles: {}', humanize.intcomma(num_articles))
        if preview:
            self.print_articles(articles)
        else:
            if num_articles == 0:
                say.info('No articles to archive')
            else:
                say.info('Output will be written to directory "{}"', dest_dir)
                if not preview:
                    make_dir(dest_dir)
                self.write_articles(dest_dir, articles)
                if do_zip:
                    archive_file = dest_dir + '.zip'
                    say.info('Creating ZIP archive file "{}"', archive_file)
                    comments = file_comments(num_articles)
                    create_archive(archive_file, '.zip', dest_dir, comments)
                    say.info('Deleting directory "{}"', dest_dir)
                    shutil.rmtree(dest_dir)
        if report:
            if path.exists(report):
                rename_existing(report)
            say.info('Writing report to ' + report)
            self.write_report(report, articles)


    def get_articles_list(self):
        '''Write to standard output the XML article list from the server.'''
        (response, error) = net('get', _URL_ARTICLES_LIST)
        if not error and response and response.text:
            # The micropublication xml declaration explicit uses ascii encoding.
            return response.text
        else:
            return ''


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
        create a list of `Article` records.
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
                short(article.pdf) if article.pdf else self._say.error_text('missing URL')))
        self._say.info('-'*89)


    def write_report(self, report_file, articles_list):
        if __debug__: log('writing report file {}', report_file)
        try:
            with open(report_file, 'w', newline='') as file:
                file.write('Status,DOI,Date,URL\n')
                csvwriter = csv.writer(file, delimiter=',')
                for article in articles_list:
                    row = [article.status, article.doi, article.date, article.pdf]
                    csvwriter.writerow(row)
        except Exception as ex:
            if __debug__: log('error writing csv file: {}', str(ex))
            raise


    def write_articles(self, dest_dir, article_list):
        for article in article_list:
            # Start by testing that we have all the data we will need.
            if not article.doi:
                self._say.warn('Skipping article with missing DOI: ' + article.title)
                article.status = 'missing-doi'
                continue
            if not article.pdf:
                self._say.warn('Skipping article with missing PDF URL: ' + article.doi)
                article.status = 'missing-pdf'
                continue
            xml = self._metadata_xml(article)
            if not xml:
                self._say.warn('Skipping article with no DataCite entry: ' + article.doi)
                article.status = 'failed-datacite'
                continue

            # Looks good. Carry on.
            article_dir = path.join(dest_dir, tail_of_doi(article))
            try:
                os.makedirs(article_dir)
            except FileExistsError:
                pass
            xml_file = path.join(article_dir, xml_filename(article))
            pdf_file = path.join(article_dir, pdf_filename(article))
            self._say.info('Writing ' + article.doi)
            with open(xml_file, 'w', encoding = 'utf8') as f:
                if __debug__: log('writing XML to {}', xml_file)
                f.write(xmltodict.unparse(xml))
            if __debug__: log('downloading PDF to {}', pdf_file)
            download(article.pdf, pdf_file)
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
    this_module = sys.modules[__package__]
    print('{} version {}'.format(this_module.__name__, this_module.__version__))
    print('Authors: {}'.format(this_module.__author__))
    print('URL: {}'.format(this_module.__url__))
    print('License: {}'.format(this_module.__license__))


def short(url):
    for prefix in ['https://micropublication.org', 'https://www.micropublication.org']:
        if url.startswith(prefix):
            return url[len(prefix):]
    return url


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


def parse_datetime(string):
    '''Parse a human-written time/date string using dateparser's parse()
function with predefined settings.'''
    return dateparser.parse(string, settings = {'RETURN_AS_TIMEZONE_AWARE': True})


# Main entry point.
# .............................................................................

# On windows, we want plac to use slash intead of hyphen for cmd-line options.
if sys.platform.startswith('win'):
    main.prefix_chars = '/'

# The following allows users to invoke this using "python3 -m handprint".
if __name__ == '__main__':
    plac.call(main)


# For Emacs users
# .............................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:
