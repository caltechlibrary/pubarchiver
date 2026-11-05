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

from   bun import warn, alert, alert_fatal
from   commonpy.exceptions import NoContent
from   commonpy.network_utils import net
import html
from   lxml import etree
import re

if __debug__:
    from sidetrack import log

from   pubarchiver.article import Article
from   pubarchiver.exceptions import *
from   pubarchiver.journals.base import JournalAdapter


# Constants.
# .............................................................................

_ORCID_REGEX = re.compile(r'(\d{4}-\d{4}-\d{4}-\d{3}[\dX])$')


# Main class.
# .............................................................................

class Micropublication(JournalAdapter):
    name             = "microPublication"
    issn             = '2578-9430'
    doi_prefix       = '10.17912'
    uses_jats        = True
    metadata_source  = "microPublication's JATS"
    base_urls        = ['https://www.micropublication.org']
    article_list_url = 'https://portal.micropublication.org/api/export/archives.xml'
    archive_basename = 'micropublication-org'
    journal_title    = 'microPublication Biology'
    license_name     = 'Creative Commons Attribution 4.0'
    license_url      = 'https://creativecommons.org/licenses/by/4.0/legalcode'


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


    def article_metadata(self, article, record = None):
        '''Return a dict of metadata for the article, in the DataCite-style
        layout written to the Portico XML file, or None if the article's
        JATS file can't be obtained or lacks required metadata.  The
        metadata comes from bibliographic_record(); pass its result as
        `record` to avoid reading the JATS again.
        '''
        record = record or self.bibliographic_record(article)
        if not record:
            return None

        date     = record['date']
        year     = date.split('-')[0]
        resource = {
            '@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'identifier': {
                '@identifierType': 'DOI',
                '#text': record['doi'].upper(),
            },
            'creators': {
                'creator': creator_list(record['authors']),
            },
            'titles': {
                'title': record['title'],
            },
            'publicationYear': year,
            'resourceType': {
                '@resourceTypeGeneral': 'JournalArticle',
            },
        }
        if record['abstract']:
            resource['descriptions'] = {
                'description': {
                    '@descriptionType': 'Abstract',
                    '#text': record['abstract'],
                }
            }
        resource.update({
            'dates':      { 'date': date },
            'volume':     volume_for_year(year),
            'file':       article.basename + '.pdf',
            'journal':    record['journal'],
            'e-issn':     record['issn'],
            'rightsList': {
                'rights':    self.license_name,
                'rightsURI': self.license_url,
            },
        })
        return {'resource': resource}


    def bibliographic_record(self, article):
        '''Return the article's metadata from its JATS file, or None if the
        file can't be obtained or lacks a DOI, title, or publication date.

        microPublication's JATS is the source of all article metadata.  The
        article list is used only to select articles by date and to find
        their files and article pages.  Its titles have italicized words
        moved to the end, and its dates can differ from the JATS
        publication date.  The result is a dict with these keys:

            doi       DOI, which must match the article list's
            issn      electronic ISSN
            title     article title, as plain text
            date      publication date as YYYY-MM-DD
            journal   journal title
            volume    volume, or ''
            abstract  plain text of the abstract, or ''; the JATS of the
                      earliest articles has none
            keywords  list of keywords, possibly empty
            authors   list of dicts with the keys 'given', 'family', 'name',
                      'affiliation', and 'orcid'; any may be ''
        '''
        root = self._jats_root(article)
        if root is None:
            return None
        if root.find('.//article-meta') is None:
            warn(f'JATS for {article.doi} has no article metadata')
            return None
        doi   = jats_text(root, './/article-meta/article-id[@pub-id-type="doi"]')
        title = jats_text(root, './/article-meta/title-group/article-title')
        date  = jats_pub_date(root)
        missing = [name for name, value in [('DOI', doi), ('title', title),
                                            ('publication date', date)]
                   if not value]
        if missing:
            warn(f'JATS for {article.doi} has no ' + ', '.join(missing))
            return None
        if doi.lower() != article.doi.lower():
            warn(f'JATS for {article.doi} gives a different DOI, {doi}')
            return None
        return {
            'doi':      doi,
            'issn':     (jats_text(root, './/journal-meta/issn[@pub-type="epub"]')
                         or self.issn),
            'title':    title,
            'date':     date,
            'journal':  jats_text(root, './/journal-meta//journal-title') or self.journal_title,
            'volume':   jats_text(root, './/article-meta/volume'),
            'abstract': jats_abstract(root),
            'keywords': jats_keywords(root),
            'authors':  jats_authors(root),
        }


    def doaj_record(self, article, record = None):
        '''Return the article's metadata as a DOAJ incoming article, ready
        to send to DOAJ's article API, or None if the article's JATS file
        can't be obtained or lacks required metadata.  The metadata comes
        from bibliographic_record(); pass its result as `record` to avoid
        reading the JATS again.  The full-text link is the article's page
        on microPublication's site, from the article list, because the JATS
        doesn't give it.

        The format is DOAJ's IncomingArticleDO, documented at
        https://doaj.github.io/doaj-docs/master/data_models/IncomingAPIArticle
        Fields that DOAJ fills in from its journal record (journal title,
        publisher, country, language, and subject) are left out.

        Don't change the form of the DOI or the full-text link URL.  DOAJ
        matches a resent article to its existing record by either one, so a
        different form creates a duplicate record instead of an update.
        '''
        record = record or self.bibliographic_record(article)
        if not record:
            return None
        year, month = record['date'].split('-')[:2]

        bibjson = {
            'title': record['title'],
            'identifier': [
                {'type': 'doi',   'id': record['doi']},
                {'type': 'eissn', 'id': record['issn']},
            ],
            'year':  year,
            'month': str(int(month)),
        }
        authors = doaj_authors(record['authors'])
        if authors:
            bibjson['author'] = authors
        if record['abstract']:
            bibjson['abstract'] = record['abstract']
        if record['keywords']:
            # DOAJ's documentation allows at most 6 keywords.
            bibjson['keywords'] = record['keywords'][:6]
        if article.url:
            bibjson['link'] = [{'type': 'fulltext', 'url': article.url,
                                'content_type': 'HTML'}]
        if record['volume']:
            bibjson['journal'] = {'volume': record['volume']}
        return {'bibjson': bibjson}


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




