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


if __debug__:
    from sidetrack import log

import pubarchiver
from   pubarchiver.exceptions import *
from   pubarchiver.journals.base import JournalAdapter


# Main class.
# .............................................................................

class PromptJournal(JournalAdapter):
    pass
