#!/usr/bin/env python3
from flay_toroid_v2 import (
    Answer,
    ClosureWitness,
    Fact,
    Juliet,
    Link,
    Mandel,
    Relation,
    TemporalSubstrate,
    Ternary,
    excursion,
)


def expect_raises(exc, fn):
    try:
        fn()
    except exc:
        return
    raise AssertionError(f"expected {exc.__name__}")


def main():
    # Exactly three temporal substrates.
    assert set(TemporalSubstrate) == {
        TemporalSubstrate.PAST,
        TemporalSubstrate.PRESENT,
        TemporalSubstrate.FUTURE,
    }

    # Closure math: exact thirds plus display observer.
    w = ClosureWitness()
    assert w.exact_balanced
    assert w.display_balanced
    assert w.balanced_to_one
    assert w.vector_locked
    assert w.gravity == 1
    assert w.local_time == 0
    assert w.branches_frozen

    # FUTURE scratchpad -> PRESENT close -> PAST archive.
    m = Mandel()
    j = Juliet(m, "What happened?")
    assert j.substrate is TemporalSubstrate.FUTURE
    assert j.state == Ternary.QUESTION
    j.open()
    assert j.state == Ternary.ROOT

    a = Fact("idea A", "source A", "t0", evidence="e0")
    b = Fact("idea B", "source B", "t1", evidence="e1")
    link = Link(a, b, Relation.DOCUMENTED_INHERITANCE, evidence="citation")

    j.answer(
        "B followed A with documented access.",
        [a, b],
        [link],
        expected="rule-relative expectation",
        counterfactual="simulated branch only",
    )
    entry = j.close()

    assert entry.substrate is TemporalSubstrate.PAST
    assert entry.answer.actual == "B followed A with documented access."
    assert entry.answer.expected == "rule-relative expectation"
    assert entry.answer.counterfactual == "simulated branch only"
    assert entry.answer.links[0].relation is Relation.DOCUMENTED_INHERITANCE
    assert m.revision == 1
    assert len(m.archive) == 1

    # Archive append does not imply truth; it records the closed evidence state.
    assert m.archive[0] == entry

    # Closed excursion is immutable.
    expect_raises(RuntimeError, j.open)
    expect_raises(RuntimeError, j.close)
    expect_raises(RuntimeError, lambda: j.answer("rewrite"))

    # Unanswered/unresolved branches do not realize.
    j2 = Juliet(m, "Why?").open()
    expect_raises(RuntimeError, j2.close)
    j2.answer("unknown", resolved=False)
    expect_raises(RuntimeError, j2.close)
    assert m.revision == 1

    # Bad observer balance cannot close.
    j3 = Juliet(m, "Balance?").open()
    j3.answer("candidate")
    bad = ClosureWitness(observer=0)
    expect_raises(RuntimeError, lambda: j3.close(bad))
    assert m.revision == 1

    # Independent/happenstance/unknown are distinct factual relation labels.
    assert Relation.INDEPENDENT_DISCOVERY != Relation.HAPPENSTANCE
    assert Relation.UNKNOWN != Relation.DOCUMENTED_INHERITANCE

    # New evidence opens a new toroid and appends.
    excursion(m, "What happened next?", "A second supported event.")
    assert m.revision == 2
    assert len(m.archive) == 2

    print("0e / FLAY MANDEL-JULIET TOROID v2 REALIGNMENT PASS")


if __name__ == "__main__":
    main()
