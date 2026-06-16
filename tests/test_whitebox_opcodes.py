"""White-box testing driven by pickle's opcode stream.

The pickle module's wire format is documented and ``pickletools.genops`` lets us
walk the opcodes a stream is built from. Instead of treating ``dumps`` as a
black box, here we assert facts about *which opcodes* appear, exercising
specific code paths in the C/Python pickler (an all-uses-style approach: we
target the definitions of individual opcode-emitting branches).

These tests make the structural coverage concrete and let the traceability
matrix point at code paths rather than just behaviours.
"""

import pickle
import pickletools
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from pickle_stability import dumps  # noqa: E402


def opcode_names(obj, protocol):
    return [op.name for op, _, _ in pickletools.genops(dumps(obj, protocol))]


def test_memo_opcodes_emitted_for_shared_refs():
    """Aliased objects must trigger memo PUT/GET opcodes (the path that makes
    aliased vs copied streams differ)."""
    shared = [1, 2, 3]
    ops = opcode_names([shared, shared], 4)
    assert any(name in ("BINGET", "LONG_BINGET", "GET") for name in ops), (
        "expected a memo GET opcode for the second reference to the shared list"
    )


def test_no_memo_get_for_distinct_copies():
    """Independent equal copies should NOT share a memo entry."""
    ops = opcode_names([[1, 2, 3], [1, 2, 3]], 4)
    assert not any(name in ("BINGET", "LONG_BINGET", "GET") for name in ops)


@pytest.mark.parametrize("value,expected", [
    (0, "BININT1"),
    (255, "BININT1"),
    (256, "BININT2"),
    (65536, "BININT"),
])
def test_int_opcode_selection(value, expected):
    """Integer width boundaries select different opcodes (protocol 2)."""
    ops = opcode_names(value, 2)
    assert expected in ops, f"{value} -> {ops}, expected {expected}"


def test_protocol_header_present_from_protocol_2():
    """Protocols >= 2 must emit a PROTO opcode as the first instruction."""
    ops = opcode_names({"a": 1}, 2)
    assert ops[0] == "PROTO"


def test_framing_opcode_present_from_protocol_4():
    """Protocol 4 introduces FRAME opcodes for large payloads."""
    big = list(range(5000))
    ops = opcode_names(big, 4)
    assert "FRAME" in ops


def test_stop_opcode_terminates_stream():
    """Every well-formed stream ends with STOP."""
    for proto in range(pickle.HIGHEST_PROTOCOL + 1):
        ops = opcode_names({"k": "v"}, proto)
        assert ops[-1] == "STOP"
