"""NOMCOG R005: bounded atomic checkpoint persistence.

Requires R001 through R004 in the same directory. The self-test writes only
inside an automatically removed temporary directory and opens no network.
"""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import hmac
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Optional

from nomcog_r001_executable_cycle import packet
from nomcog_r003_audit_journal import AuditEntry, AuditedSession, build_three_entry_journal
from nomcog_r004_checkpoint_recovery import (
    RuntimeCheckpoint,
    make_checkpoint,
    recover_checkpoint,
)


SCHEMA = "NOMCOG-R005-v1"
MAX_CHECKPOINT_BYTES = 65_536


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def checkpoint_payload(checkpoint: RuntimeCheckpoint) -> dict[str, object]:
    return {
        "entries": [asdict(entry) for entry in checkpoint.entries],
        "expected_sequence": checkpoint.expected_sequence,
        "head_hash": checkpoint.head_hash,
        "receipt_count": checkpoint.receipt_count,
        "state_window": list(checkpoint.state_window),
    }


def checkpoint_document(checkpoint: RuntimeCheckpoint) -> dict[str, object]:
    body = {
        "schema": SCHEMA,
        "checkpoint": checkpoint_payload(checkpoint),
    }
    return {
        **body,
        "document_hash": hashlib.sha256(canonical_bytes(body)).hexdigest(),
    }


def save_checkpoint_atomic(path: Path, checkpoint: RuntimeCheckpoint) -> None:
    """Write completely, flush, then atomically replace the destination."""
    path = Path(path)
    if not path.parent.is_dir():
        raise ValueError("checkpoint parent directory does not exist")
    encoded = canonical_bytes(checkpoint_document(checkpoint)) + b"\n"
    if len(encoded) > MAX_CHECKPOINT_BYTES:
        raise ValueError("checkpoint exceeds byte bound")

    temporary_name: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(encoded)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def exact_int(value: object) -> Optional[int]:
    return value if type(value) is int and value >= 0 else None


def parse_entry(raw: object) -> Optional[AuditEntry]:
    if not isinstance(raw, dict):
        return None
    required = {
        "index",
        "sequence",
        "input_payload",
        "output_payload",
        "proposal",
        "previous_hash",
        "entry_hash",
    }
    if set(raw) != required:
        return None

    index = exact_int(raw["index"])
    sequence = exact_int(raw["sequence"])
    input_payload = exact_int(raw["input_payload"])
    output_payload = exact_int(raw["output_payload"])
    proposal = raw["proposal"]
    previous_hash = raw["previous_hash"]
    entry_hash = raw["entry_hash"]
    if None in (index, sequence, input_payload, output_payload):
        return None
    if proposal not in {"increase", "hold", "decrease"}:
        return None
    if not isinstance(previous_hash, str) or len(previous_hash) != 64:
        return None
    if not isinstance(entry_hash, str) or len(entry_hash) != 64:
        return None
    return AuditEntry(
        index=index,
        sequence=sequence,
        input_payload=input_payload,
        output_payload=output_payload,
        proposal=proposal,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
    )


def parse_checkpoint(raw: object) -> Optional[RuntimeCheckpoint]:
    if not isinstance(raw, dict):
        return None
    required = {
        "entries",
        "expected_sequence",
        "head_hash",
        "receipt_count",
        "state_window",
    }
    if set(raw) != required:
        return None
    if not isinstance(raw["entries"], list):
        return None
    parsed_entries = [parse_entry(entry) for entry in raw["entries"]]
    if any(entry is None for entry in parsed_entries):
        return None
    if not isinstance(raw["state_window"], list):
        return None
    state_window = [exact_int(value) for value in raw["state_window"]]
    if any(value is None for value in state_window):
        return None
    expected_sequence = exact_int(raw["expected_sequence"])
    receipt_count = exact_int(raw["receipt_count"])
    head_hash = raw["head_hash"]
    if expected_sequence is None or receipt_count is None:
        return None
    if not isinstance(head_hash, str) or len(head_hash) != 64:
        return None
    return RuntimeCheckpoint(
        entries=tuple(entry for entry in parsed_entries if entry is not None),
        head_hash=head_hash,
        expected_sequence=expected_sequence,
        state_window=tuple(value for value in state_window if value is not None),
        receipt_count=receipt_count,
    )


