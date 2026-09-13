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
