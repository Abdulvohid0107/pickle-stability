"""Determinism tests: does the *same* input always produce the *same* output?

Strategy: **equivalence partitioning** over Python's built-in type families.
For each representative value we assert that two independent ``dumps`` calls in
the same process yield hash-identical streams, across every supported protocol.

This is the baseline stability property. If it fails, nothing else matters.
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from pickle_stability import ALL_PROTOCOLS, sha256_pickle  # noqa: E402


# One representative per equivalence class of picklable built-in types.
REPRESENTATIVES = {
    "none": None,
    "bool_true": True,
    "bool_false": False,
    "small_int": 42,
    "negative_int": -7,
    "zero_int": 0,
    "large_int": 2 ** 1000,
    "float": 3.14159,
    "complex": complex(1, 2),
    "empty_str": "",
    "ascii_str": "hello world",
    "unicode_str": "Salom, Toshkent! \u00fc\u00e9 \u4f60\u597d",
    "bytes": b"\x00\x01\x02binary\xff",
    "bytearray": bytearray(b"mutable bytes"),
    "empty_list": [],
    "list": [1, 2, 3, "a", None],
    "nested_list": [[1, [2, [3, [4]]]]],
    "empty_tuple": (),
    "tuple": (1, "two", 3.0),
    "empty_dict": {},
    "dict": {"a": 1, "b": [2, 3], "c": {"d": 4}},
    "empty_set": set(),
    "int_set": {1, 2, 3, 4, 5},
    "frozenset": frozenset([1, 2, 3]),
}


@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
@pytest.mark.parametrize("name,value", list(REPRESENTATIVES.items()))
def test_repeat_dump_is_hash_identical(name, value, protocol):
    """Same object pickled twice in one process must be byte-identical."""
    first = sha256_pickle(value, protocol)
    second = sha256_pickle(value, protocol)
    assert first == second, (
        f"{name} produced non-deterministic output on protocol {protocol}"
    )


@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
def test_recursive_list_is_deterministic(protocol):
    """Self-referential containers must pickle deterministically."""
    a = [1, 2, 3]
    a.append(a)
    b = [1, 2, 3]
    b.append(b)
    assert sha256_pickle(a, protocol) == sha256_pickle(b, protocol)


@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
def test_recursive_dict_is_deterministic(protocol):
    """Self-referential dict must pickle deterministically."""
    a = {"k": 1}
    a["self"] = a
    b = {"k": 1}
    b["self"] = b
    assert sha256_pickle(a, protocol) == sha256_pickle(b, protocol)
