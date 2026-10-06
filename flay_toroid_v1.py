#!/usr/bin/env python3
"""Local adoption of FLAY Mandel-Juliet Toroid v1."""

from dataclasses import dataclass, field
from enum import IntEnum


class State(IntEnum):
    QUESTION = -1
    ROOT = 0
    CLOSED = 1


@dataclass(frozen=True)
class Fact:
    what: str
    who: str = ""
    when: str = ""
    where: str = ""
    evidence: str = ""


@dataclass
class Mandel:
    answers: list[str] = field(default_factory=list)
    facts: list[Fact] = field(default_factory=list)
    revision: int = 0


class Juliet:
    def __init__(self, mandel: Mandel, question: str):
        if not question.strip():
            raise ValueError("question required")
        self.mandel = mandel
        self.question = question.strip()
        self.state = State.QUESTION
        self.answer_text = None
        self.facts = ()
        self.resolved = False

    def open(self):
        if self.state != State.QUESTION:
            raise RuntimeError("excursion cannot reopen")
        self.state = State.ROOT
        return self

    def answer(self, text: str, facts=(), resolved=True):
        if self.state != State.ROOT:
            raise RuntimeError("answer requires open excursion")
        if not text.strip():
            raise ValueError("answer required")
        self.answer_text = text.strip()
        self.facts = tuple(facts)
        self.resolved = bool(resolved)
        return self

    def close(self):
        if self.state != State.ROOT:
            raise RuntimeError("close requires open excursion")
        if self.answer_text is None or not self.resolved:
            raise RuntimeError("resolved answer required")
        self.mandel.answers.append(self.answer_text)
        self.mandel.facts.extend(self.facts)
        self.mandel.revision += 1
        self.state = State.CLOSED
        return self.answer_text


def _self_test():
    m = Mandel()
    j = Juliet(m, "What happened?").open()
    j.answer("Supported answer.", [Fact("event", evidence="source")])
    assert j.close() == "Supported answer."
    assert j.state == State.CLOSED
    assert m.revision == 1
    assert len(m.facts) == 1
    try:
        j.open()
    except RuntimeError:
        pass
    else:
        raise AssertionError("closed Juliet reopened")
    print("0e / FLAY MANDEL-JULIET TOROID v1 LOCAL PASS")


if __name__ == "__main__":
    _self_test()
