# OaSIs AE v179 witness bridge

**NOMCOG additive bridge — Posi v00.01 remains immutable.**

This directory verifies OaSIs AE Witness-Generative v179 receipts locally.

## Boundary

    OaSIs v179 receipt JSON
             |
             v
    NOMCOG local verifier
             |
       +-----+------+
       |            |
      PASS        REJECT
       |            |
    witness      no state change

The verifier:

- performs no network access;
- does not edit Posi v00.01;
- validates receipt ID and receipt seal;
- enforces identity anchor 17;
- enforces provenance anchor 131;
- enforces network = disabled;
- enforces Posi v00.01 stable/frozen witnesses;
- preserves UNBOUND lane mappings;
- rejects a BOUND receipt unless lane class equals the mathematical orbit class;
- validates /0/0 only when the source state is halted;
- can verify a hash-linked receipt chain.

## Run

    python verifier.py --self-test

Verify one local receipt:

    python verifier.py receipt.json

Verify a JSON array of receipts as a chain:

    python verifier.py receipts.json

## OaSIs peer

Public page:

    https://davidwise01.github.io/oasis/architecture/ae-generative-v179/

Source:

    https://github.com/DavidWise01/oasis/tree/main/kernel/generative/ae-witness-v179

The bridge is a witness/provenance interface, not merged authority.
