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
import xmltodict

import microarchiver
from microarchiver import print_version
from .debug import set_debug, log
from .exceptions import *
from .files import readable, writable, file_in_use, rename_existing
from .files import make_dir, create_archive, verify_archive
from .network import net, network_available, download
from .ui import UI, inform, warn, alert, alert_fatal


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
    # Process arguments and handle early exits --------------------------------

    debugging = debug != 'OUT'
    if debugging:
        set_debug(True, debug)
        import faulthandler
        faulthandler.enable()

    if version:
        print_version()
        exit()

    if not network_available():
        alert('No network.')
        exit()

    if get_xml:
        if __debug__: log('Fetching articles from server')
        print(articles_list())
        exit()

    # Do the real work --------------------------------------------------------

    try:
        ui = UI('Microarchiver', use_color = not no_color, be_quiet = quiet)
        body = MainBody(source  = articles if articles != 'A' else None,
                        dest    = '.' if output_dir == 'O' else output_dir,
                        after   = None if after_date == 'D' else after_date,
                        report  = None if report == 'R' else report,
                        do_zip  = not no_zip,
                        preview = preview,
                        ui      = ui)
        body.run()
    except KeyboardInterrupt as ex:
        warn('Quitting')
        exit(1)
    except Exception as ex:
        if debugging:
            import traceback
            alert('{}\n{}', str(ex), traceback.format_exc())
            import pdb; pdb.set_trace()
        else:
            alert_fatal('{}'.format(str(ex)))
            exit(2)


class MainBody(object):
    '''Main body for Microarchiver.'''

    def __init__(self, **kwargs):
        '''Initialize internal state and prepare for running services.'''
        # Assign parameters to self to make them available within this object.
        self.__dict__ = kwargs


    def run(self):
        '''Execute the control logic.'''

        # Check and process argument values & fail early if there's a problem.
        self._process_arguments()

        # Read the article list, then do optional filtering for date.
        if self.source:
            inform('Reading articles list from XML file {}', self.source)
            articles = self._articles_from_xml(self.source)
        else:
            inform('Fetching articles list from {}', _URL_ARTICLES_LIST)
            articles = self._articles_from_xml(_URL_ARTICLES_LIST)

        if self.after:
            date_str = self.after.strftime(_DATE_PRINT_FORMAT)
            inform('Will only keep articles published after {}', date_str)
            articles = [x for x in articles if parse_datetime(x.date) > self.after]

        num_articles = len(articles)
        inform('Total articles: {}', humanize.intcomma(num_articles))
        if self.preview:
            self._print_articles(articles)
        else:
            if num_articles == 0:
                inform('No articles to archive')
            else:
                inform('Output will be written to directory "{}"', self.dest)
                make_dir(self.dest)
                self._save_articles(self.dest, articles)
                if self.do_zip:
                    archive_file = self.dest + '.zip'
                    inform('Creating ZIP archive file "{}"', archive_file)
                    comments = file_comments(num_articles)
                    create_archive(archive_file, '.zip', self.dest, comments)
                    inform('Deleting directory "{}"', self.dest)
                    shutil.rmtree(self.dest)
        if self.report:
            if path.exists(self.report):
                rename_existing(self.report)
            inform('Writing report to ' + self.report)
            self._write_report(self.report, articles)


    def _process_arguments(self):
        if self.source and not readable(self.source):
            raise RuntimeError('File not readable: {}'.format(self.source))
        if self.source and not self.source.endswith('.xml'):
            raise RuntimeError('Does not appear to be an XML file: {}'.format(self.source))

        if not path.isabs(self.dest):
            self.dest = path.realpath(path.join(os.getcwd(), self.dest))
        if path.isdir(self.dest):
            if not writable(self.dest):
                raise RuntimeError('Directory not writable: {}'.format(self.dest))
        else:
            if path.exists(self.dest):
                raise ValueError('Not a directory: {}'.format(self.dest))
        self.dest = path.join(self.dest, _ARCHIVE_DIR_NAME)

        if self.report and file_in_use(self.report):
            raise RuntimeError("File is in use by another process: {}".format(self.report))

        if self.after:
            try:
                self.after = parse_datetime(self.after)
                if __debug__: log('Parsed after_date as {}', self.after)
            except Exception as ex:
                raise RuntimeError('Unable to parse date: {}'.format(str(ex)))


    def _articles_from_xml(self, file_or_url):
        '''Returns a list of `Article` tuples from the given URL or file.'''
        # Read the XML.
        if file_or_url.startswith('http'):
            (response, error) = net('get', file_or_url)
            if not error and response and response.text:
                # The micropublication xml declaration explicit uses ascii encoding.
                xml = response.text.encode('ascii')
            elif error and isinstance(error, NoContent):
                if __debug__: log('request for article list was met with code 404 or 410')
                alert_fatal(str(error))
                return []
            elif error:
                if __debug__: log('error reading from micropublication.org server')
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
        try:
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
        except Exception as ex:
            if __debug__: log('could not parse XML from server')
            alert('Unexpected or badly formed XML returned by server')
        return articles


    def _print_articles(self, articles_list):
        inform('-'*89)
        inform('{:3}  {:<32}  {:10}  {:20}'.format(
            '?', 'DOI', 'Date', 'URL (https://micropublication.org)'))
        inform('-'*89)
        count = 0
        for article in articles_list:
            count += 1
            inform('{:3}  {:<32}  {:10}  {:20}'.format(
                self.ui.error_text('err') if article.status == 'incomplete' else 'OK',
                article.doi if article.doi else self.ui.error_text('missing DOI'),
                article.date if article.date else self.ui.error_text('missing date'),
                short(article.pdf) if article.pdf else self.ui.error_text('missing URL')))
        inform('-'*89)


    def _write_report(self, report_file, articles_list):
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


    def _save_articles(self, dest_dir, article_list):
        for article in article_list:
            # Start by testing that we have all the data we will need.
            if not article.doi:
                warn('Skipping article with missing DOI: ' + article.title)
                article.status = 'missing-doi'
                continue
            if not article.pdf:
                warn('Skipping article with missing PDF URL: ' + article.doi)
                article.status = 'missing-pdf'
                continue
            xml = self._metadata_xml(article)
            if not xml:
                warn('Skipping article with no DataCite entry: ' + article.doi)
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
            inform('Writing ' + article.doi)
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

def articles_list():
    '''Write to standard output the XML article list from the server.'''
    (response, error) = net('get', _URL_ARTICLES_LIST)
    if not error and response and response.text:
        # The micropublication xml declaration explicit uses ascii encoding.
        return response.text
    else:
        return ''


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
    text += 'created on {}. There {} {} article{} in this archive.'.format(
        str(datetime.date.today()), 'is' if num_articles == 1 else 'are',
        num_articles, '' if num_articles == 1 else 's')
    text += '\n'
    text += software_comments()
    text += '\n'
    text += '~ '*35
    text += '\n'
    return text


def software_comments():
    text  = '\n'
    text += 'The software used to create this archive file was microarchiver\n'
    text += 'version {} <{}>'.format(microarchiver.__version__, microarchiver.__url__)
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
