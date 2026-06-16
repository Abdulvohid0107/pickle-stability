# Pickle Stability & Correctness Test Suite

A test suite that investigates one question:

> **Does the same input always produce the same (hash-identical) pickle output?**

We treat two pickle streams as "the same" only when their **SHA-256 digests
match**. Object equivalence (`a == b` after unpickling) is necessary for
correctness but is *not* sufficient for stability.

*Software Engineering Testing course — LAB project.*

---

## TL;DR findings

Pickle is **deterministic within a single process** but **not unconditionally
stable**. The same logical input can produce different bytes when:

| ID | Cause | Equivalent? | Hash-identical? |
|----|-------|-------------|-----------------|
| F1 | String `set`/`frozenset` across processes (`PYTHONHASHSEED`) | yes | **no** |
| F2 | `dict` key insertion order | yes | **no** |
| F3 | Aliased vs copied sub-objects (memoization) | yes | **no** |
| F4 | Float rounding (`0.1 + 0.2` vs `0.3`) | no | **no** |
| F5 | Signed zero (`0.0` vs `-0.0`) | yes | **no** |
| F6 | Default vs highest protocol when `protocol` omitted | n/a | **no** |
| F7 | Different protocol versions | n/a | **no** |

F1 is the most consequential: it is non-deterministic *between runs* unless
`PYTHONHASHSEED` is fixed. Everything else is deterministic once the input,
protocol and process are pinned.

---

## Quick start

```bash
pip install -r requirements.txt
pytest                      # run the 520-case suite
python src/generate_findings.py   # reproduce results/findings.json
```

## Layout

```
src/
  pickle_stability.py     # serialize + SHA-256 helpers (single source of truth)
  generate_findings.py    # reproducible findings -> results/findings.json
tests/
  test_determinism.py             # equivalence partitioning: repeat-dump stability
  test_correctness.py             # round-trip value equality
  test_boundary.py                # boundary value analysis (opcode width edges)
  test_equivalent_not_identical.py# equivalent-but-not-identical findings
  test_cross_process.py           # PYTHONHASHSEED instability (subprocess)
  test_fuzzing.py                 # seeded random differential testing
  test_whitebox_opcodes.py        # opcode-level (pickletools) structural tests
docs/
  traceability_matrix.md  # technique x property x test mapping
results/
  findings.json           # generated evidence
```

## Testing techniques used

- **Equivalence partitioning** — one representative per built-in type family.
- **Boundary value analysis** — values straddling pickle's 1/2/4/8-byte opcode
  width transitions.
- **Fuzzing** — seeded recursive object generator, differential checks.
- **White-box / structural** — `pickletools.genops` assertions on emitted
  opcodes (memo GET/PUT, PROTO, FRAME, STOP) — an all-uses-style approach.

## Reproducibility

All randomness is seeded (`FUZZ_SEED = 20250616`). Cross-process tests spawn
fresh interpreters so `PYTHONHASHSEED` actually varies. Re-running
`generate_findings.py` regenerates every number cited in the report.

Tested on CPython 3.12, pickle protocols 0–5.
