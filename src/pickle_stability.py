"""Core helpers for the pickle stability and correctness test suite.

This module centralises the serialization + hashing logic used by every test.
The project's definition of "stable" is *hash-identical* output: two pickle
byte streams are considered the same only when their SHA-256 digests match.
Mere object equivalence (``a == b`` after unpickling) is necessary for
correctness but is explicitly *insufficient* for stability.
"""

from __future__ import annotations

import hashlib
import pickle
import subprocess
import sys
from typing import Any


# All protocols the running interpreter understands (0 .. HIGHEST_PROTOCOL).
ALL_PROTOCOLS = list(range(pickle.HIGHEST_PROTOCOL + 1))


def dumps(obj: Any, protocol: int | None = None) -> bytes:
    """Serialize ``obj`` to a pickle byte stream.

    Thin wrapper around :func:`pickle.dumps` kept so the whole suite has a
    single serialization entry point that can be instrumented if needed.
    """
    return pickle.dumps(obj, protocol=protocol)


def sha256_pickle(obj: Any, protocol: int | None = None) -> str:
    """Return the SHA-256 hex digest of ``pickle.dumps(obj, protocol)``."""
    return hashlib.sha256(dumps(obj, protocol)).hexdigest()


def is_hash_identical(obj_a: Any, obj_b: Any, protocol: int | None = None) -> bool:
    """True when two objects pickle to byte-for-byte identical streams."""
    return sha256_pickle(obj_a, protocol) == sha256_pickle(obj_b, protocol)


def roundtrip(obj: Any, protocol: int | None = None) -> Any:
    """Pickle then unpickle ``obj`` and return the reconstructed object."""
    return pickle.loads(dumps(obj, protocol))


def hash_in_subprocess(literal_expr: str, protocol: int = 5,
                       hashseed: str | None = None) -> str:
    """Pickle ``literal_expr`` in a *fresh* interpreter and return its digest.

    Spawning a new process is the only reliable way to exercise per-process
    state such as ``PYTHONHASHSEED`` based string hash randomization. The
    expression is evaluated inside the child, so pass a self-contained literal
    such as ``"{'a','b','c'}"``.

    Parameters
    ----------
    literal_expr:
        A Python expression producing the object to pickle.
    protocol:
        Pickle protocol to use in the child process.
    hashseed:
        Value forced into ``PYTHONHASHSEED`` for the child. ``None`` leaves the
        environment untouched (i.e. randomization stays enabled).
    """
    code = (
        "import pickle, hashlib;"
        f"obj = {literal_expr};"
        f"print(hashlib.sha256(pickle.dumps(obj, protocol={protocol})).hexdigest())"
    )
    env = None
    if hashseed is not None:
        import os
        env = dict(os.environ, PYTHONHASHSEED=hashseed)
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, env=env, check=True,
    )
    return result.stdout.strip()
