'''
PubArchiver -- Package up publications for archiving in Portico

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

# Package metadata
# .............................................................................
#
#  ╭────────────────────── Notice ── Notice ── Notice ─────────────────────╮
#  |    The following values are automatically updated at every release    |
#  |    by the Makefile. Manual changes to these values will be lost.      |
#  ╰────────────────────── Notice ── Notice ── Notice ─────────────────────╯

__version__     = '2.1.1'
__description__ = 'Automation for archiving journals hosted by the Caltech Library'
__url__         = 'https://github.com/caltechlibrary/pubarchiver'
__author__      = 'Michael Hucka, Tom Morrell'
__email__       = 'mhucka@caltech.edu, tmorrell@library.caltech.edu'
__license__     = 'BSD 3-clause'


# Miscellaneous utilities
# .............................................................................

def print_version():
    print(f'{__name__} version {__version__}')
    print(f'Authors: {__author__}')
    print(f'URL: {__url__}')
    print(f'License: {__license__}')
