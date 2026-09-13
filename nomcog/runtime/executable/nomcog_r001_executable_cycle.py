"""NOMCOG R001: deterministic executable five-stage cycle.

This is an executable model of the already frozen Lean runtime closures.
It uses only the Python standard library, opens no sockets, and writes no files.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from typing import Optional


IDENTITY_ANCHOR = 17
PROVENANCE_ANCHOR = 131
REGISTER_SIZE = 256
CARRIER_WIDTH = 4
HOMEOSTATIC_ANCHOR = 42


@dataclass(frozen=True)
class InputPacket:
    identity_anchor: int
    provenance_anchor: int
    sequence: int
    payload: int
    checksum: int
    coherent: bool = True
    carrier_present: bool = True
    carrier_width: int = CARRIER_WIDTH


@dataclass(frozen=True)
class OutputFrame:
    identity_anchor: int
    provenance_anchor: int
    sequence: int
    payload: int
    carrier_width: int
    checksum: int


@dataclass(frozen=True)
class CycleResult:
    status: str
    stage: str
    reason: str
    proposal: Optional[str] = None
    output: Optional[OutputFrame] = None
    receipts: tuple[str, ...] = ()


@dataclass
class PosiRuntime:
    expected_sequence: int = 1
    seen_fingerprints: set[tuple[int, int, int, int, int]] = field(
        default_factory=set
    )
    state_window: list[int] = field(default_factory=list)
    active: bool = False

    @staticmethod
    def checksum(
        identity_anchor: int,
        provenance_anchor: int,
        sequence: int,
        payload: int,
    ) -> int:
        return (
            identity_anchor + provenance_anchor + sequence + payload
        ) % REGISTER_SIZE

    @staticmethod
    def fingerprint(packet: InputPacket) -> tuple[int, int, int, int, int]:
        return (
            packet.identity_anchor,
            packet.provenance_anchor,
            packet.sequence,
            packet.payload,
            packet.checksum,
        )

    @staticmethod
    def halted(stage: str, reason: str) -> CycleResult:
        return CycleResult(status="halted", stage=stage, reason=reason)

    def run_cycle(
        self,
        packet: InputPacket,
        *,
        left_sentinel: bool = True,
        right_sentinel: bool = True,
    ) -> CycleResult:
        """Run exactly one bounded cycle and return its auditable result."""
        self.active = True
        receipts: list[str] = []

        ingress_failure = self._check_ingress(packet)
        if ingress_failure is not None:
            self.active = False
            return self.halted("ingress", ingress_failure)

        packet_fingerprint = self.fingerprint(packet)
        self.seen_fingerprints.add(packet_fingerprint)
        receipts.append("ingress")

        snapshot = tuple(self.state_window)
        self.state_window.append(packet.payload)
        if len(self.state_window) > 8:
            self.state_window[:] = list(snapshot)
            self.active = False
            return self.halted("state", "state_window_capacity")
        receipts.append("state")

        if packet.payload < HOMEOSTATIC_ANCHOR:
            proposal = "increase"
            candidate = packet.payload + 1
        elif packet.payload > HOMEOSTATIC_ANCHOR:
            proposal = "decrease"
            candidate = packet.payload - 1
        else:
            proposal = "hold"
            candidate = packet.payload

        if abs(candidate - packet.payload) > 1:
            self.state_window[:] = list(snapshot)
            self.active = False
            return self.halted("cognition", "one_step_bound")
        receipts.append("cognition")

        if not (left_sentinel and right_sentinel):
            self.state_window[:] = list(snapshot)
            self.active = False
            return self.halted("governance", "dual_sentinel_quorum")
        receipts.append("governance")

        output = OutputFrame(
            identity_anchor=IDENTITY_ANCHOR,
            provenance_anchor=PROVENANCE_ANCHOR,
            sequence=packet.sequence,
            payload=candidate,
            carrier_width=CARRIER_WIDTH,
            checksum=self.checksum(
                IDENTITY_ANCHOR,
                PROVENANCE_ANCHOR,
                packet.sequence,
                candidate,
            ),
        )
        receipts.append("egress")

        self.expected_sequence += 1
        self.active = False
        return CycleResult(
            status="emitted",
            stage="complete",
            reason="cycle_closed",
            proposal=proposal,
            output=output,
            receipts=tuple(receipts),
        )

    def _check_ingress(self, packet: InputPacket) -> Optional[str]:
        if packet.identity_anchor != IDENTITY_ANCHOR:
            return "identity_anchor"
        if packet.provenance_anchor != PROVENANCE_ANCHOR:
            return "provenance_anchor"
        if not packet.coherent:
            return "incoherent"
        if not (0 <= packet.payload < REGISTER_SIZE):
            return "payload_bound"
        if not packet.carrier_present or packet.carrier_width != CARRIER_WIDTH:
            return "carrier_gate"
        if self.fingerprint(packet) in self.seen_fingerprints:
            return "duplicate_packet"
        if packet.sequence != self.expected_sequence:
            return "sequence_alignment"
        expected_checksum = self.checksum(
            packet.identity_anchor,
            packet.provenance_anchor,
            packet.sequence,
            packet.payload,
        )
        if packet.checksum != expected_checksum:
            return "integrity_checksum"
        return None


def packet(
    payload: int = 41,
    *,
    identity_anchor: int = IDENTITY_ANCHOR,
    provenance_anchor: int = PROVENANCE_ANCHOR,
    sequence: int = 1,
    coherent: bool = True,
    carrier_present: bool = True,
    carrier_width: int = CARRIER_WIDTH,
    checksum: Optional[int] = None,
) -> InputPacket:
    actual_checksum = (
        PosiRuntime.checksum(
            identity_anchor, provenance_anchor, sequence, payload
        )
        if checksum is None
        else checksum
    )
    return InputPacket(
        identity_anchor=identity_anchor,
        provenance_anchor=provenance_anchor,
        sequence=sequence,
        payload=payload,
        checksum=actual_checksum,
        coherent=coherent,
        carrier_present=carrier_present,
        carrier_width=carrier_width,
    )


def run_self_test() -> dict[str, object]:
    tests: dict[str, bool] = {}

    valid_runtime = PosiRuntime()
    valid = valid_runtime.run_cycle(packet())
    tests["valid_cycle"] = (
        valid.status == "emitted"
        and valid.proposal == "increase"
        and valid.output is not None
        and valid.output.payload == HOMEOSTATIC_ANCHOR
        and valid.receipts
        == ("ingress", "state", "cognition", "governance", "egress")
        and valid_runtime.active is False
    )

    tests["wrong_identity"] = (
        PosiRuntime().run_cycle(packet(identity_anchor=18)).reason
        == "identity_anchor"
    )
    tests["wrong_provenance"] = (
        PosiRuntime().run_cycle(packet(provenance_anchor=130)).reason
        == "provenance_anchor"
    )
    tests["incoherent"] = (
        PosiRuntime().run_cycle(packet(coherent=False)).reason == "incoherent"
    )
    tests["oversized_payload"] = (
        PosiRuntime().run_cycle(packet(payload=256)).reason == "payload_bound"
    )
    tests["bad_checksum"] = (
        PosiRuntime().run_cycle(packet(checksum=0)).reason
        == "integrity_checksum"
    )
    tests["sentinel_denial"] = (
        PosiRuntime().run_cycle(packet(), right_sentinel=False).reason
        == "dual_sentinel_quorum"
    )

    replay_runtime = PosiRuntime()
    replay_packet = packet()
    first = replay_runtime.run_cycle(replay_packet)
    replay = replay_runtime.run_cycle(replay_packet)
    tests["duplicate_replay"] = (
        first.status == "emitted" and replay.reason == "duplicate_packet"
    )

    if not all(tests.values()):
        failed = [name for name, passed in tests.items() if not passed]
        raise AssertionError(f"R001 failed: {failed}")

    return {
        "chonk": "R001",
        "status": "PASS",
        "tests_passed": sum(tests.values()),
        "tests_total": len(tests),
        "valid_result": asdict(valid),
        "rejections": [
            "identity_anchor",
            "provenance_anchor",
            "incoherent",
            "payload_bound",
            "integrity_checksum",
            "dual_sentinel_quorum",
            "duplicate_packet",
        ],
        "network": "disabled",
    }


if __name__ == "__main__":
    print(json.dumps(run_self_test(), indent=2, sort_keys=True))
