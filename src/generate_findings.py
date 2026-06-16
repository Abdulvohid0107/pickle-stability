"""Generate a reproducible findings report.

Run:  python src/generate_findings.py

Writes ``results/findings.json`` and prints a human-readable summary. Every
number in the final report is produced here so the results are reproducible by
re-running this one script.
"""

from __future__ import annotations

import json
import os
import platform
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pickle_stability import (  # noqa: E402
    ALL_PROTOCOLS, sha256_pickle, is_hash_identical, hash_in_subprocess,
)

import pickle  # noqa: E402


def collect():
    findings = {}

    findings["environment"] = {
        "python_version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "highest_protocol": pickle.HIGHEST_PROTOCOL,
        "default_protocol": pickle.DEFAULT_PROTOCOL,
    }

    # F1: string set instability across processes
    runs = [hash_in_subprocess("{'apple','banana','cherry','date','egg'}") for _ in range(8)]
    findings["F1_string_set_cross_process"] = {
        "unique_digests": len(set(runs)),
        "stable": len(set(runs)) == 1,
        "sample": runs[:3],
    }

    # F1b: mitigation with fixed hashseed
    fixed = [hash_in_subprocess("{'apple','banana','cherry','date','egg'}", hashseed="0")
             for _ in range(8)]
    findings["F1b_fixed_hashseed_mitigation"] = {
        "unique_digests": len(set(fixed)),
        "stable": len(set(fixed)) == 1,
    }

    # F2: dict insertion order
    findings["F2_dict_insertion_order"] = {
        "equivalent": {"a": 1, "b": 2} == {"b": 2, "a": 1},
        "hash_identical": is_hash_identical({"a": 1, "b": 2}, {"b": 2, "a": 1}),
    }

    # F3: aliasing vs copy (memoization)
    shared = [1, 2, 3]
    findings["F3_aliasing_memoization"] = {
        "equivalent": [shared, shared] == [[1, 2, 3], [1, 2, 3]],
        "hash_identical": is_hash_identical([shared, shared], [[1, 2, 3], [1, 2, 3]]),
    }

    # F4: float rounding
    findings["F4_float_rounding"] = {
        "value_0.1+0.2": repr(0.1 + 0.2),
        "hash_identical_to_0.3": is_hash_identical(0.1 + 0.2, 0.3),
    }

    # F5: signed zero
    findings["F5_signed_zero"] = {
        "equivalent": 0.0 == -0.0,
        "hash_identical": is_hash_identical(0.0, -0.0),
    }

    # F6: default vs highest protocol
    findings["F6_default_vs_highest_protocol"] = {
        "default": pickle.DEFAULT_PROTOCOL,
        "highest": pickle.HIGHEST_PROTOCOL,
        "bytes_differ": sha256_pickle(42) != sha256_pickle(42, pickle.HIGHEST_PROTOCOL),
    }

    # F7: cross-protocol divergence
    digests = {p: sha256_pickle({"k": [1, 2, 3]}, p) for p in ALL_PROTOCOLS}
    findings["F7_cross_protocol"] = {
        "unique_digests": len(set(digests.values())),
        "num_protocols": len(ALL_PROTOCOLS),
    }

    # Controls: things that ARE stable
    findings["C1_int_set_cross_process"] = {
        "unique_digests": len({hash_in_subprocess("{1,2,3,4,5}") for _ in range(8)}),
    }
    findings["C2_repeat_dump_determinism"] = {
        "stable": all(
            sha256_pickle({"x": [1, 2, 3]}, p) == sha256_pickle({"x": [1, 2, 3]}, p)
            for p in ALL_PROTOCOLS
        ),
    }

    return findings


def main():
    findings = collect()
    out_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "findings.json")
    with open(out_path, "w") as fh:
        json.dump(findings, fh, indent=2)

    print("Pickle stability findings")
    print("=" * 50)
    for key, value in findings.items():
        print(f"\n[{key}]")
        for k, v in value.items():
            print(f"  {k}: {v}")
    print(f"\nWritten to {os.path.relpath(out_path)}")


if __name__ == "__main__":
    main()