def load_checkpoint(path: Path) -> Optional[AuditedSession]:
    """Load only a bounded, canonical, hash-valid, recoverable checkpoint."""
    path = Path(path)
    try:
        if path.stat().st_size > MAX_CHECKPOINT_BYTES:
            return None
        raw_bytes = path.read_bytes()
        document: Any = json.loads(raw_bytes)
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(document, dict):
        return None
    if set(document) != {"schema", "checkpoint", "document_hash"}:
        return None
    if document["schema"] != SCHEMA:
        return None
    supplied_hash = document["document_hash"]
    if not isinstance(supplied_hash, str) or len(supplied_hash) != 64:
        return None
    body = {
        "schema": document["schema"],
        "checkpoint": document["checkpoint"],
    }
    expected_hash = hashlib.sha256(canonical_bytes(body)).hexdigest()
    if not hmac.compare_digest(supplied_hash, expected_hash):
        return None
    checkpoint = parse_checkpoint(document["checkpoint"])
    return None if checkpoint is None else recover_checkpoint(checkpoint)


def run_self_test() -> dict[str, object]:
    tests: dict[str, bool] = {}
    original = build_three_entry_journal()
    checkpoint = make_checkpoint(original)

    with tempfile.TemporaryDirectory(prefix="nomcog-r005-") as directory:
        root = Path(directory)
        path = root / "runtime.checkpoint.json"
        save_checkpoint_atomic(path, checkpoint)
        tests["atomic_file_created"] = path.is_file()

        recovered = load_checkpoint(path)
        tests["round_trip_recovers"] = (
            recovered is not None
            and recovered.journal.entries == original.journal.entries
            and recovered.journal.head_hash == original.journal.head_hash
        )

        document = json.loads(path.read_text(encoding="utf-8"))
        document["checkpoint"]["entries"][1]["output_payload"] = 99
        path.write_text(json.dumps(document), encoding="utf-8")
        tests["tampered_document_rejected"] = load_checkpoint(path) is None

        path.write_bytes(b'{"schema":"NOMCOG-R005-v1"')
        tests["truncated_document_rejected"] = load_checkpoint(path) is None

        wrong_schema = checkpoint_document(checkpoint)
        wrong_schema["schema"] = "NOMCOG-R005-v2"
        path.write_text(json.dumps(wrong_schema), encoding="utf-8")
        tests["wrong_schema_rejected"] = load_checkpoint(path) is None

        replacement_source = build_three_entry_journal()
        fourth = replacement_source.submit(packet(sequence=4, payload=40))
        if fourth.status != "committed":
            raise AssertionError("replacement fixture did not commit")
        replacement = make_checkpoint(replacement_source)
        save_checkpoint_atomic(path, replacement)
        replaced = load_checkpoint(path)
        tests["atomic_replacement_recovers_latest"] = (
            replaced is not None
            and len(replaced.journal.entries) == 4
            and replaced.session.runtime.expected_sequence == 5
        )

        temporary_files = list(root.glob(f".{path.name}.*.tmp"))
        tests["no_temporary_residue"] = temporary_files == []

        stored_bytes = path.stat().st_size

    if not all(tests.values()):
        failed = [name for name, passed in tests.items() if not passed]
        raise AssertionError(f"R005 failed: {failed}")

    return {
        "chonk": "R005",
        "status": "PASS",
        "tests_passed": sum(tests.values()),
        "tests_total": len(tests),
        "schema": SCHEMA,
        "stored_bytes": stored_bytes,
        "replacement_entries": 4,
        "next_sequence": 5,
        "tamper_rejected": True,
        "truncation_rejected": True,
        "temporary_residue": 0,
        "network": "disabled",
    }


if __name__ == "__main__":
    print(json.dumps(run_self_test(), indent=2, sort_keys=True))
