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

from   bs4 import BeautifulSoup
from   bun import inform, warn, alert, alert_fatal
from   commonpy.exceptions import NoContent
from   commonpy.network_utils import net
from   crossref.restful import Works, Etiquette
from   lxml import etree
from   os import path
import re

if __debug__:
    from sidetrack import log

import pubarchiver
from   pubarchiver.article import Article
from   pubarchiver.exceptions import *
from   pubarchiver.journals.base import JournalAdapter


# Constants.
# .............................................................................

_DATACITE_API_URL = 'https://api.datacite.org/dois/'

_ORCID_REGEX = re.compile(r'(\d{4}-\d{4}-\d{4}-\d{3}[\dX])$')


# Main class.
# .............................................................................

class Micropublication(JournalAdapter):
    name             = "microPublication"
    issn             = '2578-9430'
    doi_prefix       = '10.17912'
    uses_jats        = True
    metadata_source  = 'Crossref and DataCite'
    base_urls        = ['https://www.micropublication.org']
    article_list_url = 'https://portal.micropublication.org/api/export/archives.xml'
    archive_basename = 'micropublication-org'
    journal_title    = 'microPublication Biology'
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
        layout written to the Portico XML file, or None if neither Crossref
        nor DataCite has a record for the article.

        Bibliographic data comes from bibliographic_record().  The title
        comes from there too, not from microPublication's article list, whose
        titles have italicized words moved to the end.  The abstract
        comes from the article's JATS file, because microPublication's
        Crossref records have none, or from the DOI registration when the
        JATS has no abstract, as in the earliest articles.
        '''
        record = self.bibliographic_record(article)
        if not record:
            return None

        year     = article.date.split('-')[0]
        resource = {
            '@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'identifier': {
                '@identifierType': 'DOI',
                '#text': article.doi.upper(),
            },
            'creators': {
                'creator': creator_list(record['authors']),
            },
            'titles': {
                'title': record['title'] or article.title,
            },
            'publicationYear': year,
            'resourceType': {
                '@resourceTypeGeneral': 'JournalArticle',
            },
        }
        abstract = self._jats_abstract(article) or record['abstract']
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
            'journal':     record['journal'],
            'e-issn':     self.issn,
            'rightsList': {
                'rights':    self.license_name,
                'rightsURI': self.license_url,
            },
        })
        return {'resource': resource}


    def bibliographic_record(self, article):
        '''Return the article's bibliographic data from its DOI registration,
        or None if no registry has a record for it.

        microPublication's older DOIs are registered with DataCite and its
        newer ones with Crossref, and each registry has no record of the
        other's DOIs, so Crossref is asked first and DataCite second.  The
        result has the same layout whichever registry supplied it:

            source    'Crossref' or 'DataCite'
            title     article title, as plain text
            journal   journal title
            url       URL of the article's landing page
            issue     issue number, or ''
            abstract  plain text of the abstract, or ''
            authors   list of dicts with the keys 'given', 'family', 'name',
                      'affiliation', and 'orcid'; any may be ''
        '''
        record = self._crossref_record(article) or self._datacite_record(article)
        if not record:
            if __debug__: log(f'neither Crossref nor DataCite has {article.doi}')
        return record


    def _crossref_record(self, article):
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

        authors = []
        for author in data.get('author', []):
            affiliations = author.get('affiliation') or [{}]
            authors.append({
                'given':       author.get('given', ''),
                'family':      author.get('family', ''),
                'name':        author.get('name', ''),
                'affiliation': affiliations[0].get('name', ''),
                'orcid':       author.get('ORCID', ''),
            })
        return {
            'source':   'Crossref',
            'title':    plain_text(first(data.get('title'))),
            'journal':  first(data.get('container-title')) or self.journal_title,
            'url':      data.get('resource', {}).get('primary', {}).get('URL', ''),
            'issue':    data.get('issue', ''),
            'abstract': plain_text(data.get('abstract', '')),
            'authors':  authors,
        }


    def _datacite_record(self, article):
        if __debug__: log(f'asking DataCite for data about {article.doi}')
        (response, error) = net('get', _DATACITE_API_URL + article.doi)
        if error:
            if isinstance(error, NoContent):
                if __debug__: log(f'DataCite has no record for {article.doi}')
            else:
                if __debug__: log(f'error from DataCite for {article.doi}: {str(error)}')
                warn(f'Failed to get data from DataCite for {article.doi}: {str(error)}')
            return None
        try:
            data = response.json()['data']['attributes']
        except Exception as ex:
            if __debug__: log(f'unexpected DataCite response for {article.doi}: {str(ex)}')
            warn(f'Unexpected response from DataCite for {article.doi}')
            return None

        authors = []
        for creator in data.get('creators', []):
            orcids = [x.get('nameIdentifier', '') for x in creator.get('nameIdentifiers', [])
                      if x.get('nameIdentifierScheme', '').upper() == 'ORCID']
            affiliation = first(creator.get('affiliation'))
            if isinstance(affiliation, dict):
                affiliation = affiliation.get('name', '')
            given  = creator.get('givenName', '')
            family = creator.get('familyName', '')
            authors.append({
                'given':       given if family else '',
                'family':      family,
                'name':        '' if family else creator.get('name', ''),
                'affiliation': affiliation or '',
                'orcid':       first(orcids),
            })
        publisher = data.get('publisher')
        if isinstance(publisher, dict):
            publisher = publisher.get('name')
        journal = (data.get('container') or {}).get('title') or publisher
        abstracts = [d.get('description', '') for d in data.get('descriptions', [])
                     if d.get('descriptionType') == 'Abstract']
        return {
            'source':   'DataCite',
            'title':    plain_text(first([t.get('title') for t in data.get('titles', [])])),
            'journal':  journal or self.journal_title,
            'url':      data.get('url', ''),
            'issue':    (data.get('container') or {}).get('issue', ''),
            'abstract': plain_text(first(abstracts)),
            'authors':  authors,
        }


    def doaj_record(self, article):
        '''Return the article's metadata as a DOAJ incoming article, ready
        to send to DOAJ's article API, or None if neither Crossref nor
        DataCite has a record for the article.

        The format is DOAJ's IncomingArticleDO, documented at
        https://doaj.github.io/doaj-docs/master/data_models/IncomingAPIArticle
        Fields that DOAJ fills in from its journal record (journal title,
        publisher, country, language, and subject) are left out.

        Authors and affiliations come from the JATS, which has affiliations
        for every article; DataCite has none for older articles.  ORCID iDs
        come from the DOI registration, matched by family name, because the
        JATS has none.
        '''
        record = self.bibliographic_record(article)
        if not record:
            return None
        jats = self._jats_root(article)
        year, month = article.date.split('-')[:2]

        bibjson = {
            'title': record['title'] or article.title,
            'identifier': [
                {'type': 'doi',   'id': article.doi},
                {'type': 'eissn', 'id': self.issn},
            ],
            'year':  year,
            'month': str(int(month)),
        }
        authors = doaj_authors(jats_authors(jats), record['authors'])
        if authors:
            bibjson['author'] = authors
        abstract = jats_abstract(jats) or record['abstract']
        if abstract:
            bibjson['abstract'] = abstract
        keywords = jats_keywords(jats)
        if keywords:
            # DOAJ's documentation allows at most 6 keywords.
            bibjson['keywords'] = keywords[:6]
        url = article.url or record['url']
        if url:
            bibjson['link'] = [{'type': 'fulltext', 'url': url, 'content_type': 'HTML'}]
        journal = {}
        volume = jats_text(jats, './/article-meta/volume')
        if volume:
            journal['volume'] = volume
        if record['issue']:
            journal['number'] = record['issue']
        if journal:
            bibjson['journal'] = journal
        return {'bibjson': bibjson}


    def _jats_abstract(self, article):
        '''Return the plain text of the abstract in the article's JATS file,
        or an empty string if it can't be obtained.'''
        return jats_abstract(self._jats_root(article))


    def _jats_root(self, article):
        '''Return the parsed JATS file for the article, or None if it can't
        be obtained.'''
        if not article.jats:
            return None
        (response, error) = net('get', article.jats)
        if error or not response or not response.content:
            if __debug__: log(f'could not get JATS for {article.doi}: {str(error)}')
            warn(f'Could not get JATS for {article.doi}')
            return None
        try:
            parser = etree.XMLParser(load_dtd = False, no_network = True,
                                     resolve_entities = False)
            return etree.fromstring(response.content, parser)
        except Exception as ex:
            if __debug__: log(f'could not parse JATS for {article.doi}: {str(ex)}')
            warn(f'Could not parse JATS for {article.doi}')
            return None


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
                    url   = field_text(element, 'micropublication-permalink')
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
                                            basename, pdf, jats, image, status,
                                            url))
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
    '''Convert author records from bibliographic_record() to DataCite-style
    creator records.  Organizational authors have a name but no given or
    family name.'''
    creators = []
    for author in authors:
        given  = author['given']
        family = author['family']
        if family:
            name = f'{family}, {given}' if given else family
            creator = {'creatorName': name}
            if given:
                creator['givenName'] = given
            creator['familyName'] = family
        else:
            creator = {'creatorName': author['name']}
        creators.append(creator)
    return creators


