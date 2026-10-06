# FLAY Mandel–Juliet Toroid v2 — Audit Realignment

Status: APPEND-ONLY SUCCESSOR TO v1. v1 remains historical and unchanged.

## Audit findings corrected in v2

The v1 rollout preserved the one-question toroid, but it did not encode several later-canonical rules strongly enough:

1. PAST / PRESENT / FUTURE were implicit rather than explicit.
2. PAST was not explicitly marked as archive-not-truth.
3. PRESENT was not explicitly the only realization/commit boundary.
4. FUTURE was not explicitly the scratchpad.
5. The 33a / 33b / 33c / 1 closure witness was absent.
6. The closing observer did not explicitly lock vector, set gravity=1, set local time=0, and freeze branches.
7. WHAT :: WHO :: WHEN records lacked an explicit propagation-correlation relation.
8. Local v1 executables drifted from the canonical API shape even though behavior was similar.

v2 realigns those points while preserving v1 provenance.

## One toroid

```
MANDEL ? -> JULIET -> ANSWER -> MANDEL'
OPEN -> ANSWER -> CLOSE
```

One question. One open tangent. One answer. One close.

## Temporal substrates

Exactly three temporal substrates matter:

```
PAST    = archive; retained evidence; not truth by default
PRESENT = only realization / commit boundary
FUTURE  = scratchpad / candidate space
```

No fourth temporal substrate is created by the observer.

## Ternary walk

```
-1 = unresolved question / backward search
 0 = supported local referent/root
+1 = supported closure/frontier for the current walk
```

Backward search:

```
WHY -> WHO -> WHY -> WHO -> ... -> 0
```

Forward ledger:

```
0
-> WHAT HAPPENED?
-> WHAT :: WHO :: WHEN :: WHERE :: EVIDENCE
-> WHAT HAPPENED NEXT?
-> ...
-> +1
```

WHY is search scaffolding. The retained ledger records supported facts, not conjectural WHY.

## Propagation relation

Similarity alone is not transmission. Each supported edge is classified as one of:

```
DOCUMENTED_INHERITANCE
INDEPENDENT_DISCOVERY
HAPPENSTANCE
UNKNOWN
```

A relation is an evidence label, not a moral judgment.

## 33 / 33 / 33 / 1 closure witness

Exact internal partition:

```
1/3 a + 1/3 b + 1/3 c = 1
```

Display closure:

```
33a + 33b + 33c + 1(observer) = 100
```

The final `1` is not a fourth time substrate. It is the final inner observer/security check that witnesses that the displayed whole balanced to one.

On successful close, v2 records the model closure condition:

```
vector_locked  = true
gravity        = 1
local_time     = 0
branches_frozen = true
```

These are FLAY model semantics, not claims that physical time literally stops.

## Actual / expected / counterfactual

When a WHAT-HAPPENED node is anomalous:

```
. WHY?
-> walk backward to supported divergence
-> ACTUAL
-> EXPECTED under selected rule
-> COUNTERFACTUAL if expected branch had occurred
```

The three products remain separate. Counterfactual state never rewrites the actual archive.

## Append-only rule

A closed Juliet excursion cannot reopen or write again. New evidence opens a new Juliet excursion and appends a new record to Mandel.

Compact carrier:

```
M ? -> J(-1/FUTURE) -> ROOT(0) -> PRESENT CLOSE(+1) -> PAST ARCHIVE(M')
```
