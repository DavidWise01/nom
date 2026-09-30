#!/usr/bin/env python3
"""Local verifier for OaSIs AE witness receipts v179.

This bridge is additive. It does not modify frozen Posi v00.01 and it performs
no network access.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import sys

RECEIPT_SCHEMA = "oasis.ae.witness.receipt.v179"
PACKET_SCHEMA = "nom.nomcog.oasis.witness.packet.v179"

IDENTITY_ANCHOR = 17
PROVENANCE_ANCHOR = 131
NETWORK = "disabled"
POSI = "Posi v00.01"
STABLE_REF = "posi-v00.01"
SEALED_PARENT_COMMIT = "aac18870dfbc12a20bd7b1e220336286ac887873"
EXECUTABLE_CAPSTONE_SHA256 = "feb8194640e32be06827e42ce755fcd7408af73d4aa592fe9ff632704c3ff427"
MANIFEST_SHA256 = "ebb5588a22c644f13f674d9c11cf476d16ac8847e8c8196d89f2ff21c108ffd8"


def canonical_json(obj) -> bytes:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_receipt(receipt: dict) -> bool:
    required = {
        "schema",
        "kernel_version",
        "source_repo",
        "source_parent_commit",
        "source_frozen_canon_sha256",
        "source_state_id",
        "source_state_seal",
        "source_state_json_sha256",
        "source_generation",
        "source_point",
        "source_orbit_class",
        "source_lane_label",
        "source_lane_class_binding",
        "binding_status",
        "source_control",
        "source_halted",
        "source_polarity",
        "nom_repo",
        "nom_tether_commit",
        "nom_posi",
        "nom_stable_ref",
        "nom_sealed_parent_commit",
        "nom_executable_capstone_sha256",
        "nom_manifest_sha256",
        "nom_identity_anchor",
        "nom_provenance_anchor",
        "nom_network",
        "previous_receipt_id",
        "previous_receipt_seal",
        "receipt_id",
        "seal",
    }
    if set(receipt) != required:
        return False

    if receipt["schema"] != RECEIPT_SCHEMA:
        return False
    if receipt["kernel_version"] != "v179":
        return False
    if receipt["source_repo"] != "DavidWise01/oasis":
        return False
    if receipt["nom_repo"] != "DavidWise01/nom":
        return False
    if receipt["nom_posi"] != POSI or receipt["nom_stable_ref"] != STABLE_REF:
        return False
    if receipt["nom_sealed_parent_commit"] != SEALED_PARENT_COMMIT:
        return False
    if receipt["nom_executable_capstone_sha256"] != EXECUTABLE_CAPSTONE_SHA256:
        return False
    if receipt["nom_manifest_sha256"] != MANIFEST_SHA256:
        return False
    if receipt["nom_identity_anchor"] != IDENTITY_ANCHOR:
        return False
    if receipt["nom_provenance_anchor"] != PROVENANCE_ANCHOR:
        return False
    if receipt["nom_network"] != NETWORK:
        return False

    point = receipt["source_point"]
    if (
        not isinstance(point, list)
        or len(point) != 2
        or not all(isinstance(v, int) for v in point)
    ):
        return False

    orbit_class = receipt["source_orbit_class"]
    if not isinstance(orbit_class, int) or not (0 <= orbit_class < 10):
        return False

    status = receipt["binding_status"]
    binding = receipt["source_lane_class_binding"]
    if status == "UNBOUND":
        if binding is not None:
            return False
    elif status == "BOUND":
        if binding != orbit_class:
            return False
    else:
        return False

    if receipt["source_control"] == "/0/0" and receipt["source_halted"] is not True:
        return False

    core = dict(receipt)
    receipt_id = core.pop("receipt_id")
    seal = core.pop("seal")

    expected_id = "wr179:" + sha256_bytes(
        b"receipt-id|" + canonical_json(core)
    )[:24]
    if receipt_id != expected_id:
        return False

    payload = {**core, "receipt_id": receipt_id}
    expected_seal = sha256_bytes(canonical_json(payload))
    return seal == expected_seal


def verify_chain(receipts: list[dict]) -> bool:
    for i, receipt in enumerate(receipts):
        if not verify_receipt(receipt):
            return False
        if i == 0:
            if receipt["previous_receipt_id"] is not None:
                return False
            if receipt["previous_receipt_seal"] is not None:
                return False
        else:
            prev = receipts[i - 1]
            if receipt["previous_receipt_id"] != prev["receipt_id"]:
                return False
            if receipt["previous_receipt_seal"] != prev["seal"]:
                return False
    return True


def verify_packet(packet: dict) -> bool:
    if packet.get("schema") != PACKET_SCHEMA:
        return False
    if packet.get("network") != NETWORK:
        return False
    if packet.get("identity_anchor") != IDENTITY_ANCHOR:
        return False
    if packet.get("provenance_anchor") != PROVENANCE_ANCHOR:
        return False
    if packet.get("posi") != POSI:
        return False
    if packet.get("posi_stable_ref") != STABLE_REF:
        return False
    receipt = packet.get("oasis_receipt")
    return isinstance(receipt, dict) and verify_receipt(receipt)


def _seal_core(core: dict) -> dict:
    receipt_id = "wr179:" + sha256_bytes(
        b"receipt-id|" + canonical_json(core)
    )[:24]
    payload = {**core, "receipt_id": receipt_id}
    return {
        **payload,
        "seal": sha256_bytes(canonical_json(payload)),
    }


def self_test() -> dict:
    core = {
        "schema": RECEIPT_SCHEMA,
        "kernel_version": "v179",
        "source_repo": "DavidWise01/oasis",
        "source_parent_commit": "2c1c9eabe99a3221fbf8840a51b2f4adbc07120c",
        "source_frozen_canon_sha256": "8f2be8951098c7e1764c3c0f5bba982fb3fd8c71f094924b79d0172a313a7bf8",
        "source_state_id": "v178:test",
        "source_state_seal": "11" * 32,
        "source_state_json_sha256": "22" * 32,
        "source_generation": 0,
        "source_point": [0, 0],
        "source_orbit_class": 0,
        "source_lane_label": "plank0",
        "source_lane_class_binding": None,
        "binding_status": "UNBOUND",
        "source_control": "RUN",
        "source_halted": False,
        "source_polarity": "-",
        "nom_repo": "DavidWise01/nom",
        "nom_tether_commit": "fa166428fba73d34979954296968c5dd00950354",
        "nom_posi": POSI,
        "nom_stable_ref": STABLE_REF,
        "nom_sealed_parent_commit": SEALED_PARENT_COMMIT,
        "nom_executable_capstone_sha256": EXECUTABLE_CAPSTONE_SHA256,
        "nom_manifest_sha256": MANIFEST_SHA256,
        "nom_identity_anchor": IDENTITY_ANCHOR,
        "nom_provenance_anchor": PROVENANCE_ANCHOR,
        "nom_network": NETWORK,
        "previous_receipt_id": None,
        "previous_receipt_seal": None,
    }
    receipt = _seal_core(core)
    assert verify_receipt(receipt)

    tampered = dict(receipt)
    tampered["nom_identity_anchor"] = 18
    assert not verify_receipt(tampered)

    fake_bound = dict(core)
    fake_bound["binding_status"] = "BOUND"
    fake_bound["source_lane_class_binding"] = 1
    fake_bound = _seal_core(fake_bound)
    assert not verify_receipt(fake_bound)

    stopped = dict(core)
    stopped["source_control"] = "/0/0"
    stopped["source_halted"] = True
    stopped = _seal_core(stopped)
    assert verify_receipt(stopped)

    packet = {
        "schema": PACKET_SCHEMA,
        "network": NETWORK,
        "identity_anchor": IDENTITY_ANCHOR,
        "provenance_anchor": PROVENANCE_ANCHOR,
        "posi": POSI,
        "posi_stable_ref": STABLE_REF,
        "oasis_receipt": receipt,
    }
    assert verify_packet(packet)

    return {
        "status": "0e / NOMCOG OASIS v179 RECEIPT VERIFIER PASS",
        "network": NETWORK,
        "identity_anchor": IDENTITY_ANCHOR,
        "provenance_anchor": PROVENANCE_ANCHOR,
        "tests": {
            "valid_unbound_receipt": "PASS",
            "anchor_tamper_rejected": "PASS",
            "fake_bound_mapping_rejected": "PASS",
            "stop_receipt": "PASS",
            "bridge_packet": "PASS",
        },
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        print(json.dumps(self_test(), indent=2))
        return 0

    if args.path is None:
        parser.error("provide a receipt/packet JSON path or --self-test")

    data = json.loads(args.path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        ok = verify_chain(data)
        kind = "chain"
    elif data.get("schema") == PACKET_SCHEMA:
        ok = verify_packet(data)
        kind = "packet"
    else:
        ok = verify_receipt(data)
        kind = "receipt"

    print(json.dumps({"kind": kind, "valid": ok}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
