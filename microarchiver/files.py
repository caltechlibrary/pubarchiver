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
import tempfile
import webbrowser
import zipfile
from   zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED

from .debug import log


# Main functions.
# .............................................................................

def readable(dest):
    '''Returns True if the given 'dest' is accessible and readable.'''
    return os.access(dest, os.F_OK | os.R_OK)


def writable(dest):
    '''Returns True if the destination is writable.'''

    # Helper function to test if a directory is writable.
    def dir_writable(dir):
        # This is based on the following Stack Overflow answer by user "zak":
        # https://stackoverflow.com/a/25868839/743730
        try:
            testfile = tempfile.TemporaryFile(dir = dir)
            testfile.close()
        except (OSError, IOError) as e:
            return False
        return True

    if path.exists(dest) and not path.isdir(dest):
        # Path is an existing file.
        return os.access(dest, os.F_OK | os.W_OK)
    elif path.isdir(dest):
        # Path itself is an existing directory.  Is it writable?
        return dir_writable(dest)
    else:
        # Path is a file but doesn't exist yet. Can we write to the parent dir?
        return dir_writable(path.dirname(dest))


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


def file_in_use(file):
    '''Returns True if the given 'file' appears to be in use.  Note: this only
    works on Windows, currently.
    '''
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
