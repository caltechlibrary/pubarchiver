'''
prompt.py: interface to The Prompt Journal

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
from   crossref.restful import Works, Etiquette
import xmltodict

if __debug__:
    from sidetrack import log

import pubarchiver
from   pubarchiver.article import Article
from   pubarchiver.exceptions import *
from   pubarchiver.journals.base import JournalAdapter


# Main class.
# .............................................................................

class Prompt(JournalAdapter):
    name             = "Prompt"
    issn             = '2578-9430'
    doi_prefix       = '10.31719'
    uses_jats        = False
    metadata_source  = 'Crossref'
    base_urls        = ['https://thepromptjournal.com', 'http://thepromptjournal.com']
    archive_basename = 'prompt'
    etiquette        = Etiquette('PubArchiver', pubarchiver.__version__,
                                 'https://github.com/caltechlibrary/pubarchiver',
                                 'helpdesk@library.caltech.edu')


    def all_articles(self):
        articles = []
        try:
            works = Works(etiquette = Prompt.etiquette)
            if __debug__: log(f'asking Crossref for all works by {self.doi_prefix}')
            for item in works.filter(prefix = self.doi_prefix):
                doi      = item.get('DOI', '')
                title    = item.get('title', [''])[0]
                online   = item.get('published-online', None)
                if not online or 'date-parts' not in online:
                    if __debug__: log(f'skipping {doi} lacking published-online')
                    continue
                else:
                    date = '-'.join(format(x, '02') for x in online['date-parts'][0])
                    if __debug__: log(f'keeping publication {doi} dated {date}')
                pdf = pdf_link(item.get('link', []))
                jats = ''
                image = ''
                basename = tail_of_doi(doi)
                status = 'complete' if all([pdf, doi, title, date]) else 'incomplete'
                articles.append(Article(self.issn, doi, date, title,
                                        basename, pdf, jats, image, status))
        except Exception as ex:
            if __debug__: log(f'crossref API exception: {str(ex)}')
            raise ServerError(f'Failed to get data from Crossref: {str(ex)}')
        return articles


    def articles_from(self, doi_file):
        '''Returns a list of `Article` tuples from a file of DOIs.'''
        if __debug__: log(f'reading {doi_file}')
        requested_dois = []
        with open(doi_file, 'r') as file:
            requested_dois = [line.strip() for line in file]

        num = len(requested_dois)
        # I'd use pluralized() here, but it matches case when it adds a 's',
        # and is confused by DOI which is an acronym.  Must add 's' ourselves.
        inform(f'Found {num} DOI{"s" if num > 1 else ""} in {doi_file}.')
        if not requested_dois:
            if __debug__: log(f'could not read any lines from {doi_file}')
            return []

        all_articles = self.all_articles()
        all_dois = [article.doi for article in all_articles]
        skipped = 0
        for doi in requested_dois:
            if doi not in all_dois:
                warn(f'Skipping "{doi}" because it is unknown for this journal.')
                skipped += 1
        if skipped:
            kept = num - skipped
            inform(f'Using {kept} DOI{"s" if kept > 1 else ""} from {doi_file}.')
        return [article for article in all_articles if article.doi in requested_dois]


    def article_metadata(self, article):
        try:
            works   = Works(etiquette = Prompt.etiquette)
            if __debug__: log(f'asking Crossref for data about {article.doi}')
            data    = works.doi(article.doi)
            year    = article.date.split('-')[0]
            file    = tail_of_doi(article.doi) + '.pdf'
            field   = lambda key: data.get(key, '')
            if isinstance(field('license'), list) and len(field('license')) > 1:
                rights_link = field('license')[0]['URL']
            else:
                rights_link  = 'https://creativecommons.org/licenses/by-nc/4.0/'
            xmldict = {
                'resource': {
                    '@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                    'identifier': {
                        '@identifierType': 'DOI',
                        '#text': article.doi
                    },
                    'journal':         { '#text': self.name, },
                    'volume':          { '#text': field('volume') },
                    'issue':           { '#text': field('issue') },
                    'publisher':       { '#text': field('publisher') },
                    'publicationYear': { '#text': year },
                    'e-issn':          { '#text': self.issn },
                    'file':            { '#text': file },
                    'dates': {
                        'date': {
                            '#text': article.date
                        },
                    },
                    'titles': {
                        'title': {
                            '#text': article.title
                        }
                    },
                    'creators': {
                        'creator': creator_list(field('author')),
                    },
                    'descriptions': {
                        'description': {
                            '@descriptionType': 'Abstract',
                            '#text': strip_tags(field('abstract'))
                        }
                    },
                    'rightsList': {
                        'rights': {
                            '#text': copyright_text(field('author'), year),
                        },
                        'rightsURI': {
                            '#text': rights_link
                        }
                    },

                }
            }
            return xmldict
        except Exception as ex:
            if __debug__: log(f'crossref API exception: {str(ex)}')
            foo = ex
            import pdb; pdb.set_trace()


# Miscellaneous utilities.
# .............................................................................

def tail_of_doi(doi):
    slash = doi.rfind('/')
    return doi[slash + 1:]


def pdf_link(all_links):
    pdf_info = [x for x in all_links if x['content-type'] == 'application/pdf']
    return pdf_info[0]['URL'] if pdf_info else ''


def strip_tags(text):
    return BeautifulSoup(text, features = 'lxml').get_text()


def creator_list(authors):
    return [{'givenName': { '#text': a['given'] }, 'familyName': { '#text': a['family'] }}
            for a in authors]


def copyright_text(authors, year):
    author_list = [f'{a["given"]} {a["family"]}' for a in authors]
    return f'Copyright (c) {year} ' + ', '.join(author_list)
