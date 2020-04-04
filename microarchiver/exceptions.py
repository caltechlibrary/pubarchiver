'''
exceptions.py: exceptions defined by Microarchiver

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2019-2020 by the California Institute of Technology.  This code
is open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

class NetworkFailure(Exception):
    '''Unrecoverable problem involving network operations.'''
    pass

class ServiceFailure(Exception):
    '''Unrecoverable problem involving network services.'''
    pass

class AuthenticationFailure(Exception):
    '''Problem obtaining or using authentication credentials.'''
    pass

class NoContent(Exception):
    '''Server returned a code 401 or 404, indicating no content found.'''

class CorruptedContent(Exception):
    '''Content corruption has been detected.'''
    pass

class RateLimitExceeded(Exception):
    '''The service flagged reports that its rate limits have been exceeded.'''
    pass

class InternalError(Exception):
    '''Unrecoverable problem involving Microarchiver itself.'''
    pass
