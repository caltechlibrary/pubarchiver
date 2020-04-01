'''
text_styles: color & style definitions for use with Python colorful.

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2019-2020 by the California Institute of Technology.  This code
is open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import colorful

# The following defines the basic styles we use in this application.
# Regarding the ones like 'bold': There are more possible using the Python
# colorful and other packages, but not all work on all platforms
# (particularly Windows) and not all are that useful in pratice.  Note: the
# following have to be defined after the palette above is loaded into
# "colorful", or else the colors used below will not be defined when the
# _COLORS dictionary is created at load time.

colorful.update_palette({
    'springGreen4'    : (  0, 139, 69),
})

_STYLES = {
    'info'          : colorful.springGreen4,
    'warn'          : colorful.orange,
    'warning'       : colorful.orange,
    'error'         : colorful.red,
    'fatal'         : colorful.red & colorful.bold & colorful.underlined,

    'blink'         : colorful.blinkslow,
    'bold'          : colorful.bold,
    'italic'        : colorful.italic,
    'struckthrough' : colorful.struckthrough,
    'underlined'    : colorful.underlined,
}

colorful.update_palette(_STYLES)
