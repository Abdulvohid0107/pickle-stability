# Traceability Matrix

Maps each tested property and testing technique to the test that covers it and
the finding (if any) it produced. This demonstrates the completeness of the
suite, as required by the test-plan lecture.

## Technique → Test file

| Testing technique | Test file | What it covers |
|-------------------|-----------|----------------|
| Equivalence partitioning | `test_determinism.py` | Repeat-dump stability per type family |
| Equivalence partitioning | `test_correctness.py` | Round-trip equality per type family |
| Boundary value analysis | `test_boundary.py` | Int / length opcode-width edges |
| Equivalent-not-identical | `test_equivalent_not_identical.py` | Input changes that keep equivalence |
| Cross-process / config | `test_cross_process.py` | `PYTHONHASHSEED` randomization |
| Fuzzing | `test_fuzzing.py` | Seeded random differential testing |
| White-box (structural) | `test_whitebox_opcodes.py` | Emitted opcode assertions |

## Property → Test → Finding

| # | Property under test | Technique | Test(s) | Result |
|---|---------------------|-----------|---------|--------|
| P1 | Same object, repeated dump, same bytes | EP | `test_repeat_dump_is_hash_identical` | PASS (stable) |
| P2 | Recursive/self-referential containers are deterministic | EP | `test_recursive_list_is_deterministic`, `test_recursive_dict_is_deterministic` | PASS |
| P3 | Round-trip preserves value | EP | `test_roundtrip_equality` | PASS |
| P4 | NaN round-trips bit-identically | EP | `test_nan_roundtrip_bit_identical` | PASS |
| P5 | Aliasing preserved on unpickle | EP | `test_shared_reference_preserved` | PASS |
| P6 | Int opcode boundaries deterministic | BVA | `test_int_boundary_determinism` | PASS |
| P7 | Collection length boundaries deterministic | BVA | `test_string/bytes/list_length_boundary` | PASS |
| P8 | Special floats deterministic | BVA | `test_float_special_boundaries` | PASS |
| F1 | String set unstable across processes | Config | `test_string_set_unstable_across_processes` | **FINDING** |
| F1b | Fixed `PYTHONHASHSEED` restores stability | Config | `test_fixing_hashseed_restores_stability` | PASS (mitigation) |
| F2 | Dict insertion order changes bytes | Equiv-not-id | `test_dict_insertion_order_changes_bytes` | **FINDING** |
| F3 | Aliased vs copied changes bytes | Equiv-not-id | `test_aliased_vs_copied_changes_bytes` | **FINDING** |
| F4 | Float rounding changes bytes | Equiv-not-id | `test_float_rounding_changes_bytes` | **FINDING** |
| F5 | Signed zero changes bytes | Equiv-not-id | `test_signed_zero_changes_bytes` | **FINDING** |
| F6 | Default protocol ≠ highest | Equiv-not-id | `test_default_protocol_differs_from_highest` | **FINDING** |
| F7 | Cross-protocol bytes differ | Equiv-not-id | `test_cross_protocol_outputs_differ` | **FINDING** |
| C1 | Int set stable across processes (control) | Config | `test_int_set_stable_across_processes` | PASS |
| C2 | String-keyed dict stable across processes (control) | Config | `test_string_keyed_dict_stable_across_processes` | PASS |
| P9 | Commutative int arithmetic identical | Equiv-not-id | `test_commutative_int_arithmetic_is_identical` | PASS |
| P10 | Int set/frozenset order irrelevant | Equiv-not-id | `test_int_set_order_is_identical`, `test_int_frozenset_order_is_identical` | PASS |
| P11 | Fuzzed objects deterministic | Fuzzing | `test_fuzz_determinism` | PASS |
| P12 | Fuzzed objects round-trip | Fuzzing | `test_fuzz_roundtrip` | PASS |
| W1 | Memo opcodes emitted for shared refs | White-box | `test_memo_opcodes_emitted_for_shared_refs` | PASS |
| W2 | No memo GET for distinct copies | White-box | `test_no_memo_get_for_distinct_copies` | PASS |
| W3 | Int opcode selection by width | White-box | `test_int_opcode_selection` | PASS |
| W4 | PROTO header from protocol 2 | White-box | `test_protocol_header_present_from_protocol_2` | PASS |
| W5 | FRAME from protocol 4 | White-box | `test_framing_opcode_present_from_protocol_4` | PASS |
| W6 | STOP terminates every stream | White-box | `test_stop_opcode_terminates_stream` | PASS |
