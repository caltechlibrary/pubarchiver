'''
files.py: utilities for working with files.

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2019 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import os
from   os import path
import shutil
import subprocess
import sys
import tarfile
import webbrowser
import zipfile
from   zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED

import microarchiver
from microarchiver.debug import log


# Constants.
# .............................................................................

_APP_NAME = 'Microarchiver'
'''The human name of this application for human consumption.'''

_APP_REG_PATH = r'Software\Caltech Library\Microarchiver\Settings'
'''The Windows registry path for this application.'''


# Main functions.
# .............................................................................

def readable(dest):
    '''Returns True if the given 'dest' is accessible and readable.'''
    return os.access(dest, os.F_OK | os.R_OK)


def writable(dest):
    '''Returns True if the destination is writable.'''
    return os.access(dest, os.F_OK | os.W_OK)


def module_path():
    '''Returns the absolute path to our module installation directory.'''
    # The path returned by module.__path__ is to the directory containing
    # the __init__.py file.
    return path.abspath(microarchiver.__path__[0])


def installation_path():
    '''Returns the path to where the application is installed.'''
    # The path returned by module.__path__ is to the directory containing
    # the __init__.py file.  What we want here is the path to the installation
    # of the application binary.
    if sys.platform.startswith('win'):
        from winreg import OpenKey, CloseKey, QueryValueEx, HKEY_LOCAL_MACHINE, KEY_READ
        try:
            if __debug__: log('reading Windows registry entry')
            key = OpenKey(HKEY_LOCAL_MACHINE, _APP_REG_PATH)
            value, regtype = QueryValueEx(key, 'Path')
            CloseKey(key)
            if __debug__: log('path to windows installation: {}'.format(value))
            return value
        except WindowsError:
            # Kind of a problem. Punt and return a default value.
            return path.abspath('C:\Program Files\{}'.format(_APP_NAME))
    else:
        return path.abspath(path.join(module_path(), '..'))


def desktop_path():
    '''Returns the path to the user's desktop directory.'''
    if sys.platform.startswith('win'):
        return path.join(path.join(os.environ['USERPROFILE']), 'Desktop')
    else:
        return path.join(path.join(path.expanduser('~')), 'Desktop')


def datadir_path():
    '''Returns the path to Lost It's internal data directory.'''
    return path.join(module_path(), 'data')


def rename_existing(file):
    '''Renames 'file' to 'file.bak'.'''

    def rename(f):
        backup = f + '.bak'
        # If we fail, we just give up instead of throwing an exception.
        try:
            os.rename(f, backup)
            if __debug__: log('renamed {} to {}', file, backup)
        except:
            try:
                delete_existing(backup)
                os.rename(f, backup)
            except:
                if __debug__: log('failed to delete {}', backup)
                if __debug__: log('failed to rename {} to {}', file, backup)

    if path.exists(file):
        rename(file)
        return
    full_path = path.join(os.getcwd(), file)
    if path.exists(full_path):
        rename(full_path)
        return


def delete_existing(file):
    '''Delete the given file.'''
    # Check if it's actually a directory.
    if path.isdir(file):
        if __debug__: log('doing rmtree on directory {}', file)
        try:
            shutil.rmtree(file)
        except:
            if __debug__: log('unable to rmtree {}; will try renaming', file)
            try:
                rename_existing(file)
            except:
                if __debug__: log('unable to rmtree or rename {}', file)
    else:
        if __debug__: log('doing os.remove on file {}', file)
        os.remove(file)


def file_in_use(file):
    if not path.exists(file):
        return False
    if sys.platform.startswith('win'):
        # This is a hack, and it really only works for this purpose on Windows.
        try:
            os.rename(file, file)
            return False
        except:
            return True
    return False


def open_file(file):
    '''Open document with default application in Python.'''
    # Code originally from https://stackoverflow.com/a/435669/743730
    if __debug__: log('opening file {}', file)
    if sys.platform.startswith('darwin'):
        subprocess.call(('open', file))
    elif os.name == 'nt':
        os.startfile(file)
    elif os.name == 'posix':
        subprocess.call(('xdg-open', file))


def open_url(url):
    '''Open the given 'url' in a web browser using the current platform's
    default approach.'''
    if __debug__: log('opening url {}', url)
    webbrowser.open(url)


def make_dir(dir_path):
    '''Creates directory 'dir_path' (including intermediate directories).'''
    if path.isdir(dir_path):
        if __debug__: log('Reusing existing directory {}', dir_path)
        return
    else:
        if __debug__: log('Creating directory {}', dir_path)
        # If this gets an exception, let it bubble up to caller.
        os.makedirs(dir_path)


def create_archive(archive_file, type, source_dir, comment = None):
    root_dir = path.dirname(path.normpath(source_dir))
    base_dir = path.basename(source_dir)
    if type.endswith('zip'):
        format = ZIP_STORED if type.startswith('uncompress') else ZIP_DEFLATED
        current_dir = os.getcwd()
        try:
            os.chdir(root_dir)
            with zipfile.ZipFile(archive_file, 'w', format) as zf:
                for root, dirs, files in os.walk(base_dir):
                    for file in files:
                        zf.write(os.path.join(root, file))
                if comment:
                    zf.comment = comment.encode()
        finally:
            os.chdir(current_dir)
    else:
        if type.startswith('uncompress'):
            shutil.make_archive(source_dir, 'tar', root_dir, base_dir)
        else:
            shutil.make_archive(source_dir, 'gztar', root_dir, base_dir)


def verify_archive(archive_file, type):
    '''Check the integrity of an archive and raise an exception if needed.'''
    if type.endswith('zip'):
        error = ZipFile(archive_file).testzip()
        if error:
            raise CorruptedContent('Failed to verify file "{}"'.format(archive_file))
    else:
        # Algorithm originally from https://stackoverflow.com/a/32312857/743730
        tfile = None
        try:
            tfile = tarfile.open(archive_file)
            for member in tfile.getmembers():
                content = tfile.extractfile(member.name)
                if content:
                    for chunk in iter(lambda: content.read(1024), b''):
                        pass
        except Exception as ex:
            raise CorruptedContent('Failed to verify file "{}"'.format(archive_file))
        finally:
            if tfile:
                tfile.close()
