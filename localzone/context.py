"""
localzone.context
~~~~~~~~~~~~~~~~~

This module implements the methods for localzone context management.

:copyright: (c) 2018 Andrew Grant Spencer
:license: BSD, see LICENSE for more details.
"""

from contextlib import contextmanager
import dns.name
import dns.rdataclass
import dns.tokenizer
import dns.zone
from .models import Zone


@contextmanager
def manage(filename, origin=None, autosave=False):
    """
    A context manager that yields a :class:`Zone <Zone>` object.

    :param filename: The path to the zone's master file.
    :type filename: string
    :param origin: (optional) The zone's origin domain
    :type origin: string
    :param autosave: (optional) controls whether or not the zone's master file
        is written to disk upon exit
    :type autosave: bool
    :return: :class:`Zone <Zone>` object
    :rtype: localzone.models.Zone
    """
    if origin:
        # perform basic validation/sanitization on origin
        origin = dns.name.from_text(origin).to_text()

    zone = load(filename, origin)

    try:
        yield zone
    finally:
        if autosave:
            zone.save()


def load(filename, origin=None):
    """
    Read a master zone file and construct a :class:`Zone <Zone>` object.

    :param filename: The path to the zone's master file.
    :type filename: string
    :param origin: (optional) The zone's origin domain
    :type origin: string
    :return: :class:`Zone <Zone>` object
    :rtype: localzone.Zone
    """
    with open(filename) as text:
        tok = dns.tokenizer.Tokenizer(text, filename)
        reader = dns.zone._MasterReader(
            tok,
            origin=origin,
            rdclass=dns.rdataclass.IN,
            relativize=True,
            zone_factory=Zone,
            allow_include=True,
            check_origin=True,
        )
        reader.read()

        # TODO: remember that any method using the zone.filename property should
        # have it passed as a parameter
        reader.zone._filename = filename

        # starting with dnspython v1.16.0, use default_ttl
        try:
            reader.zone._ttl = reader.default_ttl
        except AttributeError:
            reader.zone._ttl = reader.ttl

        return reader.zone
