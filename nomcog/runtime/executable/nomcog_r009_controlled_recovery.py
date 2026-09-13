"""NOMCOG R009: explicit, checkpoint-bound recovery after circuit halt.

Requires R001 through R008 in the same directory. No background restart,
threads, or network access.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import tempfile
from typing import Optional

from nomcog_r001_executable_cycle import IDENTITY_ANCHOR, PROVENANCE_ANCHOR
from nomcog_r006_local_control_boundary import LocalControlBoundary, request
from nomcog_r007_deterministic_scheduler import DeterministicScheduler, event
from nomcog_r008_fault_convergence import FaultWatchdog


@dataclass(frozen=True)
class RecoveryReceipt:
    status: str
    reason: str
    quarantined_events: int
    resumed_event_id: int
    recovered_sequence: int


class ResumedScheduler(DeterministicScheduler):
    def __init__(
        self, boundary: LocalControlBoundary, resumed_event_id: int
    ) -> None:
        super().__init__(boundary)
        if resumed_event_id < 1:
            raise ValueError("resumed_event_id must be positive")
        self._next_event_id = resumed_event_id


def controlled_recovery(
    halted_scheduler: DeterministicScheduler,
    watchdog: FaultWatchdog,
    checkpoint_path: Path,
    *,
    identity_anchor: int = IDENTITY_ANCHOR,
    provenance_anchor: int = PROVENANCE_ANCHOR,
    left_sentinel: bool = True,
    right_sentinel: bool = True,
) -> tuple[RecoveryReceipt, Optional[ResumedScheduler]]:
    quarantined = halted_scheduler.queue_depth
    resumed_event_id = halted_scheduler.next_event_id

    def denied(reason: str) -> tuple[RecoveryReceipt, None]:
        return (
            RecoveryReceipt(
                status="halted",
                reason=reason,
                quarantined_events=quarantined,
                resumed_event_id=resumed_event_id,
                recovered_sequence=0,
            ),
            None,
        )

    if watchdog.state != "open":
        return denied("circuit_not_open")
    if identity_anchor != IDENTITY_ANCHOR:
        return denied("identity_anchor")
    if provenance_anchor != PROVENANCE_ANCHOR:
        return denied("provenance_anchor")
    if not (left_sentinel and right_sentinel):
        return denied("dual_sentinel_quorum")

    boundary = LocalControlBoundary(Path(checkpoint_path))
    response = boundary.handle(
        request(
            "recover",
            identity_anchor=identity_anchor,
            provenance_anchor=provenance_anchor,
            left_sentinel=left_sentinel,
            right_sentinel=right_sentinel,
        )
    )
    if response.status != "ok":
        return denied("checkpoint_rejected")

    resumed = ResumedScheduler(boundary, resumed_event_id)
    receipt = RecoveryReceipt(
        status="recovered",
        reason="checkpoint_witnessed",
        quarantined_events=quarantined,
        resumed_event_id=resumed_event_id,
        recovered_sequence=response.next_sequence,
    )
    return receipt, resumed


def build_halted_fixture(
    checkpoint_path: Path,
) -> tuple[DeterministicScheduler, FaultWatchdog]:
    boundary = LocalControlBoundary(checkpoint_path)
    scheduler = DeterministicScheduler(boundary)
    initial = (
        event(1, "submit", packet_sequence=1, payload=41),
        event(2, "checkpoint"),
    )
    for item in initial:
        if not scheduler.enqueue(item).accepted:
            raise AssertionError("initial fixture admission failed")
    healthy_watchdog = FaultWatchdog()
    healthy = healthy_watchdog.run(scheduler)
    if healthy.state != "closed" or not checkpoint_path.is_file():
        raise AssertionError("fixture checkpoint was not established")

    fault_work = (
        event(3, "set_state"),
        event(4, "set_state"),
        event(5, "set_state"),
        event(6, "status"),
    )
    for item in fault_work:
        if not scheduler.enqueue(item).accepted:
            raise AssertionError("fault fixture admission failed")
    halted_watchdog = FaultWatchdog()
    halted = halted_watchdog.run(scheduler)
    if halted.state != "open" or scheduler.queue_depth != 1:
        raise AssertionError("fixture did not reach bounded halt")
    return scheduler, halted_watchdog


def run_self_test() -> dict[str, object]:
    tests: dict[str, bool] = {}

    with tempfile.TemporaryDirectory(prefix="nomcog-r009-") as directory:
        root = Path(directory)
        checkpoint_path = root / "runtime.json"
        halted_scheduler, open_watchdog = build_halted_fixture(checkpoint_path)

        closed_watchdog = FaultWatchdog()
        not_open, no_scheduler = controlled_recovery(
            halted_scheduler,
            closed_watchdog,
            checkpoint_path,
        )
        tests["open_circuit_required"] = (
            not_open.reason == "circuit_not_open" and no_scheduler is None
        )

        wrong_identity, no_scheduler = controlled_recovery(
            halted_scheduler,
            open_watchdog,
            checkpoint_path,
            identity_anchor=18,
        )
        tests["identity_required"] = (
            wrong_identity.reason == "identity_anchor" and no_scheduler is None
        )

        one_sentinel, no_scheduler = controlled_recovery(
            halted_scheduler,
            open_watchdog,
            checkpoint_path,
            right_sentinel=False,
        )
        tests["dual_sentinel_required"] = (
            one_sentinel.reason == "dual_sentinel_quorum"
            and no_scheduler is None
        )

        corrupt_path = root / "corrupt.json"
        corrupt_path.write_text("not a checkpoint", encoding="utf-8")
        corrupt, no_scheduler = controlled_recovery(
            halted_scheduler,
            open_watchdog,
            corrupt_path,
        )
        tests["valid_checkpoint_required"] = (
            corrupt.reason == "checkpoint_rejected" and no_scheduler is None
        )

        recovered, resumed = controlled_recovery(
            halted_scheduler,
            open_watchdog,
            checkpoint_path,
        )
        tests["clean_recovery_succeeds"] = (
            recovered.status == "recovered"
            and recovered.recovered_sequence == 2
            and resumed is not None
        )
        tests["old_queue_is_quarantined"] = (
            recovered.quarantined_events == 1
            and halted_scheduler.queue_depth == 1
            and resumed is not None
            and resumed.queue_depth == 0
        )

        continued_status = "not_run"
        continued_reason = "not_run"
        if resumed is not None:
            admission = resumed.enqueue(
                event(recovered.resumed_event_id, "submit", packet_sequence=2, payload=43)
            )
            receipt = resumed.step()
            tests["event_identity_continues"] = (
                admission.accepted
                and receipt is not None
                and receipt.event_id == recovered.resumed_event_id
            )
            if receipt is not None:
                continued_status = receipt.control_status
                continued_reason = receipt.control_reason
        else:
            tests["event_identity_continues"] = False

        tests["recovered_runtime_continues"] = (
            continued_status == "ok" and continued_reason == "cycle_committed"
        )

    if not all(tests.values()):
        failed = [name for name, passed in tests.items() if not passed]
        raise AssertionError(f"R009 failed: {failed}")

    return {
        "chonk": "R009",
        "status": "PASS",
        "tests_passed": sum(tests.values()),
        "tests_total": len(tests),
        "recovery": asdict(recovered),
        "old_queue_remaining": halted_scheduler.queue_depth,
        "new_queue_initial": 0,
        "continued_status": continued_status,
        "automatic_restart": False,
        "network": "disabled",
    }


if __name__ == "__main__":
    print(json.dumps(run_self_test(), indent=2, sort_keys=True))
