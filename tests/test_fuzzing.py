"""Fuzzing: randomized differential testing of stability and correctness.

A recursive random-object generator builds deeply nested structures of mixed
types. For each generated object we check two properties:

1. **Determinism** - pickling the same object twice in-process is identical.
2. **Round-trip** - unpickling reproduces an equal object.

The generator is seeded for reproducibility (the brief requires reproducible
findings). Strings are deliberately kept out of *sets* in the fuzzer so that the
known hash-seed instability (covered in test_cross_process) does not mask other
defects; string keys in dicts are fine because dicts keep insertion order.
"""

import random
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from pickle_stability import ALL_PROTOCOLS, sha256_pickle, roundtrip  # noqa: E402


FUZZ_SEED = 20250616
FUZZ_ITERATIONS = 200


def _rand_atom(rng):
    kind = rng.choice(["int", "float", "str", "bytes", "bool", "none"])
    if kind == "int":
        return rng.randint(-(2 ** 40), 2 ** 40)
    if kind == "float":
        return rng.uniform(-1e6, 1e6)
    if kind == "str":
        return "".join(rng.choice("abcXYZ \u00e9\u4f60") for _ in range(rng.randint(0, 12)))
    if kind == "bytes":
        return bytes(rng.randint(0, 255) for _ in range(rng.randint(0, 8)))
    if kind == "bool":
        return rng.choice([True, False])
    return None


def _rand_object(rng, depth=0):
    if depth >= 4 or rng.random() < 0.45:
        return _rand_atom(rng)
    kind = rng.choice(["list", "tuple", "dict", "set"])
    n = rng.randint(0, 5)
    if kind == "list":
        return [_rand_object(rng, depth + 1) for _ in range(n)]
    if kind == "tuple":
        return tuple(_rand_object(rng, depth + 1) for _ in range(n))
    if kind == "dict":
        return {f"k{i}": _rand_object(rng, depth + 1) for i in range(n)}
    # set: only hashable, non-string atoms to avoid hash-seed order effects
    return {rng.randint(-1000, 1000) for _ in range(n)}


def _fuzz_corpus():
    rng = random.Random(FUZZ_SEED)
    return [_rand_object(rng) for _ in range(FUZZ_ITERATIONS)]


CORPUS = _fuzz_corpus()


@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
def test_fuzz_determinism(protocol):
    """Every fuzzed object must pickle deterministically in-process."""
    for i, obj in enumerate(CORPUS):
        assert sha256_pickle(obj, protocol) == sha256_pickle(obj, protocol), (
            f"non-deterministic fuzz object #{i} on protocol {protocol}"
        )


@pytest.mark.parametrize("protocol", ALL_PROTOCOLS)
def test_fuzz_roundtrip(protocol):
    """Every fuzzed object must survive a pickle round-trip unchanged."""
    for i, obj in enumerate(CORPUS):
        assert roundtrip(obj, protocol) == obj, (
            f"round-trip mismatch on fuzz object #{i}, protocol {protocol}"
        )
