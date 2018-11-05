#
# You have entered the localzone.
#

"""
The `localzone` DNS Library
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A simple DNS library, written in Python, for managing zone files.

Basic usage:

   >>> import localzone
   >>> with localzone.manage("db.example.com") as z:
   ...     r = z.add_record("greeting", "TXT", "hello, world!")
   ...     r.name    # the record name, i.e. 'greeting'
   ...     r.rdtype  # the record type, i.e. 'TXT'
   ...     r.content # the record content, i.e. '"hello," "world!"'
   ...

Print the zone's resource records:

   >>> import localzone
   >>> with localzone.manage("db.example.com") as z:
   ...     print(*z.records, sep="\\n")
   ...
   @ 3600 IN SOA ns username 2007120710 86400 7200 2419200 3600
   @ 3600 IN NS ns
   @ 3600 IN NS ns.somewhere.example.
   @ 3600 IN MX 10 mail
   @ ...

or:

   >>> import localzone
   >>> with localzone.manage("db.example.com") as z:
   >>>     for r in z.records:
   >>>         print(r)
   ...

The full documentation is available at <https://localzone.iomaestro.com>.

:copyright: (c) 2018 by Andrew Grant Spencer.
:license: BSD, see LICENSE for more details.
"""

from .context import manage, load
from .models import Zone, Record
