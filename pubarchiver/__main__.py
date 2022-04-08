'''
__main__: main command-line interface to PubArchiver

Authors
-------

Tom Morrell <tmorrell@caltech.edu> -- Caltech Library
Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2019-2022 by the California Institute of Technology.  This code
is open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

from   bun import UI, inform, warn, alert, alert_fatal
import csv
from   commonpy.data_utils import pluralized, timestamp, parsed_datetime
from   commonpy.exceptions import NoContent
from   commonpy.file_utils import filename_basename, filename_extension
from   commonpy.file_utils import readable, writable, nonempty, file_in_use
from   commonpy.file_utils import rename_existing, delete_existing
from   commonpy.module_utils import module_path
from   commonpy.network_utils import net, network_available, download_file
import dateparser
from   datetime import date
from   datetime import datetime as dt
import humanize
import json as jsonlib
from   lxml import etree
import os
import os.path as path
from   PIL import Image, ImageFile
import plac
import shutil
from   sidetrack import set_debug, log, logf
import sys
import xmltodict
import zipfile
from   zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED

# Set this to prevent some image files from causing errors such as
# "OSError: image file is truncated (10 bytes not processed)"
ImageFile.LOAD_TRUNCATED_IMAGES = True

# This is to prevent Pillow from warning "DecompressionBombWarning: Image size
# (100153418 pixels) exceeds limit of 89478485 pixels ..."
Image.MAX_IMAGE_PIXELS = None

import pubarchiver
from pubarchiver import print_version
from .exceptions import *
from .journals import journal_list, journal_handler


# Constants.
# .............................................................................

_TIFF_DPI = (500, 500)
'''Resolution for the TIFF images saved with JATS content.'''

_DATE_FORMAT = '%b %d %Y %H:%M:%S %Z'
'''Format in which lastmod date is printed back to the user. The value is used
with datetime.strftime().'''

_INTERNAL_DTD_DIR = 'JATS-Archiving-1-2-MathML3-DTD'
'''Directory relative to <module>/data containing JATS DTD files.'''

_JATS_DTD_FILENAME = 'JATS-archivearticle1-mathml3.dtd'
'''Name of the root DTD file for JATS.'''

_HTML_REPORT_TOP = '''<html>
    <style>
      html  {{ font-family: "Helvetica", sans-serif     }}
      h1    {{ font-size: 14pt; text-align: center      }}
      table {{ width: 100%                              }}
      thead {{ background-color: #eee                   }}
      th    {{ text-align: left; padding: 6px 6px 0 6px }}
      td    {{ padding: 6px 10px                        }}
    </style>
  <body>
    <h1>{}</h1>
    <table>
      <thead>
        <tr>
          <th width="10%">Status</th>
          <th width="30%">DOI</th>
          <th width="10%">Date</th>
          <th>URL</th>
        </tr>
      </thead>
      <tbody>
'''

_HTML_REPORT_BOTTOM = '''
      </tbody>
    </table>
  </body>
</html>
'''


# Main program.
# .............................................................................

@plac.annotations(
    after_date = ('only keep articles published after date "A"',              'option', 'a'),
    no_color   = ('do not colorize output printed to the terminal',           'flag',   'C'),
    dest       = ('assume destination "portico" or "pmc" (default: portico)', 'option', 'd'),
    doi_file   = ('retrieve the articles whose DOIs are found in file "F"',   'option', 'f'),
    journal    = ('work with journal "J" (required)',                         'option', 'j'),
    list_dois  = ("list all known DOIs from the journal & exit",              'flag',   'l'),
    output_dir = ('write archive in directory O (default: current dir)',      'option', 'o'),
    preview    = ('preview the list of articles that would be archived',      'flag',   'p'),
    quiet      = ('only print important messages while working',              'flag',   'q'),
    rep_file   = ('write report to file R (default: print to terminal)',      'option', 'r'),
    rep_fmt    = ('with -r, write report as "csv" or "html" (default: csv)',  'option', 's'),
    rep_title  = ('with -r, use title "T" for the report',                    'option', 't'),
    version    = ('print version information and exit',                       'flag',   'V'),
    no_check   = ('do not validate JATS XML files against the DTD',           'flag'  , 'X'),
    no_zip     = ('do not zip up the output (default: do)',                   'flag',   'Z'),
    debug      = ('write detailed log to "OUT" (use "-" for console)',        'option', '@'),
)

def main(after_date = 'A', no_color = False, dest = 'D', doi_file = 'F',
         journal = 'J', list_dois = False, output_dir = 'O', preview = False,
         quiet = False, rep_file = 'R', rep_fmt = 'S', rep_title = 'T',
         version = False, no_check = False, no_zip = False, debug = 'OUT'):
    '''Create archives of journals suitable for sending to Portico or PMC.

The journal whose articles are to be archived must be indicated using the
required option -j (or /j on Windows).  To list the currently-supported
journals, you can use a value of "list" to the -j option:

  pubarchiver -j list

Without any additional options, PubArchiver will contact the journal website
and either DataCite or Crossref, and create an archive containing articles and
their metadata for all articles published to date by the journal.  The options
below can be used to select articles and influence other PubArchiver behaviors.

Selecting a subset of articles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the option -a (or /a on Windows) is given, PubArchiver will download only
articles whose publication dates are AFTER the given date.  Valid date
descriptors are those accepted by the Python dateparser library.  Make sure to
enclose descriptions within single or double quotes.  Examples:

  pubarchiver -a "2014-08-29"   ....
  pubarchiver -a "12 Dec 2014"  ....
  pubarchiver -a "July 4, 2013"  ....
  pubarchiver -a "2 weeks ago"  ....

The option -f (or /f on Windows) can be used with a value of a file path to
limit archiving to only the DOIs listed in the given file.  The file format
must be a simple list of one DOI per line.

The selection by date performed by the -a option happens after reading the
list of articles using the -f option if present, and can be used to filter
by date the articles whose DOIs are provided.

Controlling the output
~~~~~~~~~~~~~~~~~~~~~~

The value supplied after the option -d (or /d on Windows) can be used to
select the destination where the publication archive is intended to be sent
after PubArchiver has done its work.  The possible alternatives are "portico"
and "pmc"; Portico is assumed to be the default destination.  This option
changes the structure and content of the archive created by PubArchiver.

PubArchiver will write its output to the directory indicated by the value of
the option -o (or /o on Windows). If no -o is given, the output will be written
to the current directory from which PubArchiver is being run.  Each article will
be written to a subdirectory named after the DOI of the article.  The output for
each article will consist of an XML metadata file describing the article, the
article itself in PDF format, and a subdirectory named "jats" containing the
article in JATS XML format along with any image that may appear in the article.
The image is always converted to uncompressed TIFF format (because it is
considered a good preservation format).

Unless the option -Z (or /Z on Windows) is given, the output will be archived
in ZIP format.  If the output structure (as determine by the -s option) is
being generated for PMC, each article will be put into its own individual
ZIP archive; else, the default action is to put the collected output of all
articles into a single ZIP archive file.

Writing a report
~~~~~~~~~~~~~~~~

As it works, PubArchiver writes information to the terminal about the articles
it puts into the archive, including whether any problems are encountered.  To
save this information to a file, use the option -r (or /r on Windows), which
will make PubArchiver write a report file.  By default, the format of the
report file is CSV; the option -s (/s on Windows) can be used to select "csv"
or "html" (or both) as the format.  The title of the report will be based on
the current date, unless the option -t (or /t on Windows) is used to supply a
different title.

Previewing the list of articles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If given the option -p (or /p on Windows), pubarchiver will ONLY display a
list of articles it will archive and stop short of creating the archive.  This
is useful to see what would be produced without actually doing it.  However,
note that because it does not attempt to download the articles and associated
files, it will not be able to report on errors that might occur when not
operating in preview mode.  Consequently, do not use the output of -p as a
prediction of eventual success or failure.

Return values
~~~~~~~~~~~~~

This program will exit with a return code of 0 if no problems are encountered
during execution.  If a problem is encountered, it will return a nonzero value.
If no network is detected, it returns a value of 1; if the program is
interrupted (e.g., using control-c) it returns a value of 2; if it encounters
a fatal error, it returns a value of 3. If it encounters any non-fatal
problems (such as a missing PDF file or JATS validation error), it returns a
nonzero value equal to 100 + the number of articles that had failures.
Summarizing the possible return codes:

        0 = no errors were encountered -- success
        1 = no network detected -- cannot proceed
        2 = the user interrupted program execution
        3 = an exception or fatal error occurred
  100 + n = encountered non-fatal problems on a total of n articles

Additional command-line options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The option -l (or /l on Windows) can be used to obtain a list of all DOIs
for all articles published by the selected journal.

Pubarchiver will print general informational messages as it works. To
reduce messages to only warnings and errors, use the option -q (or /q on
Windows).  Output is color-coded by default unless the -C option (or /C on
Windows) is given; this option can be helpful if the color control signals
create problems for your terminal emulator.

If given the -@ option (/@ on Windows), this program will print a detailed
real-time log of what it is doing.  The output will be sent to the given
destination, which can be '-' to indicate console output, or a file path to
send the output to a file.  The output is mainly intended for debugging.

Pubarchiver always downloads the JATS XML version of articles from
micropublication.org (in addition to downloading the PDF version), and by
default, pubarchiver validates the XML content against the JATS DTD.  To
skip the XML validation step, use the option -X (/X on Windows).

If given the -V option (/V on Windows), this program will print version
information and exit without doing anything else.

Command-line options summary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
'''
    if debug != 'OUT':
        if __debug__: set_debug(True, debug)
        import faulthandler
        faulthandler.enable()

    if version:
        print_version()
        exit(0)

    try:
        if __debug__: log('='*8 + f' started {timestamp()}' + '='*8)
        ui = UI('PubArchiver', use_color = not no_color, be_quiet = quiet)
        ui.start()

        if journal == 'J':
            alert('Must specify a journal using the -j option.')
            print_supported_journals()
            exit(1)
        elif journal in ['list', 'help']:
            print_supported_journals()
            exit(0)
        elif journal not in journal_list():
            alert(f'Unrecognized journal "{journal}".')
            print_supported_journals()
            exit(1)

        if not network_available():
            alert('No network.')
            exit(1)

        handler = journal_handler(journal)
        if list_dois:
            inform(f'Asking {handler.name} server for a list of all DOIs ...')
            articles = handler.all_articles()
            if articles:
                inform(f'Got {len(articles)} DOIs from {handler.name}:')
                print('\n'.join(article.doi for article in articles))
            else:
                warn(f'Failed to get list of articles from {handler.name}')
            exit(0)

        body = MainBody(journal       = handler,
                        dest          = 'pmc' if dest.lower() == 'pmc' else 'portico',
                        doi_file      = doi_file if doi_file != 'F' else None,
                        output_dir    = '.'   if output_dir == 'O' else output_dir,
                        after         = None  if after_date == 'A' else after_date,
                        report_file   = None  if rep_file == 'R' else rep_file,
                        report_format = 'csv' if rep_fmt == 'S' else rep_fmt,
                        report_title  = None  if rep_title == 'T' else rep_title,
                        do_validate   = handler.uses_jats and not no_check,
                        do_zip        = not no_zip,
                        preview       = preview)
        body.run()
        if __debug__: logf(f'finished with {body.failures} failures')
        if __debug__: log('_'*8 + f' stopped {timestamp()} ' + '_'*8)
        exit(100 + body.failures if body.failures > 0 else 0)
    except KeyboardInterrupt as ex:
        warn('Quitting')
        if __debug__: log(f'returning with exit code 2')
        exit(2)
    except Exception as ex:
        import traceback
        if __debug__: log(f'{str(ex)}\n{traceback.format_exc()}')
        alert_fatal(f'{str(ex)}')
        if __debug__: log(f'returning with exit code 3')
        exit(3)


class MainBody(object):
    '''Main body for PubArchiver.'''

    def __init__(self, **kwargs):
        '''Initialize internal state and prepare for running services.'''
        # Assign parameters to self to make them available within this object.
        self.__dict__ = kwargs
        # Assign default return status.
        self.failures = 0


    def run(self):
        '''Execute the control logic.'''

        # Check and process argument values & fail early if there's a problem.
        self._process_arguments()

        # Read the article list from a file or the server.
        inform(f'Reading article list from {self.doi_file or "server"} ...')
        if self.doi_file:
            articles = self.journal.articles_from(self.doi_file)
        else:
            articles = self.journal.all_articles()

        # Do optional filtering based on the date.
        if self.after:
            date_str = self.after.strftime(_DATE_FORMAT)
            inform(f'Will only keep articles published after {date_str}.')
            articles = [x for x in articles if parsed_datetime(x.date) > self.after]

        inform(f'Total articles left after filtering: {humanize.intcomma(len(articles))}.')
        inform(f'Destination format: {"PMC" if self.dest == "pmc" else "Portico"}')
        if self.preview:
            self._print_articles(articles)
            return
        elif len(articles) > 0:
            inform(f'Output will be written to directory "{self.output_dir}"')
            os.makedirs(self.output_dir, exist_ok = True)
            self._save_articles(self.output_dir, articles, self.dest, self.do_zip)

        if self.report_file:
            inform(f'Writing report to {self.report_file}')
            self._write_report(self.report_file, self.report_format,
                               self.report_title, articles)

        # Count any failures by looking at the article statuses.
        inform('Done.')
        self.failures = sum(article.status.startswith('fail') for article in articles)


    def _process_arguments(self):
        if self.doi_file:
            if not readable(self.doi_file):
                raise RuntimeError(f'File not readable: {self.doi_file}')
            if not nonempty(self.doi_file):
                warn(f'File is empty: {self.doi_file}')

        if not path.isabs(self.output_dir):
            self.output_dir = path.realpath(path.join(os.getcwd(), self.output_dir))
        if path.isdir(self.output_dir):
            if not writable(self.output_dir):
                raise RuntimeError(f'Directory not writable: {self.output_dir}')
        else:
            if path.exists(self.output_dir):
                raise ValueError(f'Not a directory: {self.output_dir}')
        self.output_dir = path.join(self.output_dir, self.journal.archive_basename)

        if self.after:
            parsed_date = None
            try:
                parsed_date = parsed_datetime(self.after)
            except Exception as ex:
                raise RuntimeError(f'Unable to parse date: {str(ex)}')
            if parsed_date:
                if __debug__: log(f'parsed after_date as {parsed_date}')
                self.after = parsed_date
            else:
                # parsed_datetime(...) returned None, which means it failed.
                raise RuntimeError(f'Invalid date: {self.after}')

        if self.do_validate:
            data_dir = path.join(module_path('pubarchiver'), 'data')
            dtd_dir = path.join(data_dir, _INTERNAL_DTD_DIR)
            dtd_file = path.join(dtd_dir, _JATS_DTD_FILENAME)
            if not path.exists(data_dir) or not path.isdir(data_dir):
                raise RuntimeError(f'Data directory is missing: {data_dir}')
            elif not path.exists(dtd_dir) or not path.isdir(dtd_dir):
                warn('Cannot find internal DTD directory -- validation turned off')
                self.do_validate = False
            elif not path.exists(dtd_file) or not readable(dtd_file):
                warn('Cannot find internal copy of JATS DTD -- validation turned off')
                self.do_validate = False
            else:
                current_dir = os.getcwd()
                try:
                    os.chdir(dtd_dir)
                    if __debug__: log(f'using JATS DTD at {dtd_file}')
                    self._dtd = etree.DTD(dtd_file)
                finally:
                    os.chdir(current_dir)


    def _print_articles(self, article_list):
        inform('-'*89)
        inform('{:3}  {:<32}  {:10}  {:20}'.format(
            '?', 'DOI', 'Date', f'URL ({self.journal.base_urls[0]})'))
        inform('-'*89)
        count = 0
        for article in article_list:
            count += 1
            status = 'OK' if article.status != 'incomplete' else '[alert]err[/]'
            doi    = article.doi if article.doi else '[alert]missing DOI[/]'
            date   = article.date if article.date else '[alert]missing date[/]'
            url    = article.pdf if article.pdf else '[alert]missing URL[/]'
            for base in self.journal.base_urls:
                url = url.replace(base, '')
            inform('{:3}  {:<32}  {:10}  {:20}'.format(status, doi, date, url))
        inform('-'*89)


    def _write_report(self, report_file, report_format, title, article_list):
        for fmt in report_format.split(','):
            dest_file = filename_basename(report_file) + '.' + fmt
            if fmt == "csv":
                with open(dest_file, 'w', newline='') as file:
                    file.write('Status,DOI,Date,URL\n')
                    csvwriter = csv.writer(file, delimiter=',')
                    for article in article_list:
                        row = [article.status, article.doi, article.date, article.pdf]
                        csvwriter.writerow(row)
            elif fmt == "html":
                with open(dest_file, 'w', newline='') as file:
                    file.write(_HTML_REPORT_TOP.format(title or 'Report for ' + timestamp()))
                    for article in article_list:
                        file.write('<tr>')
                        file.write('<td>' + article.status + '</td>')
                        file.write('<td>' + article.doi + '</td>')
                        file.write('<td>' + article.date + '</td>')
                        file.write('<td><a href="{0}">{0}</a></td>'.format(article.pdf))
                        file.write('</tr>')
                    file.write(_HTML_REPORT_BOTTOM)
            else:
                raise ValueError('Unsupported report format "' + fmt + '"')


    def _save_articles(self, dest_dir, article_list, dest_service, zip_articles):
        # This overwrites the article.status field of each article with an
        # error description if there is an error.
        saved_files = []
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
            if self.journal.uses_jats and not article.jats:
                # We need JATS for PMC.
                warn('Skipping article with missing JATS URL: ' + article.doi)
                article.status = 'missing-jats'
                continue
            xmldict = self.journal.article_metadata(article)
            if not xmldict:
                warn('Skipping article with missing metadata: ' + article.doi)
                article.status = 'missing-' + self.journal.metadata_source.lower()
                continue

            # Looks good. Carry on.
            if dest_service == 'pmc':
                self._save_article_pmc(dest_dir, article, xmldict, zip_articles)
            else:
                self._save_article_portico(dest_dir, article, xmldict)
            saved_files.append(article)

        # After we've downloaded everything, maybe zip it all up together.
        if zip_articles and dest_service != 'pmc':
            final_file = self.output_dir + '.zip'
            inform(f'Creating ZIP archive file "{final_file}"')
            comments = zip_comments(len(article_list), self.journal.name)
            archive_directory(final_file, self.output_dir, comments)
            if __debug__: log(f'verifying ZIP file {final_file}')
            verify_archive(final_file, 'zip')
            if __debug__: log(f'deleting directory {self.output_dir}')
            shutil.rmtree(self.output_dir)


    def _save_article_portico(self, dest_dir, article, xmldict):
        article_dir = path.join(dest_dir, article.basename)
        jats_dir    = path.join(article_dir, 'jats')
        try:
            os.makedirs(article_dir)
            if self.journal.uses_jats:
                os.makedirs(jats_dir)
        except FileExistsError:
            pass
        inform('Writing ' + article.doi)
        xml_file = xml_filename(article, article_dir)
        with open(xml_file, 'w', encoding = 'utf8') as f:
            if __debug__: log(f'writing XML to {xml_file}')
            f.write(xmltodict.unparse(xmldict, pretty = True))

        pdf_file = pdf_filename(article, article_dir)
        if __debug__: log(f'downloading PDF to {pdf_file}')
        if not download_file(article.pdf, pdf_file):
            warn(f'Could not download PDF file for {article.doi}')
            article.status = 'failed-pdf-download'

        if not self.journal.uses_jats:
            # Nothing more to do.
            return

        jats_file = jats_filename(article, jats_dir)
        if __debug__: log(f'downloading JATS XML to {jats_file}')
        if not download_file(article.jats, jats_file):
            warn(f'Could not download JATS file for {article.doi}')
            article.status = 'failed-jats-download'
        if self.do_validate:
            if not valid_xml(jats_file, self._dtd):
                warn(f'Failed to validate JATS for article {article.doi}')
                article.status = 'failed-jats-validation'
        else:
            if __debug__: log(f'skipping DTD validation of {jats_file}')

        # We need to store the image with the name that appears in the
        # JATS file. That requires a little extra work to extract.
        image_extension = filename_extension(article.image)
        image_file = image_filename(article, jats_dir, ext = image_extension)
        if article.image:
            if __debug__: log(f'downloading image file to {image_file}')
            if download_file(article.image, image_file):
                try:
                    with Image.open(image_file) as img:
                        converted = image_without_alpha(img)
                        converted = converted.convert('RGB')
                        if __debug__: log(f'converting image to TIFF format')
                        tiff_name = filename_basename(image_file) + '.tif'
                        comments = tiff_comments(article, self.journal.name)
                        # Using save() means only the 1st frame of a multiframe
                        # image will be saved.
                        converted.save(tiff_name, compression = None,
                                       dpi = _TIFF_DPI, description = comments)
                    # We keep only the uncompressed TIFF version.
                    if __debug__: log(f'deleting original image file {image_file}')
                    delete_existing(image_file)
                except Exception as ex:
                    if __debug__: log(str(ex))
                    warn(f'Encountered error trying to open image '
                         + f'{article.image} saved in file {image_file}')
                    article.status = 'failed-image-download'
            else:
                warn(f'Failed to download image for {article.doi}')
                article.status = 'failed-image-download'
        else:
            if __debug__: log(f'{article.doi} has no image (going on without it')


    def _save_article_pmc(self, dest_dir, article, xml, zip_articles):
        inform('Writing ' + article.doi)
        to_archive = []

        pdf_file = pmc_pdf_filename(article, dest_dir)
        if __debug__: log(f'downloading PDF to {pdf_file}')
        if not download_file(article.pdf, pdf_file):
            warn(f'Could not download PDF file for {article.doi}')
            article.status = 'failed-pdf-download'
        to_archive.append(pdf_file)

        jats_file = jats_filename(article, dest_dir)
        if __debug__: log(f'downloading JATS XML to {jats_file}')
        if not download_file(article.jats, jats_file):
            warn(f'Could not download JATS file for {article.doi}')
            article.status = 'failed-jats-download'
        if self.do_validate:
            if not valid_xml(jats_file, self._dtd):
                warn(f'Failed to validate JATS for article {article.doi}')
                article.status = 'failed-jats-validation'
        else:
            if __debug__: log(f'skipping DTD validation of {jats_file}')
        to_archive.append(jats_file)

        # We need to store the image with the name that appears in the
        # JATS file. That requires a little extra work to extract.
        image_extension = filename_extension(article.image)
        image_file = image_filename(article, dest_dir, ext = image_extension)
        if article.image:
            if __debug__: log(f'downloading image file to {image_file}')
            if download_file(article.image, image_file):
                with Image.open(image_file) as img:
                    converted_img = image_without_alpha(img)
                    converted_img = converted_img.convert('RGB')
                    if __debug__: log(f'converting image to TIFF format')
                    tiff_file = filename_basename(image_file) + '.tif'
                    # Using save() means that only the 1st frame of a
                    # multiframe image will be saved.
                    desc = tiff_comments(article, self.journal.name)
                    converted_img.save(tiff_file, dpi = _TIFF_DPI,
                                       compression = None, description = desc)
                    to_archive.append(tiff_file)
                # We keep only the uncompressed TIFF version.
                if __debug__: log(f'deleting original image file {image_file}')
                delete_existing(image_file)
            else:
                warn(f'Failed to download image for {article.doi}')
                article.status = 'failed-image-download'
        else:
            if __debug__: log(f'{article.doi} has no image (going on without it')

        # Finally, put the files into their own zip archive.
        if zip_articles:
            if not article.status.startswith('failed'):
                zip_file = pmc_zip_filename(article, dest_dir)
                inform(f'Creating ZIP archive file "{zip_file}"')
                archive_files(zip_file, to_archive)
                if __debug__: log(f'verifying ZIP file {zip_file}')
                verify_archive(zip_file, 'zip')
                for file in to_archive:
                    if __debug__: log(f'deleting file {file}')
                    delete_existing(file)
            else:
                warn(f'ZIP archive for {article.doi} not created due to errors')


# Miscellaneous utilities.
# .............................................................................

def print_supported_journals():
    inform('Recognized journals: [white]' + ', '.join(journal_list()) + '[/]')


def pdf_filename(article, article_dir = ''):
    filename = article.basename + '.pdf'
    return path.join(article_dir, filename)


def xml_filename(article, article_dir = ''):
    filename = article.basename + '.xml'
    return path.join(article_dir, filename)


def pmc_basename(article):
    issn_no_dash = article.issn.replace('-', '')
    volume = str(parsed_datetime(article.date).year)
    return issn_no_dash + '-' + volume + '-' + article.basename


def jats_filename(article, jats_dir = ''):
    filename = pmc_basename(article) + '.xml'
    return path.join(jats_dir, filename)


def pmc_pdf_filename(article, article_dir = ''):
    filename = pmc_basename(article) + '.pdf'
    return path.join(article_dir, filename)


def pmc_zip_filename(article, article_dir = ''):
    filename = pmc_basename(article) + '.zip'
    return path.join(article_dir, filename)


def image_filename(article, jats_dir = '', ext = '.png'):
    '''Extract the image file from the <graphic> element of the JATS file.'''
    jats_file = jats_filename(article, jats_dir)
    with open(jats_file, 'r') as f:
        try:
            root = etree.parse(jats_file)
        except Exception as ex:
            raise CorruptedContent(f'Bad XML in JATS file {jats_file}')
        # <graphic> is inside <body>, but to avoid hardcoding the xml element
        # path, this uses an XPath expression to find it anywhere.
        graphic = root.find('.//graphic')
        if graphic is None:
            return None
        # The element looks like this:
        #  <graphic xlink:href="25789430-2019-micropub.biology.000102"/>
        name = graphic.get('{http://www.w3.org/1999/xlink}href')
        if name is None:
            return None
        return path.join(jats_dir, name + ext)


def image_without_alpha(img):
    # Algorithm from 2015-11-03 posting by user "shuuji3" to
    # https://stackoverflow.com/a/33507138/743730
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        if __debug__: log(f'removing alpha channel in image')
        alpha = img.convert('RGBA')
        background = Image.new('RGBA', img.size, (255, 255, 255, 255))
        return Image.alpha_composite(background, alpha)
    else:
        return img


def tiff_comments(article, name):
    text = f'Image converted from {article.image} on {str(date.today())}'
    text += f' for article titled "{article.title}", DOI {article.doi},'
    text += f' originally published on {article.date} in {name}.'
    return text


def zip_comments(num_articles, name):
    text  = '~ '*35
    text += '\n'
    text += 'About this ZIP archive file:\n'
    text += '\n'
    text += f'This archive contains a directory of articles from {name}\n'
    text += 'created on {}. There {} {} article{} in this archive.'.format(
        str(date.today()), 'is' if num_articles == 1 else 'are',
        num_articles, '' if num_articles == 1 else 's')
    text += '\n'
    text += 'The software used to create this archive file was PubArchiver\n'
    text += f'version {pubarchiver.__version__} <{pubarchiver.__url__}>'
    text += '\n'
    text += '~ '*35
    text += '\n'
    return text


def archive_directory(archive_file, source_dir, comment = None):
    root_dir = path.dirname(path.normpath(source_dir))
    base_dir = path.basename(source_dir)
    current_dir = os.getcwd()
    try:
        os.chdir(root_dir)
        with zipfile.ZipFile(archive_file, 'w', ZIP_STORED) as zf:
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    zf.write(os.path.join(root, file))
            if comment:
                zf.comment = comment.encode()
    finally:
        os.chdir(current_dir)


def archive_files(archive_file, files, comment = None):
    base_dir = path.dirname(path.normpath(files[0]))
    current_dir = os.getcwd()
    try:
        os.chdir(base_dir)
        with zipfile.ZipFile(archive_file, 'w', ZIP_STORED) as zf:
            for f in files:
                zf.write(path.basename(f))
            if comment:
                zf.comment = comment.encode()
    finally:
        os.chdir(current_dir)


def verify_archive(archive_file, type):
    '''Check the integrity of an archive and raise an exception if needed.'''
    if type.endswith('zip'):
        error = ZipFile(archive_file).testzip()
        if error:
            raise CorruptedContent(f'Failed to verify file "{archive_file}"')
    else:
        # Algorithm originally from https://stackoverflow.com/a/32312857/743730
        tfile = None
        try:
            tfile = tarfile.open(archive_file)
            for member in tfile.getmembers():
                content = tfile.extractfile(member.name)
                if content:
                    for chunk in iter(lambda: content.read(1024), b''):
                        pass
        except Exception as ex:
            raise CorruptedContent(f'Failed to verify file "{archive_file}"')
        finally:
            if tfile:
                tfile.close()


def valid_xml(xml_file, dtd):
    if __debug__: log(f'parsing XML file {xml_file}')
    try:
        root = etree.parse(xml_file)
    except etree.XMLSyntaxError as ex:
        alert(f'File contains XML syntax errors: {xml_file}')
        # The string form of XMLSyntaxError includes line/col & file name.
        alert(str(ex))
        return False
    except Exception as ex:
        alert(f'Failed to parse XML file: {xml_file}')
        alert(str(ex))
        return False
    if __debug__: log(f'validating {xml_file}')
    if dtd:
        if dtd.validate(root):
            if __debug__: log(f'validated without errors')
            return True
        else:
            warn(f'Failed to validate file {xml_file}')
            warn(f'{pluralized("validation error", dtd.error_log, True)} encountered:')
            for item in dtd.error_log:
                warn('Line {}, col {} ({}): {}', item.line, item.column,
                     item.type_name, item.message)
            return False
    else:
        return True


# Main entry point.
# .............................................................................

# On windows, we want plac to use slash intead of hyphen for cmd-line options.
if sys.platform.startswith('win'):
    main.prefix_chars = '/'

# The following entry point definition is for the console_scripts keyword
# option to setuptools.  The entry point for console_scripts has to be a
# function that takes zero arguments.
def console_scripts_main():
    plac.call(main)

# The following allows users to invoke this using "python3 -m pubarchiver".
if __name__ == '__main__':
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] == 'help'):
        plac.call(main, ['-h'])
    else:
        plac.call(main)


# For Emacs users
# .............................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:
