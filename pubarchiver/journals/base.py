'''
base.py: base class for journal interfaces

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018-2021 by the California Institute of Technology.  This code
is open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

from   collections import namedtuple
from   commonpy.file_utils import readable, relative

if __debug__:
    from sidetrack import log


# Class definitions.
# .............................................................................
# Basics for the __eq__ etc. methods came from
# https://stackoverflow.com/questions/1061283/lt-instead-of-cmp

class JournalAdapter(object):
    '''Base class for journal site adapters.'''

    # The publication name.  Used in printing file comments and such.
    name = None

    # The ISSN of the publication.
    issn = None

    # List of alternative base URLs for the journal site.
    base_urls = None

    # Base file name for the archives we create for this journal.
    archive_basename = None

    # Whether the journal provides JATS.
    uses_jats = False

    # Which source of metadata we use for this journal.
    metadata_source = None


    def __init__(self):
        pass


    def __str__(self):
        return self.name()


    def __repr__(self):
        return self.name()


    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.__dict__ == other.__dict__
        return NotImplemented


    def __ne__(self, other):
        # Based on lengthy Stack Overflow answer by user "Maggyero" posted on
        # 2018-06-02 at https://stackoverflow.com/a/50661674/743730
        eq = self.__eq__(other)
        if eq is not NotImplemented:
            return not eq
        return NotImplemented


    def __lt__(self, other):
        return self.name() < other.name()


    def __gt__(self, other):
        if isinstance(other, type(self)):
            return other.name() < self.name()
        return NotImplemented


    def __le__(self, other):
        if isinstance(other, type(self)):
            return not other.name() < self.name()
        return NotImplemented


    def __ge__(self, other):
        if isinstance(other, type(self)):
            return not self.name() < other.name()
        return NotImplemented


    def article_index(self):
        '''Return an XML list of all articles available.'''
        pass


    def articles_from(self, file_or_url):
        '''Returns a list of `Article` tuples from the given URL or file.'''
        pass
