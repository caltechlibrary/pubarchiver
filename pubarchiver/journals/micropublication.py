'''
micropublication.py: interface to microPublication.org

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018-2021 by the California Institute of Technology.  This code
is open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import base64
from   bun import inform, warn, alert, alert_fatal
from   commonpy.network_utils import net
from   lxml import etree
from   os import path
import xmltodict

if __debug__:
    from sidetrack import log

import pubarchiver
from   pubarchiver.article import Article
from   pubarchiver.exceptions import *
from   pubarchiver.journals.base import JournalAdapter


# Constants.
# .............................................................................

_DATACITE_API_URL = 'https://api.datacite.org/dois/'


# Main class.
# .............................................................................

class Micropublication(JournalAdapter):
    name             = "microPublication"
    issn             = '2578-9430'
    doi_prefix       = '10.17912'
    uses_jats        = True
    metadata_source  = 'DataCite'
    base_urls        = ['https://www.micropublication.org']
    article_list_url = 'https://portal.micropublication.org/api/export/archives.xml'
    archive_basename = 'micropublication-org'


    def all_articles(self):
        '''Return a list of all articles.'''
        (response, error) = net('get', self.article_list_url)
        if not error and response and response.text:
            return self._article_tuples(response.text)
        elif error and isinstance(error, NoContent):
            if __debug__: log(f'request for article list was met with code 404 or 410')
            alert_fatal(str(error))
            return []
        elif error:
            if __debug__: log(f'error reading from micropublication.org server')
            raise error
        else:
            raise InternalError('Unexpected response from network call')


    def article_metadata(self, article):
        (response, error) = net('get', _DATACITE_API_URL + article.doi)
        if error:
            if __debug__: log(f'error from datacite for {article.doi}: {str(error)}')
            return None
        elif not response:
            warn(f'Empty response from DataCite for {article.doi}')
            return None

        json = response.json()
        xmldict = xmltodict.parse(base64.b64decode(json['data']['attributes']['xml']))
        date = json['data']['attributes']['registered']
        if 'dates' in xmldict['resource']:
            xmldict['resource']['dates']['date']['#text'] = date
        else:
            xmldict['resource']['dates'] = {'date': article.date}
        xmldict['resource']['volume']  = volume_for_year(xmldict['resource']['publicationYear'])
        xmldict['resource']['file']    = article.basename + '.pdf'
        xmldict['resource']['journal'] = xmldict['resource'].pop('publisher')
        xmldict['resource']['e-issn']  = self.issn
        xmldict['resource']["rightsList"] = [{
            "rights": "Creative Commons Attribution 4.0",
            "rightsURI": "https://creativecommons.org/licenses/by/4.0/legalcode"}]
        xmldict['resource'].pop('@xmlns')
        xmldict['resource'].pop('@xsi:schemaLocation')
        return xmldict


    def articles_from(self, doi_file):
        '''Returns a list of `Article` tuples from a file of DOIs.'''
        if __debug__: log(f'reading {doi_file}')
        with open(doi_file, 'r') as f:
            # An earlier version (Microarchiver) allowed the use of a file
            # containing an article list in the XML format returned by
            # micropublication.org. This proved to be unnecessary, but I'm
            # leaving it as an undocumented feature for testing purposes.
            if f.readline().startswith('<?xml'):
                return self._articles_from_xml(doi_file)
            else:
                return self._articles_from_dois(doi_file)


    def _article_tuples(self, xml):
        '''Parse the XML input, assumed to be from micropublication.org, and
        create a list of `Article` records.
        '''
        if __debug__: log(f'parsing XML data')
        articles = []
        if type(xml) == str:
            # The micropublication xml declaration explicit uses ascii encoding.
            xml = xml.encode('utf-8')
        try:
            for element in etree.fromstring(xml).findall('article'):
                doi = ''
                try:
                    doi   = field_text(element, 'doi')
                    pdf   = field_text(element, 'pdf-url')
                    jats  = field_text(element, 'jats-url')
                    image = field_text(element, 'image-url')
                    title = field_text(element, 'article-title')
                    date  = element.find('date-published')
                    if date is not None:
                        year  = (date.find('year').text or '').strip()
                        month = (date.find('month').text or '').strip()
                        day   = (date.find('day').text or '').strip()
                        date  = year + '-' + month.rjust(2, '0') + '-' + day.rjust(2, '0')
                    else:
                        date = ''
                    basename = tail_of_doi(doi)
                    status = 'complete' if all([pdf, jats, doi, title, date]) else 'incomplete'
                    articles.append(Article(self.issn, doi, date, title,
                                            basename, pdf, jats, image, status))
                    if __debug__: log(f'parsed {doi}')
                except Exception as ex:
                    if doi:
                        alert(f'Error parsing XML data for {doi} -- skipping')
                        if __debug__: log(f'Parse error for {doi}: {str(ex)}')
                    else:
                        alert('Skipping unparseable XML element')
                        if __debug__: log(str(ex))
                    continue
        except Exception as ex:
            if __debug__: log(f'could not parse XML from server')
            alert('Unexpected or badly formed XML returned by server')
        return sorted(articles, key = lambda item: item.date)


    def _articles_from_xml(self, xml_file):
        '''Returns a list of `Article` tuples from the XML source, which can be
        either a file or a network server responding to HTTP 'get'.'''
        with open(xml_file, 'rb') as file:
            xml = file.readlines()
        return self._article_tuples(xml)


    def _articles_from_dois(self, doi_file):
        '''Read the given file (assumed to contain a list of DOIs) and return
        a list of corresponding `Article` records.  A side-effect of doing this
        is that this function has to contact the server to get a list of all
        articles in XML format.'''
        dois = []
        with open(doi_file, 'r') as f:
            dois = [line.strip() for line in f]
        if not dois:
            if __debug__: log(f'could not read any lines from {doi_file}')
            return []
        else:
            return [a for a in self.all_articles() if a.doi in dois]


# Miscellaneous utilities.
# .............................................................................

def volume_for_year(year):
    return int(year) - 2014


def tail_of_doi(doi):
    slash = doi.rfind('/')
    return doi[slash + 1:]


def field_text(element, field):
    field_el = element.find(field)
    if field_el is None:
        return ''
    as_text = etree.tostring(field_el, encoding = 'unicode', method = 'text')
    return ' '.join(as_text.split())