def plain_text(text):
    '''Return text with any HTML or JATS tags removed and its whitespace
    collapsed to single spaces.'''
    if not text:
        return ''
    return ' '.join(BeautifulSoup(text, features = 'lxml').get_text().split())


def jats_text(root, xpath):
    '''Return the whitespace-normalized text of the first element matching
    xpath in a parsed JATS file, or '' if there is none.'''
    if root is None:
        return ''
    element = root.find(xpath)
    if element is None:
        return ''
    return ' '.join(''.join(element.itertext()).split())


def jats_abstract(root):
    '''Return the plain text of the abstract in a parsed JATS file.'''
    return jats_text(root, './/article-meta/abstract')


def jats_keywords(root):
    '''Return keywords for a parsed JATS file.  microPublication's JATS has
    no <kwd> elements; its "subject" and "species" categories serve instead.'''
    if root is None:
        return []
    keywords = [' '.join(''.join(k.itertext()).split())
                for k in root.findall('.//article-meta//kwd')]
    for group in root.findall('.//article-meta/article-categories/subj-group'):
        if group.get('subj-group-type') in ['subject', 'species']:
            keywords += [' '.join(''.join(s.itertext()).split())
                         for s in group.findall('subject')]
    return [k for k in dict.fromkeys(keywords) if k]


