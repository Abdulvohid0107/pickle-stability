"""Equivalent-but-not-identical: the heart of the assignment.

The brief stresses that altering the input (``2+3`` -> ``3+2``, reordering a
dict, aliasing vs copying) may yield *equivalent* objects whose pickle streams
are no longer *identical*. These tests pin down exactly where that line falls.

Some of these assert a difference on purpose: they document a real property of
pickle (a "finding"), not a bug. Where pickle *is* robust (commutative int
arithmetic) we assert identity instead.
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from pickle_stability import ALL_PROTOCOLS, sha256_pickle, is_hash_identical  # noqa: E402


# --- Cases where equivalent inputs ARE hash-identical (pickle is robust) ----

@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
def test_commutative_int_arithmetic_is_identical(protocol):
    """2+3 and 3+2 both evaluate to the int 5 before pickling -> identical."""
    assert is_hash_identical(2 + 3, 3 + 2, protocol)


@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
def test_int_set_order_is_identical(protocol):
    """Small int sets iterate by hash (== value), so order of literals is moot."""
    assert is_hash_identical({1, 2, 3}, {3, 2, 1}, protocol)


@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
def test_int_frozenset_order_is_identical(protocol):
    assert is_hash_identical(frozenset([3, 1, 2]), frozenset([1, 2, 3]), protocol)


# --- Cases where equivalent inputs are NOT identical (documented findings) --

@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
def test_dict_insertion_order_changes_bytes(protocol):
    """FINDING: dicts preserve insertion order, so reordering keys changes bytes
    even though the dicts compare equal."""
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 2, "a": 1}
    assert d1 == d2                                   # equivalent
    assert not is_hash_identical(d1, d2, protocol)    # but not identical


@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
def test_aliased_vs_copied_changes_bytes(protocol):
    """FINDING: memoization makes aliased sub-objects encode differently from
    independent equal copies."""
    shared = [1, 2, 3]
    aliased = [shared, shared]
    copied = [[1, 2, 3], [1, 2, 3]]
    assert aliased == copied                              # equivalent
    assert not is_hash_identical(aliased, copied, protocol)  # not identical


@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
def test_float_rounding_changes_bytes(protocol):
    """FINDING: 0.1+0.2 != 0.3 at the bit level, so they never hash-match."""
    assert (0.1 + 0.2) != 0.3
    assert not is_hash_identical(0.1 + 0.2, 0.3, protocol)


@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
def test_signed_zero_changes_bytes(protocol):
    """FINDING: -0.0 and 0.0 compare equal but carry a different sign bit."""
    assert 0.0 == -0.0
    assert not is_hash_identical(0.0, -0.0, protocol)


def test_default_protocol_differs_from_highest():
    """FINDING: pickle.dumps() defaults to DEFAULT_PROTOCOL, not HIGHEST.
    Omitting the protocol argument silently changes the bytes on interpreters
    whose default differs from the highest supported protocol."""
    import pickle
    if pickle.DEFAULT_PROTOCOL == pickle.HIGHEST_PROTOCOL:
        pytest.skip("default == highest on this interpreter")
    assert sha256_pickle(42) != sha256_pickle(42, pickle.HIGHEST_PROTOCOL)


def test_cross_protocol_outputs_differ():
    """FINDING: the same object yields different bytes under each protocol.
    'Same input' is only well-defined once the protocol is fixed."""
    digests = {sha256_pickle({"k": [1, 2, 3]}, p) for p in ALL_PROTOCOLS}
    assert len(digests) > 1
