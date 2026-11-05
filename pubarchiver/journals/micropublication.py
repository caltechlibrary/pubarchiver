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

from   bun import inform, warn, alert, alert_fatal
from   commonpy.network_utils import net
from   crossref.restful import Works, Etiquette
from   lxml import etree
from   os import path

if __debug__:
    from sidetrack import log

import pubarchiver
from   pubarchiver.article import Article
from   pubarchiver.exceptions import *
from   pubarchiver.journals.base import JournalAdapter


# Main class.
# .............................................................................

class Micropublication(JournalAdapter):
    name             = "microPublication"
    issn             = '2578-9430'
    doi_prefix       = '10.17912'
    uses_jats        = True
    metadata_source  = 'Crossref'
    base_urls        = ['https://www.micropublication.org']
    article_list_url = 'https://portal.micropublication.org/api/export/archives.xml'
    archive_basename = 'micropublication-org'
    license_name     = 'Creative Commons Attribution 4.0'
    license_url      = 'https://creativecommons.org/licenses/by/4.0/legalcode'
    etiquette        = Etiquette('PubArchiver', pubarchiver.__version__,
                                 'https://github.com/caltechlibrary/pubarchiver',
                                 'helpdesk@library.caltech.edu')


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
        '''Return a dict of metadata for the article, in the DataCite-style
        layout written to the Portico XML file, or None if Crossref has no
        record for the article.

        Bibliographic data comes from Crossref.  microPublication's Crossref
        deposits carry no abstract, so the abstract comes from the article's
        JATS file instead.
        '''
        try:
            if __debug__: log(f'asking Crossref for data about {article.doi}')
            data = Works(etiquette = self.etiquette).doi(article.doi)
        except Exception as ex:
            if __debug__: log(f'crossref API exception for {article.doi}: {str(ex)}')
            warn(f'Failed to get data from Crossref for {article.doi}: {str(ex)}')
            return None
        if not data:
            if __debug__: log(f'Crossref has no record for {article.doi}')
            return None

        year     = article.date.split('-')[0]
        journal  = (data.get('container-title') or [self.name])[0]
        resource = {
            '@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'identifier': {
                '@identifierType': 'DOI',
                '#text': article.doi.upper(),
            },
            'creators': {
                'creator': creator_list(data.get('author', [])),
            },
            'titles': {
                'title': article.title or (data.get('title') or [''])[0],
            },
            'publicationYear': year,
            'resourceType': {
                '@resourceTypeGeneral': 'JournalArticle',
            },
        }
        abstract = self._jats_abstract(article)
        if abstract:
            resource['descriptions'] = {
                'description': {
                    '@descriptionType': 'Abstract',
                    '#text': abstract,
                }
            }
        resource.update({
            'dates':      { 'date': article.date },
            'volume':     volume_for_year(year),
            'file':       article.basename + '.pdf',
            'journal':    journal,
            'e-issn':     self.issn,
            'rightsList': {
                'rights':    self.license_name,
                'rightsURI': self.license_url,
            },
        })
        return {'resource': resource}


    def _jats_abstract(self, article):
        '''Return the plain text of the abstract in the article's JATS file,
        or an empty string if it can't be obtained.'''
        if not article.jats:
            return ''
        (response, error) = net('get', article.jats)
        if error or not response or not response.content:
            if __debug__: log(f'could not get JATS for {article.doi}: {str(error)}')
            warn(f'Could not get abstract from JATS for {article.doi}')
            return ''
        try:
            parser = etree.XMLParser(load_dtd = False, no_network = True,
                                     resolve_entities = False)
            root = etree.fromstring(response.content, parser)
        except Exception as ex:
            if __debug__: log(f'could not parse JATS for {article.doi}: {str(ex)}')
            warn(f'Could not get abstract from JATS for {article.doi}')
            return ''
        abstract = root.find('.//article-meta/abstract')
        if abstract is None:
            if __debug__: log(f'JATS for {article.doi} has no abstract')
            return ''
        return ' '.join(''.join(abstract.itertext()).split())


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
                    if not doi:
                        doi = field_text(element, 'correctionDoi')
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


def creator_list(authors):
    '''Convert Crossref author records to DataCite-style creator records.
    Crossref gives organizational authors a single 'name' and no given or
    family name.'''
    creators = []
    for author in authors:
        given  = author.get('given', '')
        family = author.get('family', '')
        if family:
            name = f'{family}, {given}' if given else family
            creator = {'creatorName': name}
            if given:
                creator['givenName'] = given
            creator['familyName'] = family
        else:
            creator = {'creatorName': author.get('name', '')}
        creators.append(creator)
    return creators


def field_text(element, field):
    field_el = element.find(field)
    if field_el is None:
        return ''
    as_text = etree.tostring(field_el, encoding = 'unicode', method = 'text')
    return ' '.join(as_text.split())
