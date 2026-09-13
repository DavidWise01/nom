"""NOMCOG R003: append-only hash-linked audit journal.

Requires R001 and R002 in the same directory. No network or file writes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json

from nomcog_r001_executable_cycle import InputPacket, packet
from nomcog_r002_bounded_session import BoundedSession, SessionResult


GENESIS_HASH = hashlib.sha256(b"NOMCOG:R003:GENESIS").hexdigest()


@dataclass(frozen=True)
class AuditEntry:
    index: int
    sequence: int
    input_payload: int
    output_payload: int
    proposal: str
    previous_hash: str
    entry_hash: str


def entry_digest(
    index: int,
    sequence: int,
    input_payload: int,
    output_payload: int,
    proposal: str,
    previous_hash: str,
) -> str:
    canonical = json.dumps(
        {
            "index": index,
            "input_payload": input_payload,
            "output_payload": output_payload,
            "previous_hash": previous_hash,
            "proposal": proposal,
            "sequence": sequence,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


class AuditJournal:
    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    @property
    def entries(self) -> tuple[AuditEntry, ...]:
        return tuple(self._entries)

    @property
    def head_hash(self) -> str:
        return self._entries[-1].entry_hash if self._entries else GENESIS_HASH

    def append_committed(self, result: SessionResult) -> AuditEntry:
        if result.status != "committed" or result.receipt is None:
            raise ValueError("only committed cycles may enter the journal")

        receipt = result.receipt
        index = len(self._entries) + 1
        previous_hash = self.head_hash
        digest = entry_digest(
            index,
            receipt.sequence,
            receipt.input_payload,
            receipt.output_payload,
            receipt.proposal,
            previous_hash,
        )
        entry = AuditEntry(
            index=index,
            sequence=receipt.sequence,
            input_payload=receipt.input_payload,
            output_payload=receipt.output_payload,
            proposal=receipt.proposal,
            previous_hash=previous_hash,
            entry_hash=digest,
        )
        self._entries.append(entry)
        return entry


def verify_entries(entries: tuple[AuditEntry, ...]) -> bool:
    previous_hash = GENESIS_HASH
    previous_sequence = 0
    for expected_index, entry in enumerate(entries, start=1):
        if entry.index != expected_index:
            return False
        if entry.sequence != previous_sequence + 1:
            return False
        if entry.previous_hash != previous_hash:
            return False
        expected_hash = entry_digest(
            entry.index,
            entry.sequence,
            entry.input_payload,
            entry.output_payload,
            entry.proposal,
            entry.previous_hash,
        )
        if entry.entry_hash != expected_hash:
            return False
        previous_hash = entry.entry_hash
        previous_sequence = entry.sequence
    return True


class AuditedSession:
    def __init__(self) -> None:
        self.session = BoundedSession()
        self.journal = AuditJournal()

    def submit(
        self,
        input_packet: InputPacket,
        *,
        left_sentinel: bool = True,
        right_sentinel: bool = True,
    ) -> SessionResult:
        result = self.session.submit(
            input_packet,
            left_sentinel=left_sentinel,
            right_sentinel=right_sentinel,
        )
        if result.status == "committed":
            self.journal.append_committed(result)
        return result


def build_three_entry_journal() -> AuditedSession:
    audited = AuditedSession()
    for sequence, payload_value in ((1, 41), (2, 42), (3, 43)):
        result = audited.submit(packet(sequence=sequence, payload=payload_value))
        if result.status != "committed":
            raise AssertionError("fixture cycle did not commit")
    return audited


def run_self_test() -> dict[str, object]:
    tests: dict[str, bool] = {}

    audited = build_three_entry_journal()
    clean_entries = audited.journal.entries
    tests["clean_chain_verifies"] = (
        len(clean_entries) == 3 and verify_entries(clean_entries)
    )

    count_before = len(audited.journal.entries)
    rejected = audited.submit(packet(sequence=4, checksum=0))
    tests["rejection_not_recorded"] = (
        rejected.status == "halted"
        and len(audited.journal.entries) == count_before
        and verify_entries(audited.journal.entries)
    )

    tampered_payload = list(clean_entries)
    tampered_payload[1] = replace(
        tampered_payload[1], output_payload=99
    )
    tests["payload_tamper_detected"] = not verify_entries(
        tuple(tampered_payload)
    )

    broken_link = list(clean_entries)
    broken_link[2] = replace(broken_link[2], previous_hash=GENESIS_HASH)
    tests["broken_link_detected"] = not verify_entries(tuple(broken_link))

    missing_entry = (clean_entries[0], clean_entries[2])
    tests["missing_entry_detected"] = not verify_entries(missing_entry)

    replayed = build_three_entry_journal()
    tests["deterministic_head"] = (
        replayed.journal.head_hash == audited.journal.head_hash
        and replayed.journal.entries == clean_entries
    )

    empty = AuditJournal()
    tests["empty_chain_has_genesis"] = (
        verify_entries(empty.entries) and empty.head_hash == GENESIS_HASH
    )

    if not all(tests.values()):
        failed = [name for name, passed in tests.items() if not passed]
        raise AssertionError(f"R003 failed: {failed}")

    return {
        "chonk": "R003",
        "status": "PASS",
        "tests_passed": sum(tests.values()),
        "tests_total": len(tests),
        "entries": len(clean_entries),
        "sequences": [entry.sequence for entry in clean_entries],
        "chain_verified": verify_entries(clean_entries),
        "rejection_recorded": False,
        "tamper_detected": True,
        "head_hash": audited.journal.head_hash,
        "network": "disabled",
        "last_entry": asdict(clean_entries[-1]),
    }


if __name__ == "__main__":
    print(json.dumps(run_self_test(), indent=2, sort_keys=True))
