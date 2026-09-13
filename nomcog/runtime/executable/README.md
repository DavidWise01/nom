# NOMCOG executable runtime

This directory is the canonical executable body layered beneath the frozen
NOMCOG cognitive specification and its Lean runtime closure.

## Closed path

```text
Ingress -> State -> Cognition -> Governance -> Egress
```

The executable body is local-only and deterministic:

- identity anchor: `17`
- provenance anchor: `131`
- register: `0..255`
- carrier width: `4`
- session capacity: `8`
- scheduler: FIFO, single writer
- fault convergence: circuit opens after `3` consecutive faults
- recovery: explicit, dual-sentinel, checkpoint-bound
- network: disabled

## Frozen chonks

| Chonk | Function | Status |
|---|---|---|
| R001 | Five-stage executable cycle | frozen |
| R002 | Bounded transactional session | frozen |
| R003 | Append-only hash-linked audit journal | frozen |
| R004 | Exact checkpoint recovery | frozen |
| R005 | Atomic local checkpoint persistence | frozen |
| R006 | Governed local control boundary | frozen |
| R007 | Deterministic single-writer scheduler | frozen |
| R008 | Fault convergence and circuit halt | frozen |
| R009 | Witnessed controlled recovery | frozen |
| R010 | Dependency seal and executable capstone | frozen |

## Machine check

Place all ten Python files in one directory and run:

```powershell
python .\nomcog_r010_executable_capstone.py
$LASTEXITCODE
```

Canonical result:

- 9 of 9 dependency hashes verified
- 68 component tests passed
- 7 integrated checks passed
- 75 total tests passed
- exit code `0`

`manifest.json` is the canonical hash and verification register. R001 through
R010 are append-only frozen artifacts; later work belongs in new files.
