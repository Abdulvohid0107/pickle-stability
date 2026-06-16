"""Boundary value analysis for pickle stability.

Pickle's opcodes switch on the *size* of a value: small ints use BININT1,
larger ones BININT2 / BININT4, and so on. Strings, bytes and collections have
1-byte vs 4-byte vs 8-byte length encodings. These width transitions are
natural boundaries, so we test values immediately around them and confirm each
is still deterministic.
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from pickle_stability import ALL_PROTOCOLS, sha256_pickle  # noqa: E402


# Integer opcode boundaries (unsigned 1/2/4-byte and signed 4-byte edges).
INT_BOUNDARIES = [
    0, 255, 256,                 # BININT1 -> BININT2
    65535, 65536,                # BININT2 -> BININT4
    2 ** 31 - 1, 2 ** 31,        # BININT4 -> LONG
    -1, -256, -(2 ** 31), -(2 ** 31) - 1,
    2 ** 63 - 1, 2 ** 63,        # machine-word edge
]

# Collection length boundaries (1-byte length -> 4-byte length at 256).
LENGTH_BOUNDARIES = [0, 1, 255, 256, 257, 1000]


@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
@pytest.mark.parametrize("value", INT_BOUNDARIES)
def test_int_boundary_determinism(value, protocol):
    assert sha256_pickle(value, protocol) == sha256_pickle(value, protocol)


@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
@pytest.mark.parametrize("length", LENGTH_BOUNDARIES)
def test_string_length_boundary(length, protocol):
    s = "x" * length
    assert sha256_pickle(s, protocol) == sha256_pickle(s, protocol)


@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
@pytest.mark.parametrize("length", LENGTH_BOUNDARIES)
def test_bytes_length_boundary(length, protocol):
    b = b"y" * length
    assert sha256_pickle(b, protocol) == sha256_pickle(b, protocol)


@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
@pytest.mark.parametrize("length", LENGTH_BOUNDARIES)
def test_list_length_boundary(length, protocol):
    lst = list(range(length))
    assert sha256_pickle(lst, protocol) == sha256_pickle(lst, protocol)


@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
def test_float_special_boundaries(protocol):
    """Special floats must each be self-consistent within a process."""
    for value in [0.0, -0.0, float("inf"), float("-inf"),
                  sys.float_info.max, sys.float_info.min]:
        assert sha256_pickle(value, protocol) == sha256_pickle(value, protocol)
