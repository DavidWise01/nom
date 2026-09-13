"""NOMCOG R004: verified checkpoint and deterministic recovery.

Requires R001, R002, and R003 in the same directory.
No network access and no file writes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
from typing import Optional

from nomcog_r001_executable_cycle import packet
from nomcog_r002_bounded_session import SESSION_CAPACITY
from nomcog_r003_audit_journal import (
    AuditEntry,
    AuditedSession,
    build_three_entry_journal,
    verify_entries,
)


@dataclass(frozen=True)
class RuntimeCheckpoint:
    entries: tuple[AuditEntry, ...]
    head_hash: str
    expected_sequence: int
    state_window: tuple[int, ...]
    receipt_count: int


def make_checkpoint(audited: AuditedSession) -> RuntimeCheckpoint:
    entries = audited.journal.entries
    if not verify_entries(entries):
        raise ValueError("cannot checkpoint an invalid audit chain")
    if len(entries) != len(audited.session.receipts):
        raise ValueError("journal and session receipt counts differ")
    return RuntimeCheckpoint(
        entries=entries,
        head_hash=audited.journal.head_hash,
        expected_sequence=audited.session.runtime.expected_sequence,
        state_window=tuple(audited.session.runtime.state_window),
        receipt_count=len(audited.session.receipts),
    )


def recover_checkpoint(
    checkpoint: RuntimeCheckpoint,
) -> Optional[AuditedSession]:
    """Return a reconstructed session only when every witness agrees."""
    if checkpoint.receipt_count != len(checkpoint.entries):
        return None
    if len(checkpoint.entries) > SESSION_CAPACITY:
        return None
    if not verify_entries(checkpoint.entries):
        return None
    if checkpoint.entries:
        if checkpoint.head_hash != checkpoint.entries[-1].entry_hash:
            return None
    if checkpoint.expected_sequence != len(checkpoint.entries) + 1:
        return None
    expected_window = tuple(entry.input_payload for entry in checkpoint.entries)
    if checkpoint.state_window != expected_window:
        return None

    recovered = AuditedSession()
    for entry in checkpoint.entries:
        result = recovered.submit(
            packet(sequence=entry.sequence, payload=entry.input_payload)
        )
        if result.status != "committed":
            return None

    if recovered.journal.entries != checkpoint.entries:
        return None
    if recovered.journal.head_hash != checkpoint.head_hash:
        return None
    if recovered.session.runtime.expected_sequence != checkpoint.expected_sequence:
        return None
    if tuple(recovered.session.runtime.state_window) != checkpoint.state_window:
        return None
    return recovered


def run_self_test() -> dict[str, object]:
    tests: dict[str, bool] = {}

    original = build_three_entry_journal()
    checkpoint = make_checkpoint(original)
    recovered = recover_checkpoint(checkpoint)
    tests["clean_checkpoint_recovers"] = (
        recovered is not None
        and recovered.journal.entries == original.journal.entries
        and recovered.journal.head_hash == original.journal.head_hash
        and recovered.session.runtime.state_window
        == original.session.runtime.state_window
    )

    continued_status = "not_run"
    if recovered is not None:
        continued = recovered.submit(packet(sequence=4, payload=40))
        continued_status = continued.status
    tests["recovered_session_continues"] = continued_status == "committed"

    damaged_entries = list(checkpoint.entries)
    damaged_entries[1] = replace(damaged_entries[1], input_payload=99)
    damaged = replace(checkpoint, entries=tuple(damaged_entries))
    tests["tampered_entry_rejected"] = recover_checkpoint(damaged) is None

    forged_head = replace(checkpoint, head_hash="0" * 64)
    tests["forged_head_rejected"] = recover_checkpoint(forged_head) is None

    wrong_sequence = replace(
        checkpoint, expected_sequence=checkpoint.expected_sequence + 1
    )
    tests["wrong_sequence_rejected"] = (
        recover_checkpoint(wrong_sequence) is None
    )

    wrong_window = replace(checkpoint, state_window=(41, 42, 99))
    tests["wrong_state_window_rejected"] = (
        recover_checkpoint(wrong_window) is None
    )

    wrong_count = replace(checkpoint, receipt_count=2)
    tests["wrong_receipt_count_rejected"] = (
        recover_checkpoint(wrong_count) is None
    )

    if not all(tests.values()):
        failed = [name for name, passed in tests.items() if not passed]
        raise AssertionError(f"R004 failed: {failed}")

    return {
        "chonk": "R004",
        "status": "PASS",
        "tests_passed": sum(tests.values()),
        "tests_total": len(tests),
        "checkpoint": {
            "entries": len(checkpoint.entries),
            "expected_sequence": checkpoint.expected_sequence,
            "state_window": list(checkpoint.state_window),
            "head_hash": checkpoint.head_hash,
        },
        "recovery": "exact",
        "continued_sequence": 4,
        "continued_status": continued_status,
        "forgeries_rejected": [
            "entry",
            "head_hash",
            "expected_sequence",
            "state_window",
            "receipt_count",
        ],
        "network": "disabled",
        "checkpoint_shape": asdict(checkpoint),
    }


if __name__ == "__main__":
    print(json.dumps(run_self_test(), indent=2, sort_keys=True))
