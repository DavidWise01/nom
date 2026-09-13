"""NOMCOG R006: governed local control boundary.

Requires R001 through R005 in the same directory. The control boundary has no
socket listener. Its storage target is fixed at construction and cannot be
selected by a command.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import tempfile
from typing import Optional

from nomcog_r001_executable_cycle import (
    IDENTITY_ANCHOR,
    PROVENANCE_ANCHOR,
    packet,
)
from nomcog_r003_audit_journal import AuditedSession
from nomcog_r004_checkpoint_recovery import make_checkpoint
from nomcog_r005_atomic_checkpoint_store import (
    load_checkpoint,
    save_checkpoint_atomic,
)


ALLOWED_COMMANDS = frozenset({"status", "submit", "checkpoint", "recover"})


@dataclass(frozen=True)
class ControlRequest:
    identity_anchor: int
    provenance_anchor: int
    command: str
    packet_sequence: Optional[int] = None
    payload: Optional[int] = None
    left_sentinel: bool = True
    right_sentinel: bool = True


@dataclass(frozen=True)
class ControlResponse:
    status: str
    command: str
    reason: str
    next_sequence: int
    receipt_count: int
    output_payload: Optional[int] = None


class LocalControlBoundary:
    def __init__(self, checkpoint_path: Path) -> None:
        self._checkpoint_path = Path(checkpoint_path)
        self._audited = AuditedSession()

    @property
    def audited(self) -> AuditedSession:
        return self._audited

    def _response(
        self,
        status: str,
        command: str,
        reason: str,
        output_payload: Optional[int] = None,
    ) -> ControlResponse:
        return ControlResponse(
            status=status,
            command=command,
            reason=reason,
            next_sequence=self._audited.session.runtime.expected_sequence,
            receipt_count=len(self._audited.journal.entries),
            output_payload=output_payload,
        )

    def handle(self, request: ControlRequest) -> ControlResponse:
        if request.identity_anchor != IDENTITY_ANCHOR:
            return self._response("halted", request.command, "identity_anchor")
        if request.provenance_anchor != PROVENANCE_ANCHOR:
            return self._response("halted", request.command, "provenance_anchor")
        if not (request.left_sentinel and request.right_sentinel):
            return self._response(
                "halted", request.command, "dual_sentinel_quorum"
            )
        if request.command not in ALLOWED_COMMANDS:
            return self._response("halted", request.command, "command_denied")

        if request.command == "status":
            return self._response("ok", request.command, "ready")

        if request.command == "submit":
            if request.packet_sequence is None or request.payload is None:
                return self._response(
                    "halted", request.command, "missing_packet_fields"
                )
            result = self._audited.submit(
                packet(sequence=request.packet_sequence, payload=request.payload),
                left_sentinel=request.left_sentinel,
                right_sentinel=request.right_sentinel,
            )
            if result.status != "committed" or result.cycle is None:
                return self._response(
                    "halted", request.command, result.reason
                )
            output = result.cycle.output
            return self._response(
                "ok",
                request.command,
                "cycle_committed",
                None if output is None else output.payload,
            )

        if request.command == "checkpoint":
            if not self._audited.journal.entries:
                return self._response(
                    "halted", request.command, "empty_session"
                )
            save_checkpoint_atomic(
                self._checkpoint_path, make_checkpoint(self._audited)
            )
            return self._response("ok", request.command, "checkpoint_written")

        recovered = load_checkpoint(self._checkpoint_path)
        if recovered is None:
            return self._response(
                "halted", request.command, "checkpoint_rejected"
            )
        self._audited = recovered
        return self._response("ok", request.command, "checkpoint_recovered")


def request(command: str, **changes: object) -> ControlRequest:
    values: dict[str, object] = {
        "identity_anchor": IDENTITY_ANCHOR,
        "provenance_anchor": PROVENANCE_ANCHOR,
        "command": command,
    }
    values.update(changes)
    return ControlRequest(**values)  # type: ignore[arg-type]


def run_self_test() -> dict[str, object]:
    tests: dict[str, bool] = {}

    with tempfile.TemporaryDirectory(prefix="nomcog-r006-") as directory:
        checkpoint_path = Path(directory) / "runtime.checkpoint.json"
        boundary = LocalControlBoundary(checkpoint_path)

        status = boundary.handle(request("status"))
        tests["status_is_read_only"] = (
            status.status == "ok"
            and status.reason == "ready"
            and status.receipt_count == 0
            and status.next_sequence == 1
        )

        submitted = boundary.handle(
            request("submit", packet_sequence=1, payload=41)
        )
        tests["submit_commits_cycle"] = (
            submitted.status == "ok"
            and submitted.output_payload == 42
            and submitted.receipt_count == 1
            and submitted.next_sequence == 2
        )

        saved = boundary.handle(request("checkpoint"))
        tests["checkpoint_command_writes"] = (
            saved.status == "ok" and checkpoint_path.is_file()
        )

        second_boundary = LocalControlBoundary(checkpoint_path)
        recovered = second_boundary.handle(request("recover"))
        tests["recover_command_restores"] = (
            recovered.status == "ok"
            and recovered.receipt_count == 1
            and recovered.next_sequence == 2
        )

        continued = second_boundary.handle(
            request("submit", packet_sequence=2, payload=43)
        )
        tests["recovered_runtime_continues"] = (
            continued.status == "ok"
            and continued.output_payload == 42
            and continued.next_sequence == 3
        )

        before_denials = len(second_boundary.audited.journal.entries)
        unknown = second_boundary.handle(request("set_state"))
        tests["direct_mutation_denied"] = (
            unknown.reason == "command_denied"
            and len(second_boundary.audited.journal.entries) == before_denials
        )

        wrong_identity = second_boundary.handle(
            request("status", identity_anchor=18)
        )
        tests["wrong_identity_denied"] = (
            wrong_identity.reason == "identity_anchor"
        )

        one_sentinel = second_boundary.handle(
            request("status", right_sentinel=False)
        )
        tests["single_sentinel_denied"] = (
            one_sentinel.reason == "dual_sentinel_quorum"
        )

        missing = second_boundary.handle(request("submit"))
        tests["incomplete_submit_denied"] = (
            missing.reason == "missing_packet_fields"
        )

        empty_boundary = LocalControlBoundary(
            Path(directory) / "empty.checkpoint.json"
        )
        empty_checkpoint = empty_boundary.handle(request("checkpoint"))
        tests["empty_checkpoint_denied"] = (
            empty_checkpoint.reason == "empty_session"
        )

    if not all(tests.values()):
        failed = [name for name, passed in tests.items() if not passed]
        raise AssertionError(f"R006 failed: {failed}")

    return {
        "chonk": "R006",
        "status": "PASS",
        "tests_passed": sum(tests.values()),
        "tests_total": len(tests),
        "allowed_commands": sorted(ALLOWED_COMMANDS),
        "denied_command": "set_state",
        "recovered_next_sequence": recovered.next_sequence,
        "continued_output": continued.output_payload,
        "network": "disabled",
        "sample_response": asdict(continued),
    }


if __name__ == "__main__":
    print(json.dumps(run_self_test(), indent=2, sort_keys=True))
