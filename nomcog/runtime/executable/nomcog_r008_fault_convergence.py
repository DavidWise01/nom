"""NOMCOG R008: deterministic fault convergence and circuit halt.

Requires R001 through R007 in the same directory. No threads or network.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import tempfile

from nomcog_r006_local_control_boundary import LocalControlBoundary
from nomcog_r007_deterministic_scheduler import (
    DeterministicScheduler,
    ExecutionReceipt,
    event,
)


FAULT_LIMIT = 3


@dataclass(frozen=True)
class FaultRecord:
    event_id: int
    reason: str
    consecutive_faults: int


@dataclass(frozen=True)
class WatchdogResult:
    state: str
    processed: int
    remaining: int
    consecutive_faults: int


class FaultWatchdog:
    def __init__(self, fault_limit: int = FAULT_LIMIT) -> None:
        if fault_limit < 1:
            raise ValueError("fault_limit must be positive")
        self.fault_limit = fault_limit
        self.state = "closed"
        self.consecutive_faults = 0
        self.faults: list[FaultRecord] = []
        self.observed_events: list[int] = []

    def observe(self, receipt: ExecutionReceipt) -> None:
        if self.state != "closed":
            raise RuntimeError("open watchdog cannot observe new work")
        self.observed_events.append(receipt.event_id)
        if receipt.control_status == "ok":
            self.consecutive_faults = 0
            return

        self.consecutive_faults += 1
        self.faults.append(
            FaultRecord(
                event_id=receipt.event_id,
                reason=receipt.control_reason,
                consecutive_faults=self.consecutive_faults,
            )
        )
        if self.consecutive_faults >= self.fault_limit:
            self.state = "open"

    def run(self, scheduler: DeterministicScheduler) -> WatchdogResult:
        processed = 0
        while self.state == "closed" and scheduler.queue_depth > 0:
            receipt = scheduler.step()
            if receipt is None:
                break
            self.observe(receipt)
            processed += 1
        return WatchdogResult(
            state=self.state,
            processed=processed,
            remaining=scheduler.queue_depth,
            consecutive_faults=self.consecutive_faults,
        )


def scheduler_with_events(
    checkpoint_path: Path, commands: tuple[str, ...]
) -> DeterministicScheduler:
    scheduler = DeterministicScheduler(LocalControlBoundary(checkpoint_path))
    for event_id, command in enumerate(commands, start=1):
        admission = scheduler.enqueue(event(event_id, command))
        if not admission.accepted:
            raise AssertionError(f"fixture admission failed: {admission.reason}")
    return scheduler


def run_self_test() -> dict[str, object]:
    tests: dict[str, bool] = {}

    with tempfile.TemporaryDirectory(prefix="nomcog-r008-") as directory:
        root = Path(directory)

        halt_scheduler = scheduler_with_events(
            root / "halt.json",
            ("set_state", "set_state", "set_state", "status"),
        )
        halt_watchdog = FaultWatchdog()
        halted = halt_watchdog.run(halt_scheduler)
        tests["three_faults_open_circuit"] = (
            halted.state == "open"
            and halted.processed == FAULT_LIMIT
            and halted.remaining == 1
            and halted.consecutive_faults == FAULT_LIMIT
        )

        second_run = halt_watchdog.run(halt_scheduler)
        tests["open_circuit_processes_nothing"] = (
            second_run.processed == 0
            and second_run.remaining == 1
            and halt_watchdog.observed_events == [1, 2, 3]
        )

        reset_scheduler = scheduler_with_events(
            root / "reset.json",
            ("set_state", "status", "set_state", "set_state"),
        )
        reset_watchdog = FaultWatchdog()
        reset_result = reset_watchdog.run(reset_scheduler)
        tests["success_clears_fault_count"] = (
            reset_result.state == "closed"
            and reset_result.processed == 4
            and reset_result.remaining == 0
            and reset_result.consecutive_faults == 2
        )

        exact_scheduler = scheduler_with_events(
            root / "exact.json", ("set_state", "set_state")
        )
        exact_watchdog = FaultWatchdog()
        exact_result = exact_watchdog.run(exact_scheduler)
        tests["below_limit_stays_closed"] = (
            exact_result.state == "closed"
            and exact_result.consecutive_faults == 2
        )

        valid_scheduler = scheduler_with_events(
            root / "valid.json", ("status", "status", "status")
        )
        valid_watchdog = FaultWatchdog()
        valid_result = valid_watchdog.run(valid_scheduler)
        tests["valid_work_has_no_faults"] = (
            valid_result.state == "closed"
            and valid_result.consecutive_faults == 0
            and valid_watchdog.faults == []
        )

        deterministic_scheduler = scheduler_with_events(
            root / "deterministic.json",
            ("set_state", "status", "set_state", "set_state"),
        )
        deterministic_watchdog = FaultWatchdog()
        deterministic_watchdog.run(deterministic_scheduler)
        tests["fault_trace_is_deterministic"] = (
            deterministic_watchdog.faults == reset_watchdog.faults
            and deterministic_watchdog.observed_events
            == reset_watchdog.observed_events
        )

        invalid_limit_rejected = False
        try:
            FaultWatchdog(0)
        except ValueError:
            invalid_limit_rejected = True
        tests["invalid_limit_rejected"] = invalid_limit_rejected

    if not all(tests.values()):
        failed = [name for name, passed in tests.items() if not passed]
        raise AssertionError(f"R008 failed: {failed}")

    return {
        "chonk": "R008",
        "status": "PASS",
        "tests_passed": sum(tests.values()),
        "tests_total": len(tests),
        "fault_limit": FAULT_LIMIT,
        "halted_after_events": halt_watchdog.observed_events,
        "queued_after_halt": halted.remaining,
        "fault_trace": [asdict(record) for record in halt_watchdog.faults],
        "automatic_restart": False,
        "network": "disabled",
    }


if __name__ == "__main__":
    print(json.dumps(run_self_test(), indent=2, sort_keys=True))
