'''
article.py: simple record class for article information

Author
------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2019-2022 by the California Institute of Technology.  This code
is open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

from   recordclass import recordclass

Article = recordclass('Article', 'issn doi date title basename pdf jats image status')
'''
Record class used internally to communicate information about articles in the
article list.  The value of the "status" field can be as follows, and will
be different at different times in the process of getting information from
micropublication.org and writing out information for portico:

  'complete'   -- the info in the XML article list is complete
  'incomplete' -- something is missing in the XML article list entry
  'failed'     -- failed to download the article from the server
'''
