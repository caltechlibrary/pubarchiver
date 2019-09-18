'''
Microarchiver -- Package up microPublications for archiving in Portico

Authors
-------

Tom Morrell <tmorrell@caltech.edu> -- Caltech Library
Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2019 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import os
from   os import path
from   setuptools.config import read_configuration
import sys

# Set module-level dunder variables like __version__
# .............................................................................
# This code reads metadata values from ../setup.cfg and sets the corresponding
# module-level variables with '__' surrounding their names.  This approach
# avoids putting version and other info in more than one place.

keys = ['version', 'description', 'license', 'url', 'keywords',
        'author', 'author_email', 'maintainer', 'maintainer_email']

try:
    here        = path.abspath(path.dirname(__file__))
    conf_dict   = read_configuration(path.join(here, '..', 'setup.cfg'))
    conf        = conf_dict['metadata']
    this_module = sys.modules[__package__]
    for key in keys:
        if key in conf:
            variable_name = '__' + key + '__'
            setattr(this_module, variable_name, str(conf[key]))
except:
    pass