def jats_authors(root):
    '''Return the authors in a parsed JATS file as dicts with the keys
    'given', 'family', 'name', and 'affiliation', where the affiliation is
    the author's first one, without its label.'''
    if root is None:
        return []
    affiliations = {}
    for aff in root.findall('.//article-meta//aff'):
        label = aff.findtext('label') or ''
        text  = ' '.join(''.join(aff.itertext()).split())
        if label and text.startswith(label.strip()):
            text = text[len(label.strip()):].strip()
        affiliations[aff.get('id')] = text
    authors = []
    for contrib in root.findall('.//article-meta//contrib[@contrib-type="author"]'):
        name = contrib.find('name')
        rids = [x.get('rid') for x in contrib.findall('xref[@ref-type="aff"]')]
        affiliation = next((affiliations[r] for r in rids if affiliations.get(r)), '')
        if name is not None:
            authors.append({
                'given':       ' '.join((name.findtext('given-names') or '').split()),
                'family':      ' '.join((name.findtext('surname') or '').split()),
                'name':        '',
                'affiliation': affiliation,
            })
        else:
            collab = ' '.join(''.join(contrib.itertext()).split())
            if collab:
                authors.append({'given': '', 'family': '', 'name': collab,
                                'affiliation': affiliation})
    return authors


def doaj_authors(jats_authors, registry_authors):
    '''Return DOAJ author records.  Authors and affiliations come from the
    JATS when it has any authors, otherwise from the DOI registration.
    ORCID iDs come from the DOI registration, matched by family name, and
    are left out unless they have the form DOAJ requires,
    https://orcid.org/0000-0000-0000-0000.'''
    orcids = {}
    for author in registry_authors:
        orcid = doaj_orcid(author.get('orcid', ''))
        if orcid and author.get('family'):
            orcids[author['family'].casefold()] = orcid
    result = []
    for author in jats_authors or registry_authors:
        if author['family']:
            name = f"{author['given']} {author['family']}".strip()
        else:
            name = author['name']
        if not name:
            continue
        entry = {'name': name}
        if author['affiliation']:
            entry['affiliation'] = author['affiliation']
        orcid = doaj_orcid(author.get('orcid', '')) or orcids.get(author['family'].casefold())
        if orcid:
            entry['orcid_id'] = orcid
        result.append(entry)
    return result


def doaj_orcid(value):
    '''Return an ORCID iD in the form https://orcid.org/0000-0000-0000-0000,
    or '' if value is not an ORCID iD.'''
    match = _ORCID_REGEX.search(value or '')
    return f'https://orcid.org/{match.group(1)}' if match else ''


def first(items):
    '''Return the first item of a list, or '' if the list is empty or None.'''
    return items[0] if items else ''


def field_text(element, field):
    field_el = element.find(field)
    if field_el is None:
        return ''
    as_text = etree.tostring(field_el, encoding = 'unicode', method = 'text')
    return ' '.join(as_text.split())
