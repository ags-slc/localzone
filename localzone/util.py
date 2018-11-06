"""
localzone.util
~~~~~~~~~~~~~~

This module contains general purpose utilities used by localzone.
"""

from itertools import chain, repeat


def group(iterable, n, padvalue=None):
    """
    Create n-length sets from an iterable.

    :param iterable: An iterable object.
    :type iterable: iterable
    :param n: The number of items in the set.
    :type n: int
    :param padvalue: The value used, if necessary, to pad the last set.
    :type n: int
    :return: An iterable set.
    :rtype: iterator
    """
    return zip(*[chain(iterable, repeat(padvalue, n - 1))] * n)


def pack(tup):
    """
    Packs a tuple of 8-bit integers.

    :param tup: Tuple of 8-bit integers.
    :type tup: tuple
    :return: The packed n-bit value, where n is len(tup) * 8.
    :rtype: int
    """
    size = len(tup)
    result = 0
    for i in range(size):
        result = tup[i] << (i * 8) | result
    return result


def checksum(word, size=32):
    """
    Implements Fletcher's checksum to create 16, 32, or 64-bit checksums.

    :param word: The data to checksum.
    :type word: string
    :param size: The checksum's size.
    :type size: int
    :return: Fletcher's checksum represented as a hexadecimal digest.
    :rtype: string
    """
    if size not in [16, 32, 64]:
        raise ValueError("Valid checksum sizes are 16, 32 and 64")

    bits = int(size / 2)
    block_size = int(bits / 8)
    modulus = int(2 ** bits - 1)
    pad = 0
    ordinals = map(ord, word)

    if size == 16:
        blocks = ordinals
    else:
        blocks = map(pack, group(ordinals, block_size, pad))

    a = b = 0

    for block in blocks:
        a += block
        b += a

    a %= modulus
    b %= modulus

    return format((b << bits) | a, "x").zfill(4)
