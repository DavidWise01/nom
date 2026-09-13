"""NOMCOG R007: bounded deterministic single-writer scheduler.

Requires R001 through R006 in the same directory. No threads, sockets, network,
or background tasks are created.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import tempfile
from typing import Optional

from nomcog_r006_local_control_boundary import (
    ControlRequest,
    ControlResponse,
    LocalControlBoundary,
    request,
)


QUEUE_CAPACITY = 8


@dataclass(frozen=True)
class ScheduledEvent:
    event_id: int
    control: ControlRequest


@dataclass(frozen=True)
class AdmissionResult:
    accepted: bool
    reason: str
    event_id: int
    queue_depth: int


@dataclass(frozen=True)
class ExecutionReceipt:
    event_id: int
    command: str
    control_status: str
    control_reason: str
    queue_depth_after: int


class DeterministicScheduler:
    def __init__(self, boundary: LocalControlBoundary) -> None:
        self.boundary = boundary
        self._queue: deque[ScheduledEvent] = deque()
        self._next_event_id = 1
        self._processing = False
        self._receipts: list[ExecutionReceipt] = []

    @property
    def queue_depth(self) -> int:
        return len(self._queue)

    @property
    def next_event_id(self) -> int:
        return self._next_event_id

    @property
    def receipts(self) -> tuple[ExecutionReceipt, ...]:
        return tuple(self._receipts)

    def enqueue(self, event: ScheduledEvent) -> AdmissionResult:
        if self._processing:
            return AdmissionResult(
                False, "scheduler_busy", event.event_id, self.queue_depth
            )
        if self.queue_depth >= QUEUE_CAPACITY:
            return AdmissionResult(
                False, "queue_capacity", event.event_id, self.queue_depth
            )
        if event.event_id != self._next_event_id:
            reason = (
                "event_replay"
                if event.event_id < self._next_event_id
                else "event_skip"
            )
            return AdmissionResult(False, reason, event.event_id, self.queue_depth)

        self._queue.append(event)
        self._next_event_id += 1
        return AdmissionResult(True, "queued", event.event_id, self.queue_depth)

    def step(self) -> Optional[ExecutionReceipt]:
        if self._processing or not self._queue:
            return None
        self._processing = True
        try:
            event = self._queue.popleft()
            response: ControlResponse = self.boundary.handle(event.control)
            receipt = ExecutionReceipt(
                event_id=event.event_id,
                command=event.control.command,
                control_status=response.status,
                control_reason=response.reason,
                queue_depth_after=self.queue_depth,
            )
            self._receipts.append(receipt)
            return receipt
        finally:
            self._processing = False

    def drain(self) -> tuple[ExecutionReceipt, ...]:
        produced: list[ExecutionReceipt] = []
        while self._queue:
            receipt = self.step()
            if receipt is None:
                raise RuntimeError("scheduler lost single-writer ownership")
            produced.append(receipt)
        return tuple(produced)


def event(event_id: int, command: str, **changes: object) -> ScheduledEvent:
    return ScheduledEvent(event_id, request(command, **changes))


def run_self_test() -> dict[str, object]:
    tests: dict[str, bool] = {}

    with tempfile.TemporaryDirectory(prefix="nomcog-r007-") as directory:
        boundary = LocalControlBoundary(Path(directory) / "runtime.json")
        scheduler = DeterministicScheduler(boundary)

        work = (
            event(1, "status"),
            event(2, "submit", packet_sequence=1, payload=41),
            event(3, "submit", packet_sequence=2, payload=43),
            event(4, "set_state"),
            event(5, "status"),
        )
        admissions = tuple(scheduler.enqueue(item) for item in work)
        tests["ordered_events_admitted"] = (
            all(result.accepted for result in admissions)
            and scheduler.queue_depth == 5
            and scheduler.next_event_id == 6
        )

        drained = scheduler.drain()
        tests["fifo_execution_order"] = (
            [receipt.event_id for receipt in drained] == [1, 2, 3, 4, 5]
            and scheduler.queue_depth == 0
        )
        tests["denied_command_does_not_stop_queue"] = (
            drained[3].control_reason == "command_denied"
            and drained[4].control_reason == "ready"
            and len(boundary.audited.journal.entries) == 2
        )

        replay = scheduler.enqueue(event(5, "status"))
        skip = scheduler.enqueue(event(7, "status"))
        tests["replay_and_skip_rejected"] = (
            replay.reason == "event_replay"
            and skip.reason == "event_skip"
            and scheduler.queue_depth == 0
            and scheduler.next_event_id == 6
        )

        capacity_boundary = LocalControlBoundary(
            Path(directory) / "capacity.json"
        )
        capacity_scheduler = DeterministicScheduler(capacity_boundary)
        capacity_admissions = [
            capacity_scheduler.enqueue(event(index, "status"))
            for index in range(1, QUEUE_CAPACITY + 1)
        ]
        overflow = capacity_scheduler.enqueue(event(9, "status"))
        tests["capacity_is_exact"] = (
            all(result.accepted for result in capacity_admissions)
            and overflow.reason == "queue_capacity"
            and capacity_scheduler.queue_depth == QUEUE_CAPACITY
            and capacity_scheduler.next_event_id == 9
        )

        capacity_drained = capacity_scheduler.drain()
        tests["capacity_queue_drains_cleanly"] = (
            len(capacity_drained) == QUEUE_CAPACITY
            and capacity_scheduler.queue_depth == 0
            and all(
                receipt.control_status == "ok"
                for receipt in capacity_drained
            )
        )

        busy_boundary = LocalControlBoundary(Path(directory) / "busy.json")
        busy_scheduler = DeterministicScheduler(busy_boundary)
        busy_scheduler._processing = True
        busy = busy_scheduler.enqueue(event(1, "status"))
        busy_step = busy_scheduler.step()
        busy_scheduler._processing = False
        tests["reentrant_work_rejected"] = (
            busy.reason == "scheduler_busy"
            and busy_step is None
            and busy_scheduler.queue_depth == 0
            and busy_scheduler.next_event_id == 1
        )

        idle_step = busy_scheduler.step()
        tests["idle_step_is_noop"] = idle_step is None

    if not all(tests.values()):
        failed = [name for name, passed in tests.items() if not passed]
        raise AssertionError(f"R007 failed: {failed}")

    return {
        "chonk": "R007",
        "status": "PASS",
        "tests_passed": sum(tests.values()),
        "tests_total": len(tests),
        "queue_capacity": QUEUE_CAPACITY,
        "executed_event_ids": [receipt.event_id for receipt in drained],
        "runtime_receipts": len(boundary.audited.journal.entries),
        "denied_event": asdict(drained[3]),
        "next_event_id": scheduler.next_event_id,
        "concurrency": "single-writer",
        "network": "disabled",
    }


if __name__ == "__main__":
    print(json.dumps(run_self_test(), indent=2, sort_keys=True))
