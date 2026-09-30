# NOMCOG

NOMCOG is the bounded cognitive layer for **nom**.

The frozen six-stage path is:

| Stage | Function | Status |
|---|---|---|
| N | Attention | frozen |
| O | Observation | frozen |
| M | Memory | frozen |
| C | Cognition | frozen |
| O | Orchestration | frozen |
| G | Governance | frozen |

The original nom remains unchanged: two source doors, citation-only output, and an append-only ledger. NOMCOG is an additive module layered above that substrate.

## Boundary

```
Exterior -> Cortex -> Core
Exterior <- Cortex
Direct Exterior/Core access: denied
```

Governance requires:

1. valid identity and provenance;
2. closed orchestration;
3. Cortex routing;
4. explicit policy permission;
5. dual-sentinel agreement;
6. a complete, recorded audit receipt.

Any failed condition halts the path.

## Formal machine check

Run the standalone Lean manifest:

```powershell
cd "$HOME\Downloads"
lean .\nomcog_final_freeze_manifest.lean
$LASTEXITCODE
```

Expected output ends with exit code `0`.

## Executable runtime

The canonical local-only executable body is in
[`nomcog/runtime/executable/`](runtime/executable/).

It contains frozen chonks R001 through R010, their SHA-256 manifest, and the
75-test executable capstone.

```powershell
python .\nomcog_r010_executable_capstone.py
$LASTEXITCODE
```

Canonical result: 9 dependency hashes verified, 68 component tests passed,
7 integrated checks passed, and exit code `0`.

## OaSIs tether

NOMCOG is reciprocally tethered to the OaSIs **AE Hierarchical Generative Kernel v178**.

- Public page: https://davidwise01.github.io/oasis/architecture/ae-generative-v178/
- OaSIs kernel: https://github.com/DavidWise01/oasis/tree/main/kernel/generative/ae-hierarchical-v178
- OaSIs witness commit: `094bcff5f9ff9dae2fc1baf22ed4597567a3bf28`
- Tether record: [`OASIS_TETHER_v178.json`](OASIS_TETHER_v178.json)

The tether is an identity/witness relation. It does **not** merge authority, rewrite NOM/Posi, or permit direct Exterior/Core access.


## OaSIs witness bridge v179

The reciprocal OaSIs tether now has a local verifier under:

    nomcog/bridges/oasis-v179/

It verifies AE v179 receipt IDs/seals, anchors 17/131, disabled network status, STOP coherence, and lane-binding coherence without modifying frozen Posi v00.01.

Public peer page:

    https://davidwise01.github.io/oasis/architecture/ae-generative-v179/