def jats_text(root, xpath):
    '''Return the plain text of the first element matching xpath in a
    parsed JATS file, or '' if there is none.'''
    if root is None:
        return ''
    return plain_text(root.find(xpath))


# microPublication's JATS is pretty-printed: within an element that contains
# other elements, each child and each run of text starts on a new line,
# indented by the same amount.  Those line breaks and indentation are not
# part of the text.  Real spaces survive as a space before the line break or
# an extra space after the indentation.  Pretty-printing also drops text
# that was only whitespace, which leaves two kinds of trace: a line break
# alone between two elements, and an empty element (<italic/>) that held a
# space.  Joining the lines with spaces instead gives titles like
# "( Tsg101 )" and "Mecp2 -heterozygous".

_TRAILING_INDENT = re.compile(r'\n( *)$')
_LINE_INDENT     = re.compile(r'\n( *)(?=\S)')

def plain_text(element):
    '''Return the text of a JATS element as one line of plain text, with
    the line breaks and indentation of pretty-printing removed and
    character references such as "&#x3B3;" decoded.  microPublication's
    JATS escapes some characters twice, so they reach the parsed text as
    character references.'''
    if element is None:
        return ''
    return clean_text(_render(element))


def clean_text(text):
    '''Decode character references in text, remove zero-width spaces, and
    collapse whitespace.'''
    text = html.unescape(text or '').replace('\u200b', '')
    return ' '.join(text.split())


def _render(element):
    children = list(element)
    if not children:
        text = element.text or ''
        if not text:
            return ' '
        if not text.startswith('\n'):
            return text
        indents = [len(i) for i in _LINE_INDENT.findall(text)]
        return _unindent(text, min(indents) if indents else None)
    texts = [element.text or ''] + [c.tail or '' for c in children[:-1]]
    indents = [len(m.group(1)) for m in map(_TRAILING_INDENT.search, texts) if m]
    width = min(indents) if indents else None
    parts = [_text_piece(element.text, width, between = False)]
    for i, child in enumerate(children):
        parts.append(_render(child))
        tail = _text_piece(child.tail, width, between = i + 1 < len(children))
        # The space after an element that ends with another element, as in
        # <italic>pk<sup>pk1</sup></italic> and, is lost in pretty-printing.
        if _ends_with_element(child) and (child.tail or '').startswith('\n') \
           and tail[:1].isalnum():
            tail = ' ' + tail
        parts.append(tail)
    return ''.join(parts)


def _text_piece(text, width, between):
    text = text or ''
    if '\n' in text and not text.strip():
        return ' ' if between else ''
    return _unindent(text, width)


