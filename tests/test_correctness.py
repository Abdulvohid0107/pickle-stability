"""Correctness tests: unpickle(pickle(x)) must reconstruct an equal object.

Strategy: **equivalence partitioning** again, but here the oracle is value
equality (``==``) of the round-tripped object, not hash identity of the bytes.
Stability is about the bytes; correctness is about the reconstructed value.
Both are required for the library to be trustworthy.

NaN is handled specially: ``nan != nan`` by IEEE-754, so we compare via the
struct bit-pattern instead.
"""

import math
import struct
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from pickle_stability import ALL_PROTOCOLS, roundtrip  # noqa: E402


ROUNDTRIP_CASES = {
    "none": None,
    "bool": True,
    "int": 123456789,
    "large_int": 2 ** 500,
    "float": 2.718281828,
    "complex": complex(3, -4),
    "str": "unicode \u00e9\u00fc \u4f60\u597d \U0001f600",
    "bytes": b"\x00\xff\x10binary",
    "bytearray": bytearray(b"abc"),
    "list": [1, [2, 3], {"k": "v"}],
    "tuple": (1, 2, (3, 4)),
    "dict": {"a": 1, "b": 2, "nested": {"c": 3}},
    "set": {1, 2, 3},
    "frozenset": frozenset([4, 5, 6]),
}


@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
@pytest.mark.parametrize("name,value", list(ROUNDTRIP_CASES.items()))
def test_roundtrip_equality(name, value, protocol):
    """Round-tripped object must equal the original."""
    assert roundtrip(value, protocol) == value, f"{name} failed round-trip"


@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
def test_nan_roundtrip_bit_identical(protocol):
    """NaN never equals itself, so compare the raw 8-byte IEEE-754 pattern."""
    nan = float("nan")
    restored = roundtrip(nan, protocol)
    assert math.isnan(restored)
    assert struct.pack("d", nan) == struct.pack("d", restored)


@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
def test_recursive_structure_roundtrip(protocol):
    """A self-referential list must round-trip into a self-referential list."""
    original = [1, 2]
    original.append(original)
    restored = roundtrip(original, protocol)
    assert restored[0] == 1
    assert restored[2] is restored  # the cycle is preserved


@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
def test_shared_reference_preserved(protocol):
    """Aliased sub-objects must remain aliased after unpickling (memoization)."""
    shared = [1, 2, 3]
    container = [shared, shared]
    restored = roundtrip(container, protocol)
    assert restored[0] is restored[1]
