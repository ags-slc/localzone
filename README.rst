.. image:: https://localzone.iomaestro.com/_images/localzone.png
    :align: center
    :width: 100px
    :height: 100px
    :alt: Project link: localzone (calzone image by sobinsergey from the Noun Project)
    :target: https://localzone.iomaestro.com

A low-calorie library for managing DNS zones
============================================

.. code:: python

   import localzone

   with localzone.manage("db.example.com") as z:
       r = z.add_record("greeting", "TXT", "hello, world!")
       r.name    # the record name, i.e. "greeting"
       r.rdtype  # the record type, i.e. "TXT"
       r.content # the record content, i.e. "hello," "world!"


Powered by `dnspython <https://pypi.org/project/dnspython/>`_.


Features
--------

- A simple API focused on managing resource records in local zone files
- Support for almost all resource record types
- Auto-save and auto-serial
- Built for automation


Installing localzone
--------------------

.. code-block:: shell

    $ pip install localzone


Raison d'être
-------------

Comprehensive, low-level DNS toolkits can be cumbersome for the more common zone management tasks--especially those related to making simple changes to zone records. They can also come with a steep learning curve. Enter localzone: a simple library for managing DNS zones. While `localzone` may be a low-calorie library, it's stuffed full of everything that a hungry hostmaster needs.


License
-------

- BSD
- Calzone image by sobinsergey from the Noun Project

Where did the calories go? The likely `suspect <https://www.traegergrills.com/recipes/pork/meat-lovers-calzone-smoked-marinara>`_.
