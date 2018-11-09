from dns.rdatatype import UnknownRdatatype
import pytest
import localzone

ZONEFILE = "tests/zonefiles/db.example.com"
ORIGIN = "example.com."
HASHID = "dd03d449"

#
# readers
#


def test_get_all_records():
    z = localzone.load(ZONEFILE, ORIGIN)
    records = z.get_records("ANY")
    assert len(records) == 16


def test_get_record():
    z = localzone.load(ZONEFILE, ORIGIN)
    record = z.get_record(HASHID)
    assert record.name == "@"
    assert record.rdtype == "A"
    assert record.content == "192.0.2.1"
    assert record.ttl == 3600


def test_get_record_not_found():
    z = localzone.load(ZONEFILE, ORIGIN)
    with pytest.raises(KeyError):
        z.get_record("deadbeef")


def test_find_records_by_type():
    z = localzone.load(ZONEFILE, ORIGIN)
    records = z.find_record("MX")
    assert len(records) == 3


def test_find_record_by_name():
    z = localzone.load(ZONEFILE, ORIGIN)
    records = z.find_record("CNAME", "www")
    assert len(records) == 1
    assert records[0].content == "@"


def test_find_record_by_content():
    z = localzone.load(ZONEFILE, ORIGIN)
    records = z.find_record("A", content="192.0.2.2")
    assert len(records) == 1
    assert records[0].name == "ns"


def test_zone_records_property():
    z = localzone.load(ZONEFILE, ORIGIN)
    records = z.records
    assert len(records) == 16


#
# writers
#


def test_zone_add_record():
    with localzone.manage(ZONEFILE, ORIGIN) as z:
        record = z.add_record("test", "txt", "testing")
        assert record.hashid == "28c9e108"


def test_zone_add_record_unknown_type():
    with localzone.manage(ZONEFILE, ORIGIN) as z:
        with pytest.raises(UnknownRdatatype):
            z.add_record("test", "err", "testing")


def test_zone_add_record_no_content():
    with localzone.manage(ZONEFILE, ORIGIN) as z:
        with pytest.raises(AttributeError):
            z.add_record("test", "txt", None)


def test_zone_remove_record():
    with localzone.manage(ZONEFILE, ORIGIN) as z:
        z.remove_record(HASHID)
        with pytest.raises(KeyError):
            z.get_record(HASHID)


def test_zone_remove_record_not_found():
    with localzone.manage(ZONEFILE, ORIGIN) as z:
        with pytest.raises(KeyError):
            z.remove_record("deadbeef")


def test_zone_update_record():
    with localzone.manage(ZONEFILE, ORIGIN) as z:
        record = z.update_record(HASHID, "192.0.2.100")
        assert record.hashid == "117e047a"
        assert record.name == "@"
        assert record.rdtype == "A"
        assert record.content == "192.0.2.100"
        assert record.ttl == 3600


def test_zone_update_record_not_found():
    with localzone.manage(ZONEFILE, ORIGIN) as z:
        with pytest.raises(KeyError):
            z.update_record("deadbeef", "eat mor chikin")


def test_zone_save():
    savefile = "tests/db.example.com.saved"
    z = localzone.load(ZONEFILE, ORIGIN)
    serial = z.soa.rdata.serial
    record = z.update_record(HASHID, "192.0.2.100")
    z.save(savefile)
    z = localzone.load(savefile, ORIGIN)
    record = z.find_record("A", content="192.0.2.100")[0]
    assert z.soa.rdata.serial > serial
    assert record.name == "@"
    assert record.rdtype == "A"
    assert record.content == "192.0.2.100"
    assert record.ttl == 3600
