import pytest
from localzone.util import checksum

# Test vectors
WORD = "abcde"
CS16 = "c8f0"
CS32 = "f04fc729"
CS64 = "c8c6c527646362c6"


def test_checksum_16():
    cs = checksum(WORD, 16)
    assert cs == CS16


def test_checksum_32():
    cs = checksum(WORD)
    assert cs == CS32


def test_checksum_64():
    cs = checksum(WORD, 64)
    assert cs == CS64


def test_checksum_invalid_size():
    with pytest.raises(ValueError):
        cs = checksum(WORD, 128)
