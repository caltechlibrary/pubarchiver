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

class MicropublicationJournal(JournalAdapter):
    pub_name         = "microPublication.org"
    pub_issn         = '2578-9430'
    base_url         = 'https://www.micropublication.org'
    article_list_url = 'https://www.micropublication.org/archive-list/'
    archive_basename = 'micropublication-org'


    def article_index(self, source = article_list_url):
        (response, error) = net('get', source)
        if not error and response and response.text:
            # The micropublication xml declaration explicit uses ascii encoding.
            return response.text
        elif error and isinstance(error, NoContent):
            if __debug__: log(f'request for article list was met with code 404 or 410')
            alert_fatal(str(error))
            return ''
        elif error:
            if __debug__: log(f'error reading from micropublication.org server')
            raise error
        else:
            raise InternalError('Unexpected response from server')


    def article_metadata(self, article):
        (response, error) = net('get', _DATACITE_API_URL + article.doi)
        if error:
            if __debug__: log(f'error from datacite for {article.doi}: {str(error)}')
            return None
        elif not response:
            if __debug__: log(f'empty response from datacite for {article.doi}')
            return None

        json = response.json()
        xml = xmltodict.parse(base64.b64decode(json['data']['attributes']['xml']))
        date = json['data']['attributes']['registered']
        if 'dates' in xml['resource']:
            xml['resource']['dates']['date']['#text'] = date
        else:
            xml['resource']['dates'] = {'date': article.date}
        xml['resource']['volume']  = volume_for_year(xml['resource']['publicationYear'])
        xml['resource']['file']    = article.basename + '.pdf'
        xml['resource']['journal'] = xml['resource'].pop('publisher')
        xml['resource']['e-issn']  = self.pub_issn
        xml['resource']["rightsList"] = [{
            "rights": "Creative Commons Attribution 4.0",
            "rightsURI": "https://creativecommons.org/licenses/by/4.0/legalcode"}]
        xml['resource'].pop('@xmlns')
        xml['resource'].pop('@xsi:schemaLocation')
        return xml


    def articles_from(self, file_or_url):
        '''Returns a list of `Article` tuples from the given URL or file.'''
        if file_or_url.startswith('http'):
            return self._articles_from_xml(file_or_url)
        else:
            with open(file_or_url, 'r') as f:
                if f.readline().startswith('<?xml'):
                    return self._articles_from_xml(file_or_url)
                else:
                    return self._articles_from_dois(file_or_url)


    def _articles_from_xml(self, file_or_url):
        '''Returns a list of `Article` tuples from the XML source, which can be
        either a file or a network server responding to HTTP 'get'.'''
        # Read the XML.
        if file_or_url.startswith('http'):
            xml = self.article_index()
        else: # Assume it's a file.
            if __debug__: log(f'reading {file_or_url}')
            with open(file_or_url, 'rb') as xml_file:
                xml = xml_file.readlines()
        return self._article_tuples(xml)


    def _articles_from_dois(self, input_file):
        '''Read the given file (assumed to contain a list of DOIs) and return
        a list of corresponding `Article` records.  A side-effect of doing this
        is that this function has to contact the server to get a list of all
        articles in XML format.'''
        articles = self._articles_from_xml(self.article_list_url)
        dois = []
        with open(input_file, 'r') as f:
            dois = [line.strip() for line in f]
        if not any(dois or articles):
            return []
        return [a for a in articles if a.doi in dois]


    def _article_tuples(self, xml):
        '''Parse the XML input, assumed to be from micropublication.org, and
        create a list of `Article` records.
        '''
        if __debug__: log(f'parsing XML data')
        articles = []
        if type(xml) == str:
            # The micropublication xml declaration explicit uses ascii encoding.
            xml = xml.encode('ascii')
        try:
            for element in etree.fromstring(xml).findall('article'):
                doi      = (element.find('doi').text or '').strip()
                pdf      = (element.find('pdf-url').text or '').strip()
                jats     = (element.find('jats-url').text or '').strip()
                image    = (element.find('image-url').text or '').strip()
                title    = (element.find('article-title').text or '').strip()
                date     = element.find('date-published')
                if date != None:
                    year  = (date.find('year').text or '').strip()
                    month = (date.find('month').text or '').strip()
                    day   = (date.find('day').text or '').strip()
                    date  = year + '-' + month + '-' + day
                else:
                    date = ''
                basename = tail_of_doi(doi)
                status = 'complete' if all([pdf, jats, doi, title, date]) else 'incomplete'
                articles.append(Article(self.pub_issn, doi, date, title,
                                        basename, pdf, jats, image, status))
        except Exception as ex:
            if __debug__: log(f'could not parse XML from server')
            alert('Unexpected or badly formed XML returned by server')
        return articles


# Miscellaneous utilities.
# .............................................................................

def volume_for_year(year):
    return int(year) - 2014

def tail_of_doi(doi):
    slash = doi.rfind('/')
    return doi[slash + 1:]