def _unindent(text, width):
    if width is None:
        return text
    return re.sub(r'\n {0,%d}' % width, '', text)


def _ends_with_element(element):
    children = list(element)
    return bool(children) and not (children[-1].tail or '').strip()


def jats_pub_date(root):
    '''Return the publication date in a parsed JATS file as YYYY-MM-DD,
    or '' if it has no complete one.  microPublication's JATS gives the
    date of electronic publication as <pub-date date-type="pub">.'''
    if root is None:
        return ''
    dates = root.findall('.//article-meta/pub-date')
    preferred = [d for d in dates if (d.get('date-type') or d.get('pub-type')) in ['pub', 'epub']]
    for date in preferred + dates:
        year, month, day = (' '.join((date.findtext(x) or '').split())
                            for x in ['year', 'month', 'day'])
        if year.isdigit() and month.isdigit() and day.isdigit():
            return f'{int(year):04d}-{int(month):02d}-{int(day):02d}'
    return ''


def jats_abstract(root):
    '''Return the plain text of the abstract in a parsed JATS file, with
    its paragraphs separated by spaces.'''
    if root is None:
        return ''
    abstract = root.find('.//article-meta/abstract')
    if abstract is None:
        return ''
    paragraphs = abstract.findall('.//p') or [abstract]
    return ' '.join(text for text in map(plain_text, paragraphs) if text)


def jats_keywords(root):
    '''Return keywords for a parsed JATS file.  microPublication's JATS has
    no <kwd> elements; its "subject" and "species" categories serve instead.'''
    if root is None:
        return []
    keywords = [plain_text(k) for k in root.findall('.//article-meta//kwd')]
    for group in root.findall('.//article-meta/article-categories/subj-group'):
        if group.get('subj-group-type') in ['subject', 'species']:
            keywords += [plain_text(s) for s in group.findall('subject')]
    return [k for k in dict.fromkeys(keywords) if k]


def jats_authors(root):
    '''Return the authors in a parsed JATS file as dicts with the keys
    'given', 'family', 'name', 'affiliation', and 'orcid', where the
    affiliation is the author's first one, without its label.'''
    if root is None:
        return []
    affiliations = {}
    for aff in root.findall('.//article-meta//aff'):
        label = aff.findtext('label') or ''
        text  = plain_text(aff)
        if label and text.startswith(label.strip()):
            text = text[len(label.strip()):].strip()
        affiliations[aff.get('id')] = text
    authors = []
    for contrib in root.findall('.//article-meta//contrib[@contrib-type="author"]'):
        name = contrib.find('name')
        rids = [x.get('rid') for x in contrib.findall('xref[@ref-type="aff"]')]
        affiliation = next((affiliations[r] for r in rids if affiliations.get(r)), '')
        orcid = clean_text(contrib.findtext('contrib-id[@contrib-id-type="orcid"]'))
        if name is not None:
            authors.append({
                'given':       plain_text(name.find('given-names')),
                'family':      plain_text(name.find('surname')),
                'name':        '',
                'affiliation': affiliation,
                'orcid':       orcid,
            })
        else:
            collab = plain_text(contrib.find('collab'))
            if collab:
                authors.append({'given': '', 'family': '', 'name': collab,
                                'affiliation': affiliation, 'orcid': orcid})
    return authors


def doaj_authors(authors):
    '''Return DOAJ author records for authors from jats_authors().  ORCID
    iDs are left out unless they can be put in the form DOAJ requires,
    https://orcid.org/0000-0000-0000-0000.'''
    result = []
    for author in authors:
        if author['family']:
            name = f"{author['given']} {author['family']}".strip()
        else:
            name = author['name']
        if not name:
            continue
        entry = {'name': name}
        if author['affiliation']:
            entry['affiliation'] = author['affiliation']
        orcid = doaj_orcid(author['orcid'])
        if orcid:
            entry['orcid_id'] = orcid
        result.append(entry)
    return result


def doaj_orcid(value):
    '''Return an ORCID iD in the form https://orcid.org/0000-0000-0000-0000,
    or '' if value is not an ORCID iD.'''
    match = _ORCID_REGEX.search(value or '')
    return f'https://orcid.org/{match.group(1)}' if match else ''


def field_text(element, field):
    field_el = element.find(field)
    if field_el is None:
        return ''
    as_text = etree.tostring(field_el, encoding = 'unicode', method = 'text')
    return ' '.join(as_text.split())
