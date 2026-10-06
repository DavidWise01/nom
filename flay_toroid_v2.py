#!/usr/bin/env python3
"""FLAY Mandel-Juliet Toroid v2.

Canonical realignment:
- exactly three temporal substrates: PAST / PRESENT / FUTURE
- one question = one OPEN -> ANSWER -> CLOSE toroid
- PAST is archive, not truth by default
- PRESENT is the only realization boundary
- FUTURE is Juliet scratchpad
- 33/33/33/+1 observer closure witness
- close locks vector, G=1, local T=0, branches frozen
- factual provenance edges classify inheritance / independent discovery /
  happenstance / unknown
- actual, expected, and counterfactual remain separate
"""

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from fractions import Fraction
from typing import Iterable, Tuple


class Ternary(IntEnum):
    QUESTION = -1
    ROOT = 0
    CLOSED = 1


class TemporalSubstrate(str, Enum):
    PAST = "past"
    PRESENT = "present"
    FUTURE = "future"


class Relation(str, Enum):
    DOCUMENTED_INHERITANCE = "documented_inheritance"
    INDEPENDENT_DISCOVERY = "independent_discovery"
    HAPPENSTANCE = "happenstance"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Fact:
    what: str
    who: str = ""
    when: str = ""
    where: str = ""
    evidence: str = ""


@dataclass(frozen=True)
class Link:
    source: Fact
    target: Fact
    relation: Relation
    evidence: str = ""


@dataclass(frozen=True)
class Answer:
    actual: str
    facts: Tuple[Fact, ...] = ()
    links: Tuple[Link, ...] = ()
    expected: str | None = None
    counterfactual: str | None = None
    resolved: bool = True


@dataclass(frozen=True)
class ClosureWitness:
    exact_a: Fraction = Fraction(1, 3)
    exact_b: Fraction = Fraction(1, 3)
    exact_c: Fraction = Fraction(1, 3)
    display_a: int = 33
    display_b: int = 33
    display_c: int = 33
    observer: int = 1
    vector_locked: bool = True
    gravity: int = 1
    local_time: int = 0
    branches_frozen: bool = True

    @property
    def exact_balanced(self) -> bool:
        return self.exact_a + self.exact_b + self.exact_c == 1

    @property
    def display_balanced(self) -> bool:
        return self.display_a + self.display_b + self.display_c + self.observer == 100

    @property
    def balanced_to_one(self) -> bool:
        return self.exact_balanced and self.display_balanced


@dataclass(frozen=True)
class ArchiveEntry:
    question: str
    answer: Answer
    witness: ClosureWitness
    substrate: TemporalSubstrate = TemporalSubstrate.PAST


@dataclass
class Mandel:
    """Bound corpus state. Archive is append-only; archive != truth."""

    archive: list[ArchiveEntry] = field(default_factory=list)
    revision: int = 0

    def bind(self, entry: ArchiveEntry) -> None:
        if entry.substrate is not TemporalSubstrate.PAST:
            raise ValueError("closed entries must bind into PAST archive")
        if not entry.answer.resolved:
            raise ValueError("unresolved answer cannot enter archive")
        if not entry.witness.balanced_to_one:
            raise ValueError("closure witness did not balance to one")
        self.archive.append(entry)
        self.revision += 1


class Juliet:
    """One-shot FUTURE scratchpad bound to Mandel."""

    substrate = TemporalSubstrate.FUTURE

    def __init__(self, mandel: Mandel, question: str):
        question = question.strip()
        if not question:
            raise ValueError("question required")
        self.mandel = mandel
        self.question = question
        self.state = Ternary.QUESTION
        self._answer: Answer | None = None
        self._closed = False

    def open(self) -> "Juliet":
        if self._closed:
            raise RuntimeError("closed excursion")
        if self.state != Ternary.QUESTION:
            raise RuntimeError("excursion already opened")
        self.state = Ternary.ROOT
        return self

    def answer(
        self,
        actual: str,
        facts: Iterable[Fact] = (),
        links: Iterable[Link] = (),
        *,
        expected: str | None = None,
        counterfactual: str | None = None,
        resolved: bool = True,
    ) -> Answer:
        if self.state != Ternary.ROOT or self._closed:
            raise RuntimeError("answer requires one open excursion")
        actual = actual.strip()
        if not actual:
            raise ValueError("actual answer required")
        self._answer = Answer(
            actual=actual,
            facts=tuple(facts),
            links=tuple(links),
            expected=expected,
            counterfactual=counterfactual,
            resolved=resolved,
        )
        return self._answer

    def close(self, witness: ClosureWitness | None = None) -> ArchiveEntry:
        """PRESENT realization gate: the only operation that commits to PAST."""
        if self.state != Ternary.ROOT or self._closed:
            raise RuntimeError("close requires one open excursion")
        if self._answer is None:
            raise RuntimeError("cannot close without an answer")
        if not self._answer.resolved:
            raise RuntimeError("unresolved answer cannot close")

        witness = witness or ClosureWitness()
        if not witness.balanced_to_one:
            raise RuntimeError("observer cannot close an unbalanced whole")

        entry = ArchiveEntry(
            question=self.question,
            answer=self._answer,
            witness=witness,
        )
        self.mandel.bind(entry)
        self.state = Ternary.CLOSED
        self._closed = True
        return entry


def excursion(
    mandel: Mandel,
    question: str,
    actual: str,
    facts: Iterable[Fact] = (),
    links: Iterable[Link] = (),
    *,
    expected: str | None = None,
    counterfactual: str | None = None,
) -> ArchiveEntry:
    juliet = Juliet(mandel, question).open()
    juliet.answer(
        actual,
        facts,
        links,
        expected=expected,
        counterfactual=counterfactual,
    )
    return juliet.close()


if __name__ == "__main__":
    m = Mandel()
    excursion(
        m,
        "What happened?",
        "A supported event entered the archive.",
        [Fact(what="supported event", evidence="demo")],
    )
    assert m.revision == 1
    print("0e / FLAY MANDEL-JULIET TOROID v2 PASS")
