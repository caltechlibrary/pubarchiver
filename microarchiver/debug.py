'''
debug.py: debugging aids for Microarchiver

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2019 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import microarchiver


# Logger configuration.
# .............................................................................

if __debug__:
    import inspect
    import logging
    import os

    microarchiver_logger = logging.getLogger('microarchiver')
    formatter = logging.Formatter('%(name)s %(message)s')
    handler   = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    microarchiver_logger.addHandler(handler)

    # This next variable makes a huge speed difference.  It's used to avoid
    # having to call logging.getLogger('microarchiver').isEnabledFor(logging.DEBUG)
    # at runtime in log() to test whether debugging is turned on.
    microarchiver_debugging = False


# Exported functions.
# .............................................................................

def set_debug(enabled):
    '''Turns on debug logging if 'enabled' is True; turns it off otherwise.'''
    if __debug__:
        from logging import DEBUG, WARNING
        logging.getLogger('microarchiver').setLevel(DEBUG if enabled else WARNING)
        global microarchiver_debugging
        microarchiver_debugging = True


def log(s, *other_args):
    '''Logs a debug message. 's' can contain format directive, and the
    remaining arguments are the arguments to the format string.'''
    if __debug__:
        # This test for the level may seem redundant, but it's not: it prevents
        # the string format from always being performed if logging is not
        # turned on and the user isn't running Python with -O.
        global microarchiver_debugging
        if microarchiver_debugging:
            func = inspect.currentframe().f_back.f_code.co_name
            path = inspect.currentframe().f_back.f_code.co_filename
            filename = os.path.basename(path)
            logging.getLogger('microarchiver').debug('{} {}(): '.format(filename, func)
                                              + s.format(*other_args))
