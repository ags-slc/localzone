"""
localzone.models
~~~~~~~~~~~~~~~~

This module contains the primary objects that power localzone.

:copyright: (c) 2018 Andrew Grant Spencer
:license: BSD, see LICENSE for more details.
"""

from collections import namedtuple
from time import strftime, localtime, time
from dns.zone import Zone as DNSZone
import dns.name
import dns.rdata
import dns.rdataclass
import dns.rdatatype
from .util import checksum


class Zone(DNSZone):
    """
    Initialize a :class:`Zone <Zone>` object.

    The Zone class extends its base class dns.zone.Zone with additional
    abstractions (or denormalizations) for dealing with DNS zone records.

    :param origin: The zone's origin.
    :type origin: :class:`dns.name.Name <Name>` object or string
    :param rdclass: The zone's rdata class; the default is class
        `dns.rdataclass.IN`.
    :type rdclass: int
    :param relativize: Should the zone's names be relativized to the origin?
    :type relativize: bool
    """

    def _increment_serial(self):
        """
        Increment the zone's serial.
        Credit: https://bitbucket.org/chrismiles/easyzone/
        """
        next_serial = int(strftime("%Y%m%d00", localtime(time())))

        if next_serial <= self.soa.rdata.serial:
            next_serial = self.soa.rdata.serial + 1

        # TODO: this is cheating a little bit, since record rdata is mutable.
        # The immutable hashid of the SOA record will be out of sync until the
        # record is released. Probably not a big deal, as there is really no
        # reason to hold the record given the existence of the soa property.
        # Should this implementation be reconsidered?
        try:
            self.soa.rdata.serial = next_serial
        except TypeError:
            content = self.soa.rdata.replace(serial=next_serial).to_text()
            self.update_record(self.soa.hashid, content)

    def save(self, filename=None, autoserial=True):
        """
        Write the zone master file to disk. If `filename` is not provided, the
        file from which the zone was originally loaded will be written.

        NB: this will replace the file located at `filename`.

        :param filename: The location to where the zone master file will be
            written.
        :type filename: string
        :param autoserial: Should the zone's serial be updated automatically?
        :type autoserial: bool
        """
        if not filename:
            filename = self.filename

        if autoserial:
            self._increment_serial()

        # TODO: investigate subclassing dns.zone.Zone.to_file() to support the
        # `$ORIGIN` and `$TTL` directives, e.g. with_origin=True, with_ttl=True.
        self.to_file(filename)

    def get_record(self, hashid):
        """
        Get a resource record via ID. If no record is found, raise a `KeyError`.

        :param hashid: The record's ID.
        :type hashid: string
        :return: :class:`Record <Record>` object
        :rtype: localzone.models.Record
        """
        record = next((r for r in self.records if r.hashid == hashid), None)

        if not record:
            raise KeyError("The supplied hashid was not found in the zone")

        return record

    def get_records(self, rdtype):
        """
        Create and return a list of each resource record in the zone matching
        the specified type. If rdtype is `"ANY"`, all zone records are returned.

        :param rdtype: The record's type.
        :type rdtype: string
        :return: list of :class:`Record <Record>` objects
        :rtype: list
        """
        result = []

        for n in self.nodes:
            for rds in self[n]:
                for r in rds:
                    if (
                        r.rdtype == dns.rdatatype.from_text(rdtype)
                        or rdtype.upper() == "ANY"
                    ):
                        record = Record(self.origin, n, self[n], rds, r)
                        result.append(record)

        return result

    # TODO: was a default rdtype required because of lexicon?
    # otherwise, remove the default.
    def find_record(self, rdtype="ANY", name=None, content=None):
        """
        Create and return a list of each resource record in the zone matching
        the search criteria.

        :param rdtype: The record's type.
        :type rdtype: string
        :param name: The record's name.
        :type name: string
        :param content: The record's content.
        :type content: string
        :return: list of :class:`Record <Record>` objects
        :rtype: list
        """
        result = []

        # relativize the name
        if name:
            name_obj = dns.name.from_text(name, origin=self.origin)
            name = name_obj.relativize(self.origin).to_text()

        if rdtype.upper() == "TXT" and content:
            # Content of record type `TXT` has enclosing quotes. See:
            # https://git.io/fxART

            # TODO: will this match for multiline records e.g. domainkeys?
            # Maybe we should strip quotes instead? i.e. r.content.strip('\"')
            content = '"%s"' % content

        for r in self.get_records(rdtype):
            if (
                (r.name == name and r.content == content)
                or (r.name == name and not content)
                or (r.content == content and not name)
                or (not name and not content)
            ):
                result.append(r)

        return result

    def add_record(self, name, rdtype, content, rdclass="IN", ttl=None):
        """
        Add a resource record to the zone.

        :param name: The record's name.
        :type name: string
        :param rdtype: The record's type, e.g. "CNAME".
        :type rdtype: string
        :param content: The record's content.
        :type content: string
        :param rdclass: The record's class.
        :type rdclass: string
        :param ttl: The record's TTL.
        :type ttl: ttl
        :return: :class:`Record <Record>` object
        :rtype: localzone.models.Record
        """
        # TODO: standardize on named params?

        # convert string parameters to dnspython objects
        name = dns.name.from_text(name, self.origin)
        rdclass = dns.rdataclass.from_text(rdclass)
        rdtype = dns.rdatatype.from_text(rdtype)

        # TODO: won't this always be the case?
        if name.is_subdomain(self.origin):
            name = name.relativize(self.origin)

        if not ttl:
            ttl = self.ttl

        # create the record data
        rdata = dns.rdata.from_text(rdclass, rdtype, content, origin=self.origin)

        # get or create the node and rdataset that will conatin the record
        node = self.find_node(name, create=True)
        rdataset = self.find_rdataset(name, rdtype, create=True)

        # add the new rdata to the set
        rdataset.add(rdata, ttl)

        return Record(self.origin, name, node, rdataset, rdata)

    def remove_record(self, hashid, cascade=True):
        """
        Remove a resource record from the zone. A `KeyError` is raised by the
        `get_record()` method if the supplied `hashid` is not found in the zone.

        If `cascade` is `True` and the`rdataset` is empty after removing the
        record, the `rdataset` is also removed. If the `node` only contains the
        empty `rdataset`, then the `node` is removed.

        :param hashid: The record's ID.
        :type hashid: string
        :param cascade: (optional) Also remove the rdataset and node if empty?
        :type cascade: bool
        """
        record = self.get_record(hashid)
        rdata = record.rdata
        rdataset = record.rdataset
        node = record.node

        rdataset.remove(rdata)

        if cascade:
            if not rdataset and len(node) == 1:
                # the node contains only an empty rdataset; remove
                self.delete_node(record.name)
            elif not rdataset:
                # the node contains other rdatasets; only remove empty set
                self.delete_rdataset(record.name, record.rdtype)

    def update_record(self, hashid, content):
        """
        Update the content of a resource record. A `KeyError` is raised by the
        `get_record()` method if the supplied `hashid` is not found in the zone.

        :param hashid: The record's ID.
        :type hashid: string
        :param content: The new content of the record.
        :type content: string
        """
        record = self.get_record(hashid)
        self.remove_record(hashid, cascade=False)
        return self.add_record(record.name, record.rdtype, content)

    @property
    def filename(self):
        return self._filename

    @property
    def ttl(self):
        return self._ttl

    @property
    def soa(self):
        """
        Return the SOA record of the zone's origin.

        :return: :class:`Record <Record>` object
        :rtype: localzone.models.Record
        """
        return self.get_records("soa")[0]

    @property
    def records(self):
        """
        Return a list of :class:`Record <Record>` objects for each resource
        record in the zone. If the zone is very large, be aware of memory
        constraints.

        :return: list of :class:`Record <Record>` objects
        :rtype: list
        """
        return self.get_records("ANY")


