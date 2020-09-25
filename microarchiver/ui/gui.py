'''
gui.py: GUI class

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2019-2020 by the California Institute of Technology.  This code
is open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

from   pubsub import pub
from   queue import Queue
from   sidetrack import log
import wx
import wx.adv
import wx.lib
from   wx.lib.dialogs import ScrolledMessageDialog
import wx.richtext

from .base import UIBase


# Exported classes.
# .............................................................................

class GUI(UIBase):
    '''Graphical user interface.'''

    def __init__(self, name, subtitle, use_gui, use_color, be_quiet):
        super().__init__(name, subtitle, use_gui, use_color, be_quiet)

        # Initialize our main GUI window.
        self._app = wx.App()
        self._frame = AppFrame(name, subtitle, None, wx.ID_ANY)
        self._app.SetTopWindow(self._frame)
        self._frame.Center()
        self._frame.Show(True)

        # Initialize some stuff we use to communicate with dialogs.
        self._queue = Queue()
        self._response = None


    def start(self):
        '''Start the user interface.'''
        if __debug__: log('starting main UI loop')
        self._app.MainLoop()


    def stop(self):
        '''Stop the user interface.'''
        if __debug__: log('stopping UI')
        wx.CallAfter(self._frame.Destroy)


    def confirm(self, question):
        '''Asks the user a yes/no question using a GUI dialog.'''
        if __debug__: log('generating yes/no dialog')
        wx.CallAfter(self._ask_yes_no, question)
        self._wait()
        if __debug__: log('got response: {}', self._response)
        return self._response


    def login_details(self, prompt, user = None, password = None):
        '''Shows a login-and-password dialog, and returns a tuple of user,
        password, and a Boolean indicating whether the user cancelled the
        dialog.  The dialog will be filled in with the values of 'user' and/or
        'password', if they are provided.
        '''
        # This uses a threadsafe queue to implement a semaphore.  The
        # login_dialog will put a results tuple on the queue, but until then,
        # a get() on the queue will block.  Thus, this function will block
        # until the login dialog is closed by the user.
        results = Queue()
        if __debug__: log('sending message to login_dialog')
        wx.CallAfter(pub.sendMessage, "login_dialog", results = results,
                     user = user, password = password)
        if __debug__: log('blocking to get results')
        results_tuple = results.get()
        if __debug__: log('name_and_password results obtained')
        # Results will be a tuple of user, password, cancelled
        return results_tuple[0], results_tuple[1], results_tuple[2]


    def file_selection(self, type, message, pattern):
        return_queue = Queue()
        if __debug__: log('sending message to {}_file', type)
        if type == 'open':
            wx.CallAfter(pub.sendMessage, 'open_file', return_queue = return_queue,
                         message = message, pattern = pattern)
        else:
            wx.CallAfter(pub.sendMessage, 'save_file', return_queue = return_queue,
                         message = message)
        if __debug__: log('blocking to get results')
        return_queue = return_queue.get()
        if __debug__: log('got results')
        return return_queue


    def inform(self, text, *args):
        '''Print an informational message.'''
        if __debug__: log('generating info notice')
        wx.CallAfter(pub.sendMessage, "info_message", message = text.format(*args))


    def warn(self, text, *args):
        '''Print a nonfatal, noncritical warning message.'''
        if __debug__: log('generating warning notice')
        wx.CallAfter(pub.sendMessage, "info_message",
                     message = 'Warning: ' + text.format(*args))


    def alert(self, text, *args, **kwargs):
        '''Print a message reporting a critical error.'''
        if __debug__: log('generating error notice')
        message = text.format(*args)
        details = kwargs['details'] if 'details' in kwargs else ''
        if wx.GetApp().TopWindow:
            wx.CallAfter(self._show_alert_dialog, message, details, 'error')
        else:
            # The app window is gone, so wx.CallAfter won't work.
            self._show_alert_dialog(message, details, 'error')
        self._wait()


    def alert_fatal(self, text, *args, **kwargs):
        '''Print a message reporting a fatal error.  The keyword argument
        'details' can be supplied to pass a longer explanation that will be
        displayed if the user presses the 'Help' button in the dialog.

        When the user clicks on 'OK', this causes the UI to quit.  It should
        result in the application to shut down and exit.
        '''
        if __debug__: log('generating fatal error notice')
        message = text.format(*args)
        details = kwargs['details'] if 'details' in kwargs else ''
        if wx.GetApp().TopWindow:
            wx.CallAfter(self._show_alert_dialog, message, details, 'fatal')
        else:
            # The app window is gone, so wx.CallAfter won't work.
            self._show_alert_dialog(message, details, 'fatal')
        self._wait()
        wx.CallAfter(pub.sendMessage, 'stop')


    def _ask_yes_no(self, question):
        '''Display a yes/no dialog.'''
        frame = self._current_frame()
        dlg = wx.GenericMessageDialog(frame, question, caption = "Check It!",
                                      style = wx.YES_NO | wx.ICON_QUESTION)
        clicked = dlg.ShowModal()
        dlg.Destroy()
        frame.Destroy()
        self._response = (clicked == wx.ID_YES)
        self._queue.put(True)


    def _show_note(self, text, *args, severity = 'info'):
        '''Displays a simple notice with a single OK button.'''
        if __debug__: log('showing note dialog')
        frame = self._current_frame()
        icon = wx.ICON_WARNING if severity == 'warn' else wx.ICON_INFORMATION
        dlg = wx.GenericMessageDialog(frame, text.format(*args),
                                      caption = "Check It!", style = wx.OK | icon)
        clicked = dlg.ShowModal()
        dlg.Destroy()
        frame.Destroy()
        self._queue.put(True)


    def _show_alert_dialog(self, text, details, severity = 'error'):
        if __debug__: log('showing message dialog')
        frame = self._current_frame()
        if severity == 'fatal':
            short = text
            style = wx.OK | wx.ICON_ERROR
            extra_text = 'fatal '
        else:
            short = text + '\n\nWould you like to try to continue?\n(Click "no" to quit now.)'
            style = wx.YES_NO | wx.YES_DEFAULT | wx.ICON_EXCLAMATION
            extra_text = ''
        if details:
            style |= wx.HELP
        caption = "Check It! has encountered a {}problem".format(extra_text)
        dlg = wx.MessageDialog(frame, message = short, style = style, caption = caption)
        clicked = dlg.ShowModal()
        if clicked == wx.ID_HELP:
            body = ("Check It! has encountered a problem:\n"
                    + "─"*30
                    + "\n{}\n".format(details or text)
                    + "─"*30
                    + "\nIf the problem is due to a network timeout or "
                    + "similar transient error, then please quit and try again "
                    + "later. If you don't know why the error occurred or "
                    + "if it is beyond your control, please also notify the "
                    + "developers. You can reach the developers via email:\n\n"
                    + "    Email: mhucka@library.caltech.edu\n")
            info = ScrolledMessageDialog(frame, body, "Error")
            info.ShowModal()
            info.Destroy()
            frame.Destroy()
            self._queue.put(True)
            if 'fatal' in severity:
                if __debug__: log('sending stop message to UI')
                wx.CallAfter(pub.sendMessage, 'stop')
        elif clicked in [wx.ID_NO, wx.ID_OK]:
            dlg.Destroy()
            frame.Destroy()
            self._queue.put(True)
            if __debug__: log('sending stop message to UI')
            wx.CallAfter(pub.sendMessage, 'stop')
        else:
            dlg.Destroy()
            self._queue.put(True)


    def _current_frame(self):
        '''Returns the current application frame, or a new app frame if none
        is currently active.  This makes it possible to use dialogs when the
        application main window doesn't exist.'''
        if wx.GetApp():
            if __debug__: log('app window exists; building frame for dialog')
            app = wx.GetApp()
            frame = wx.Frame(app.TopWindow)
        else:
            if __debug__: log("app window doesn't exist; creating one for dialog")
            app = wx.App(False)
            frame = wx.Frame(None, -1, __package__)
        frame.Center()
        return frame


    def _wait(self):
        self._queue.get()
