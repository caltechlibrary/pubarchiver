'''
PubArchiver interfaces to journals.

Author
------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2019-2021 by the California Institute of Technology.  This code
is open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

from .micropublication import Micropublication
from .prompt import Prompt

KNOWN_JOURNALS = {
    'micropublication': Micropublication,
    'prompt': Prompt,
}

# Save this list to avoid recreating it all the time.
JOURNAL_LIST = sorted(KNOWN_JOURNALS.keys())

def journal_list():
    return JOURNAL_LIST

def journal_handler(name):
    return KNOWN_JOURNALS[name]() if name in KNOWN_JOURNALS else None
