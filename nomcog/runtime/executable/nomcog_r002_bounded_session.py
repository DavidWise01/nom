"""NOMCOG R002: bounded transactional session around the frozen R001 cycle.

Requires nomcog_r001_executable_cycle.py in the same directory.
Uses no network and writes no files.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from typing import Optional

from nomcog_r001_executable_cycle import (
    CycleResult,
    InputPacket,
    PosiRuntime,
    packet,
)


SESSION_CAPACITY = 8


@dataclass(frozen=True)
class SessionReceipt:
    ordinal: int
    sequence: int
    input_payload: int
    output_payload: int
    proposal: str


@dataclass(frozen=True)
class SessionResult:
    status: str
    reason: str
    cycle: Optional[CycleResult] = None
    receipt: Optional[SessionReceipt] = None


@dataclass(frozen=True)
class RuntimeSnapshot:
    expected_sequence: int
    seen_fingerprints: frozenset[tuple[int, int, int, int, int]]
    state_window: tuple[int, ...]
    active: bool


@dataclass
class BoundedSession:
    runtime: PosiRuntime = field(default_factory=PosiRuntime)
    receipts: list[SessionReceipt] = field(default_factory=list)
    capacity: int = SESSION_CAPACITY

    def snapshot(self) -> RuntimeSnapshot:
        return RuntimeSnapshot(
            expected_sequence=self.runtime.expected_sequence,
            seen_fingerprints=frozenset(self.runtime.seen_fingerprints),
            state_window=tuple(self.runtime.state_window),
            active=self.runtime.active,
        )

    def restore(self, snapshot: RuntimeSnapshot) -> None:
        self.runtime.expected_sequence = snapshot.expected_sequence
        self.runtime.seen_fingerprints = set(snapshot.seen_fingerprints)
        self.runtime.state_window[:] = snapshot.state_window
        self.runtime.active = snapshot.active

    def submit(
        self,
        input_packet: InputPacket,
        *,
        left_sentinel: bool = True,
        right_sentinel: bool = True,
    ) -> SessionResult:
        """Submit one packet; rejected cycles leave all session state untouched."""
        if len(self.receipts) >= self.capacity:
            return SessionResult(status="halted", reason="session_capacity")

        before = self.snapshot()
        receipt_count = len(self.receipts)
        result = self.runtime.run_cycle(
            input_packet,
            left_sentinel=left_sentinel,
            right_sentinel=right_sentinel,
        )

        if result.status != "emitted" or result.output is None:
            self.restore(before)
            assert len(self.receipts) == receipt_count
            return SessionResult(
                status="halted",
                reason=result.reason,
                cycle=result,
            )

        receipt = SessionReceipt(
            ordinal=receipt_count + 1,
            sequence=input_packet.sequence,
            input_payload=input_packet.payload,
            output_payload=result.output.payload,
            proposal=result.proposal or "hold",
        )
        self.receipts.append(receipt)
        return SessionResult(
            status="committed",
            reason="cycle_committed",
            cycle=result,
            receipt=receipt,
        )


def session_packet(sequence: int, payload: int = 41) -> InputPacket:
    return packet(sequence=sequence, payload=payload)


def run_self_test() -> dict[str, object]:
    tests: dict[str, bool] = {}

    session = BoundedSession()
    committed = [
        session.submit(session_packet(sequence))
        for sequence in range(1, SESSION_CAPACITY + 1)
    ]
    tests["eight_ordered_cycles"] = (
        all(result.status == "committed" for result in committed)
        and len(session.receipts) == SESSION_CAPACITY
        and session.runtime.expected_sequence == SESSION_CAPACITY + 1
        and len(session.runtime.state_window) == SESSION_CAPACITY
    )

    before_ninth = session.snapshot()
    ninth = session.submit(session_packet(SESSION_CAPACITY + 1))
    tests["ninth_cycle_rejected"] = (
        ninth.reason == "session_capacity"
        and session.snapshot() == before_ninth
        and len(session.receipts) == SESSION_CAPACITY
    )

    checksum_session = BoundedSession()
    before_checksum = checksum_session.snapshot()
    bad_checksum = checksum_session.submit(packet(checksum=0))
    tests["checksum_rejection_is_atomic"] = (
        bad_checksum.reason == "integrity_checksum"
        and checksum_session.snapshot() == before_checksum
        and checksum_session.receipts == []
    )

    quorum_session = BoundedSession()
    before_quorum = quorum_session.snapshot()
    denied = quorum_session.submit(packet(), right_sentinel=False)
    tests["quorum_rejection_is_atomic"] = (
        denied.reason == "dual_sentinel_quorum"
        and quorum_session.snapshot() == before_quorum
        and quorum_session.receipts == []
    )
    retry = quorum_session.submit(packet())
    tests["denied_packet_can_retry"] = (
        retry.status == "committed"
        and len(quorum_session.receipts) == 1
        and quorum_session.runtime.expected_sequence == 2
    )

    sequence_session = BoundedSession()
    before_sequence = sequence_session.snapshot()
    skipped = sequence_session.submit(session_packet(2))
    tests["sequence_rejection_is_atomic"] = (
        skipped.reason == "sequence_alignment"
        and sequence_session.snapshot() == before_sequence
        and sequence_session.receipts == []
    )

    if not all(tests.values()):
        failed = [name for name, passed in tests.items() if not passed]
        raise AssertionError(f"R002 failed: {failed}")

    return {
        "chonk": "R002",
        "status": "PASS",
        "tests_passed": sum(tests.values()),
        "tests_total": len(tests),
        "capacity": session.capacity,
        "committed_sequences": [receipt.sequence for receipt in session.receipts],
        "ninth_cycle": ninth.reason,
        "transactional_rejections": [
            bad_checksum.reason,
            denied.reason,
            skipped.reason,
        ],
        "retry_after_denial": retry.status,
        "final_state": {
            "expected_sequence": session.runtime.expected_sequence,
            "window_size": len(session.runtime.state_window),
            "active": session.runtime.active,
        },
        "network": "disabled",
        "sample_receipt": asdict(session.receipts[0]),
    }


if __name__ == "__main__":
    print(json.dumps(run_self_test(), indent=2, sort_keys=True))
