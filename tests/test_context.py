import pytest
import localzone
try:
    from dns.zonefile import UnknownOrigin
except ImportError:
    from dns.zone import UnknownOrigin

ZONEFILE = "tests/zonefiles/db.example.com"
ORIGIN = "example.com."
TTL = 3600


def test_load():
    z = localzone.load(ZONEFILE, ORIGIN)
    assert z.filename == ZONEFILE
    assert z.ttl == TTL
    assert len(z.records) == 16


def test_load_missing_origin():
    with pytest.raises(UnknownOrigin):
        localzone.load("tests/zonefiles/db.no-origin.com")


def test_manage():
    with localzone.manage(ZONEFILE, ORIGIN) as z:
        assert z.filename == ZONEFILE
        assert z.ttl == TTL
        assert len(z.records) == 16
