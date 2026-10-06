# FLAY Mandel-Juliet Toroid v1 — nom

Status: APPEND-ONLY LOCAL ADOPTION  
Canonical source: `DavidWise01/toph-cortex@99dfacadb97b2469e9d5ee307f67f0a144bfac9d`

This node adopts the shared FLAY reasoning excursion without expanding local authority.

## Primitive

```
MANDEL ? -> JULIET -> ANSWER -> MANDEL'
OPEN -> ANSWER -> CLOSE
```

Ternary scope:

```
-1 = question / unresolved opening
 0 = local root / referent reached for this excursion
+1 = supported closure bound back to Mandel
```

One question opens one Juliet tangent. Juliet is temporary scratch/work space while remaining bound to Mandel. It may use WHY to walk backward, compare evidence, and resolve the question. On close it retains only the answer and important supported facts.

## Provenance rule

Backward search may use:

```
WHY -> WHO -> WHY -> WHO -> ... -> 0
```

The retained forward ledger is factual:

```
0
-> WHAT HAPPENED?
-> WHAT :: WHO :: WHEN :: WHERE :: EVIDENCE
-> WHAT HAPPENED NEXT?
-> ...
-> +1
```

Do not store conjectural WHY as historical fact.

## Anomaly / counterfactual rule

If WHAT HAPPENED does not fit the supported chain:

```
anomaly
-> . WHY?
-> walk backward to a supported divergence
-> record ACTUAL
-> derive EXPECTED under the selected rule
-> simulate COUNTERFACTUAL
```

ACTUAL, EXPECTED, and COUNTERFACTUAL remain distinct. A counterfactual never rewrites the actual ledger.

## Close invariant

A local excursion may close only with a resolved answer. Closing:

1. binds the answer back to Mandel,
2. appends supported facts,
3. advances the local revision,
4. moves the excursion to +1,
5. permanently closes that excursion.

New evidence opens a new excursion. Closed history is append-only.

Compact carrier:

```
M ? -> J(-1) -> OPEN(0) -> ANSWER -> CLOSE(+1) -> M'
```

One question. One open. One answer. One close.
