"""Cross-process / environment stability tests.

The headline finding of the project lives here. String hashing in CPython is
randomized per process via ``PYTHONHASHSEED`` (PEP 456 / SipHash). Because a
``set`` or ``frozenset`` of strings is pickled in *iteration order*, and that
order depends on the per-process hash seed, **the same string set pickles to a
different byte stream in different interpreter runs**.

This violates the project's stability definition (hash-identical output under
all circumstances) and is only suppressed by fixing ``PYTHONHASHSEED``.

Each test spawns fresh interpreters via :func:`hash_in_subprocess` so the seed
actually varies between runs.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from pickle_stability import hash_in_subprocess  # noqa: E402


STRING_SET = "{'apple','banana','cherry','date','egg','fig','grape'}"
STRING_FROZENSET = "frozenset({'apple','banana','cherry','date','egg','fig'})"
STRING_KEY_DICT = "dict.fromkeys(['apple','banana','cherry','date','egg'])"
INT_SET = "{1,2,3,4,5,6,7,8,9,10}"


def _unique_digests(expr, runs=6, hashseed=None):
    return {hash_in_subprocess(expr, hashseed=hashseed) for _ in range(runs)}


def test_string_set_unstable_across_processes():
    """FINDING: a string set is NOT hash-identical across interpreter runs."""
    digests = _unique_digests(STRING_SET)
    assert len(digests) > 1, (
        "expected hash-seed randomization to perturb string-set pickle output"
    )


def test_string_frozenset_unstable_across_processes():
    """FINDING: frozensets of strings share the same instability."""
    digests = _unique_digests(STRING_FROZENSET)
    assert len(digests) > 1


def test_fixing_hashseed_restores_stability():
    """MITIGATION: pinning PYTHONHASHSEED=0 makes the output reproducible."""
    digests = _unique_digests(STRING_SET, hashseed="0")
    assert len(digests) == 1


def test_int_set_stable_across_processes():
    """CONTROL: int sets are stable because small-int hashes are not randomized.
    This isolates string hashing as the cause."""
    digests = _unique_digests(INT_SET)
    assert len(digests) == 1


def test_string_keyed_dict_stable_across_processes():
    """CONTROL: dicts keep insertion order (not hash order), so a string-keyed
    dict stays stable across processes even though a string set does not."""
    digests = _unique_digests(STRING_KEY_DICT)
    assert len(digests) == 1
