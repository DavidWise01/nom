"""NOMCOG R010: executable runtime capstone and dependency seal.

Requires the frozen R001 through R009 files in the same directory.
The capstone reruns every component self-test and performs one integrated
halt/recovery cycle. It opens no network connection.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile

from nomcog_r001_executable_cycle import run_self_test as test_r001
from nomcog_r002_bounded_session import run_self_test as test_r002
from nomcog_r003_audit_journal import run_self_test as test_r003
from nomcog_r004_checkpoint_recovery import run_self_test as test_r004
from nomcog_r005_atomic_checkpoint_store import (
    load_checkpoint,
    run_self_test as test_r005,
)
from nomcog_r006_local_control_boundary import (
    LocalControlBoundary,
    run_self_test as test_r006,
)
from nomcog_r007_deterministic_scheduler import (
    DeterministicScheduler,
    event,
    run_self_test as test_r007,
)
from nomcog_r008_fault_convergence import (
    FaultWatchdog,
    run_self_test as test_r008,
)
from nomcog_r009_controlled_recovery import (
    controlled_recovery,
    run_self_test as test_r009,
)


FROZEN_HASHES = {
    "nomcog_r001_executable_cycle.py":
        "1bb72df9ca3a6599103ff6daf2918aacfc64e86da21d6db2be81add40645ed2e",
    "nomcog_r002_bounded_session.py":
        "23c9da657ecfeb41e8c78f1450d4e2a6854295d027bfa63965499d9a5129a663",
    "nomcog_r003_audit_journal.py":
        "c830aa113c42dc3350e519d3d1baa75bbbd0585cc6f4f28645b22b4574d5a855",
    "nomcog_r004_checkpoint_recovery.py":
        "a4195dfca045108dbd1e43a616986a00550ea5ae9e783843c97ce213da0ffb65",
    "nomcog_r005_atomic_checkpoint_store.py":
        "2454cd6c2eacadb0fa04e38c9599d3dda08e6862966fc4fdd80ea844ab8732a0",
    "nomcog_r006_local_control_boundary.py":
        "a5a1c97646916851ecfc9035dc735514438a4fa6f374037bced0ae84c40b44df",
    "nomcog_r007_deterministic_scheduler.py":
        "4259f1c1e2e36790c433668f003e3644726a09e59a758aead2f9547ac0c1084b",
    "nomcog_r008_fault_convergence.py":
        "49ae216b71802a2c78f9ac91b27be54a8df11eaae48cc95431b58c94cffed947",
    "nomcog_r009_controlled_recovery.py":
        "4ab04b9d766a558250212f959d41312d924b60cc4e4f239283e5b5af06a5d4c4",
}


COMPONENT_TESTS = {
    "R001": test_r001,
    "R002": test_r002,
    "R003": test_r003,
    "R004": test_r004,
    "R005": test_r005,
    "R006": test_r006,
    "R007": test_r007,
    "R008": test_r008,
    "R009": test_r009,
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(65_536), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_frozen_files(base_directory: Path) -> dict[str, bool]:
    return {
        name: path.is_file() and file_sha256(path) == expected
        for name, expected in FROZEN_HASHES.items()
        for path in (base_directory / name,)
    }


def run_component_tests() -> dict[str, dict[str, object]]:
    results: dict[str, dict[str, object]] = {}
    for name, test in COMPONENT_TESTS.items():
        result = test()
        if result.get("status") != "PASS":
            raise AssertionError(f"{name} component test did not pass")
        results[name] = result
    return results


def require_admission(
    scheduler: DeterministicScheduler,
    event_id: int,
    command: str,
    **changes: object,
) -> None:
    admission = scheduler.enqueue(event(event_id, command, **changes))
    if not admission.accepted:
        raise AssertionError(
            f"event {event_id} admission failed: {admission.reason}"
        )


def run_integrated_cycle(checkpoint_path: Path) -> dict[str, object]:
    checks: dict[str, bool] = {}
    boundary = LocalControlBoundary(checkpoint_path)
    scheduler = DeterministicScheduler(boundary)

    require_admission(
        scheduler, 1, "submit", packet_sequence=1, payload=41
    )
    require_admission(scheduler, 2, "checkpoint")
    healthy_watchdog = FaultWatchdog()
    healthy = healthy_watchdog.run(scheduler)
    checks["healthy_cycle_checkpointed"] = (
        healthy.state == "closed"
        and healthy.processed == 2
        and checkpoint_path.is_file()
        and len(boundary.audited.journal.entries) == 1
    )

    for event_id in (3, 4, 5):
        require_admission(scheduler, event_id, "set_state")
    require_admission(scheduler, 6, "status")
    fault_watchdog = FaultWatchdog()
    halted = fault_watchdog.run(scheduler)
    checks["fault_halt_is_exact"] = (
        halted.state == "open"
        and halted.processed == 3
        and scheduler.queue_depth == 1
    )

    recovery, resumed = controlled_recovery(
        scheduler, fault_watchdog, checkpoint_path
    )
    checks["controlled_recovery_passes"] = (
        recovery.status == "recovered"
        and recovery.recovered_sequence == 2
        and recovery.resumed_event_id == 7
        and resumed is not None
    )
    checks["old_queue_is_quarantined"] = (
        recovery.quarantined_events == 1
        and scheduler.queue_depth == 1
        and resumed is not None
        and resumed.queue_depth == 0
    )

    continuation_status = "not_run"
    checkpoint_status = "not_run"
    if resumed is not None:
        require_admission(
            resumed, 7, "submit", packet_sequence=2, payload=43
        )
        continuation = resumed.step()
        if continuation is not None:
            continuation_status = continuation.control_reason
        require_admission(resumed, 8, "checkpoint")
        final_checkpoint = resumed.step()
        if final_checkpoint is not None:
            checkpoint_status = final_checkpoint.control_reason

    checks["continuation_commits"] = (
        continuation_status == "cycle_committed"
    )
    checks["final_checkpoint_written"] = (
        checkpoint_status == "checkpoint_written"
    )

    final_runtime = load_checkpoint(checkpoint_path)
    checks["final_state_recovers"] = (
        final_runtime is not None
        and len(final_runtime.journal.entries) == 2
        and final_runtime.session.runtime.expected_sequence == 3
        and [entry.output_payload for entry in final_runtime.journal.entries]
        == [42, 42]
    )

    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise AssertionError(f"R010 integration failed: {failed}")
    return {
        "checks": checks,
        "halted_after": fault_watchdog.observed_events,
        "quarantined_events": recovery.quarantined_events,
        "resumed_event_id": recovery.resumed_event_id,
        "final_packet_sequence": 2,
        "next_packet_sequence": 3,
        "final_outputs": [42, 42],
    }


def run_self_test() -> dict[str, object]:
    base_directory = Path(__file__).resolve().parent
    hash_checks = verify_frozen_files(base_directory)
    if not all(hash_checks.values()):
        failed = [name for name, passed in hash_checks.items() if not passed]
        raise AssertionError(f"frozen dependency hash mismatch: {failed}")

    component_results = run_component_tests()
    component_test_count = sum(
        int(result["tests_passed"]) for result in component_results.values()
    )

    with tempfile.TemporaryDirectory(prefix="nomcog-r010-") as directory:
        integrated = run_integrated_cycle(Path(directory) / "runtime.json")

    integration_test_count = len(integrated["checks"])
    return {
        "chonk": "R010",
        "status": "PASS",
        "frozen_files_verified": sum(hash_checks.values()),
        "frozen_files_total": len(hash_checks),
        "component_tests_passed": component_test_count,
        "integration_tests_passed": integration_test_count,
        "tests_passed_total": component_test_count + integration_test_count,
        "component_status": {
            name: result["status"]
            for name, result in component_results.items()
        },
        "integrated_cycle": integrated,
        "runtime_state": "closed",
        "network": "disabled",
    }


if __name__ == "__main__":
    print(json.dumps(run_self_test(), indent=2, sort_keys=True))