class Record(object):
    """
    Initialize a :class:`Record <Record>` object.

    :param origin: The record's parent domain.
    :type origin: :class:`dns.name.Name <Name>` object
    :param name: The record's name.
    :type name: :class:`dns.name.Name <Name>` object
    :param node: The record's node.
    :type node: :class:`dns.node.Node <Node>` object
    :param rdataset: The record's rdataset.
    :type rdataset: :class:`dns.rdataset.Rdataset <Rdataset>` object
    :param rdata: The record's rdata.
    :type rdata: :class:`dns.rdata.Rdata <Rdata>` object
    """

    def __init__(self, origin, name, node, rdataset, rdata):
        RecordData = namedtuple(
            "RecordData", ["hashid", "origin", "name", "node", "rdataset", "rdata"]
        )

        hashid = ""

        # Pre-initialize the record so that a hash id can be created.
        # Why not just use a dict instead? Because a tuple more clearly
        # communicates the nature of the interface and the immutability of
        # the (name, type, content) composite.
        self._data = RecordData(hashid, origin, name, node, rdataset, rdata)

        # Create the hash id and replace the tuple.
        hashid = self.__hash__()
        self._data = RecordData(hashid, origin, name, node, rdataset, rdata)

    def __repr__(self):
        s = "<DNS {rdtype} record: {name}>"
        return s.format(rdtype=self.rdtype, name=self.name)

    def __str__(self):
        return self.to_text()

    def __hash__(self):
        # TODO: convert to md5?
        return checksum(self.to_text())

    def to_text(self):
        s = "{name} {ttl} {rdclass} {rdtype} {content}"
        return s.format(
            name=self.name,
            ttl=self.ttl,
            rdclass=self.rdclass,
            rdtype=self.rdtype,
            content=self.content,
        )

    @property
    def hashid(self):
        return self._data.hashid

    @property
    def name(self):
        return self._data.name.to_text()

    @property
    def origin(self):
        return self._data.origin.to_text()

    @property
    def ttl(self):
        return self._data.rdataset.ttl

    @property
    def content(self):
        return self._data.rdata.to_text()

    @property
    def rdata(self):
        return self._data.rdata

    @property
    def rdclass(self):
        return dns.rdataclass.to_text(self._data.rdata.rdclass)

    @property
    def rdtype(self):
        return dns.rdatatype.to_text(self._data.rdata.rdtype)

    @property
    def rdataset(self):
        return self._data.rdataset

    @property
    def node(self):
        return self._data.node
