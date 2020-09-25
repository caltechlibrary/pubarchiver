'''
files.py: utilities for working with files.

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2019-2020 by the California Institute of Technology.  This code
is open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

from   lxml import etree
import os
from   os import path
import shutil
from   sidetrack import log
import subprocess
import sys
import tarfile
import tempfile
import webbrowser
import zipfile
from   zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED

from .ui import warn, alert


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


def file_is_empty(file):
    return os.stat(file).st_size == 0


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


def filename_basename(file):
    parts = file.rpartition('.')
    if len(parts) > 1:
        return ''.join(parts[:-1]).rstrip('.')
    else:
        return file


def filename_extension(file):
    parts = file.rpartition('.')
    if len(parts) > 1:
        return '.' + parts[-1].lower()
    else:
        return ''


def module_path():
    '''Returns the absolute path to our module installation directory.'''
    # The path returned by module.__path__ is to the directory containing
    # the __init__.py file.
    this_module = sys.modules[__package__]
    module_path = this_module.__path__[0]
    return path.abspath(module_path)


def make_dir(dir_path):
    '''Creates directory 'dir_path' (including intermediate directories).'''
    if path.isdir(dir_path):
        if __debug__: log('reusing existing directory {}', dir_path)
        return
    else:
        if __debug__: log('creating directory {}', dir_path)
        # If this gets an exception, let it bubble up to caller.
        os.makedirs(dir_path)


def archive_directory(archive_file, source_dir, comment = None):
    root_dir = path.dirname(path.normpath(source_dir))
    base_dir = path.basename(source_dir)
    current_dir = os.getcwd()
    try:
        os.chdir(root_dir)
        with zipfile.ZipFile(archive_file, 'w', ZIP_STORED) as zf:
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    zf.write(os.path.join(root, file))
            if comment:
                zf.comment = comment.encode()
    finally:
        os.chdir(current_dir)


def archive_files(archive_file, files, comment = None):
    base_dir = path.dirname(path.normpath(files[0]))
    current_dir = os.getcwd()
    try:
        os.chdir(base_dir)
        with zipfile.ZipFile(archive_file, 'w', ZIP_STORED) as zf:
            for f in files:
                zf.write(path.basename(f))
            if comment:
                zf.comment = comment.encode()
    finally:
        os.chdir(current_dir)


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


def valid_xml(xml_file, dtd):
    if __debug__: log('parsing XML file {}', xml_file)
    try:
        root = etree.parse(xml_file)
    except etree.XMLSyntaxError as ex:
        alert('File contains XML syntax errors: {}', xml_file)
        # The string form of XMLSyntaxError includes line/col & file name.
        alert(str(ex))
        return False
    except Exception as ex:
        alert('Failed to parse XML file: {}', xml_file)
        alert(str(ex))
        return False
    if __debug__: log('validating {}', xml_file)
    if dtd:
        if dtd.validate(root):
            if __debug__: log('validated without errors')
            return True
        else:
            warn('Failed to validate {}', xml_file)
            warn('{} validation error{} encountered:', len(dtd.error_log),
                 's' if len(dtd.error_log) > 1 else '')
            for item in dtd.error_log:
                warn('Line {}, col {} ({}): {}', item.line, item.column,
                     item.type_name, item.message)
            return False
    else:
        return True
