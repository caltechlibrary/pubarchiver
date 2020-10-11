'''
cli.py: CLI class

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2019-2020 by the California Institute of Technology.  This code
is open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import getpass
from   sidetrack import log
import sys

from .base import UIBase
from .styled import Styled


# Exported classes.
# .............................................................................

class CLI(UIBase, Styled):
    '''Command-line interface.'''

    def __init__(self, name, subtitle, use_gui, use_color, be_quiet):
        UIBase.__init__(self, name, subtitle, use_gui, use_color, be_quiet)
        Styled.__init__(self, apply_styling = not use_gui, use_color = use_color)


    def start(self):
        '''Start the user interface.'''
        pass


    def stop(self):
        '''Stop the user interface.'''
        pass


    def inform(self, text, *args):
        '''Print an informational message.'''
        if __debug__: log(text, *args)
        if not self._be_quiet:
            print(self.info_text(text, *args), flush = True)


    def warn(self, text, *args):
        '''Print a nonfatal, noncritical warning message.'''
        if __debug__: log(text, *args)
        print(self.warning_text(text, *args), flush = True)


    def alert(self, text, *args):
        '''Print a message reporting an error.'''
        if __debug__: log(text, *args)
        print(self.error_text(text, *args), flush = True)


    def alert_fatal(self, text, *args, **kwargs):
        '''Print a message reporting a fatal error.

        This method returns after execution and does not force an exit of
        the application.  In that sense it mirrors the behavior of the GUI
        version of alert_fatal(...), which also returns, but unlike the GUI
        version, this method does not stop the user interface (because in the
        CLI case, there is nothing equivalent to a GUI to shut down).
        '''
        if __debug__: log(text, *args)
        text += '\n' + kwargs['details'] if 'details' in kwargs else ''
        print(self.fatal_text(text, *args), flush = True)


    def confirm(self, question):
        '''Asks a yes/no question of the user, on the command line.'''
        return input("{} (y/n) ".format(question)).startswith(('y', 'Y'))


    def file_selection(self, operation_type, question, pattern):
        '''Ask the user to type in a file path.'''
        return input(operation_type.capitalize() + ' ' + question + ': ')


    def login_details(self, prompt, user = None, pswd = None):
        '''Returns a tuple of user, password, and a Boolean indicating
        whether the user cancelled the dialog.  If 'user' is provided, then
        this method offers that as a default for the user.  If both 'user'
        and 'pswd' are provided, both the user and password are offered as
        defaults but the password is not shown to the user.
        '''
        try:
            text = (prompt + ' [default: ' + user + ']: ') if user else (prompt + ': ')
            input_user = input(text)
            if len(input_user) == 0:
                input_user = user
            hidden = ' [default: ' + '*'*len(pswd) + ']' if pswd else ''
            text = 'Password' + (' for "' + user + '"' if user else '') + hidden + ': '
            input_pswd = password(text)
            if len(input_pswd) == 0:
                input_pswd = pswd
            return input_user, input_pswd, False
        except KeyboardInterrupt:
            return user, pswd, True


# Miscellaneous utilities
# .............................................................................

def password(prompt):
    # If it's a tty, use the version that doesn't echo the password.
    if sys.stdin.isatty():
        return getpass.getpass(prompt)
    else:
        sys.stdout.write(prompt)
        sys.stdout.flush()
        return sys.stdin.readline().rstrip()
