# Phase-1 fault-injection model

This folder adds a **reproducible nonce-ID state simulation**, not a working FROST signing implementation.

## Reproduce

Python 3.10+ with the standard library; no pip dependencies.

    cd experiments
    python -m unittest -v
    python run_matrix.py

10 deterministic tests and 5 scenario experiments cover:
- Unsafe exposure-before-persist crash window
- Atomic claim, restart, and a 16-way thread race
- Primary database snapshot rollback
- Independent witness ledger blocking one-sided rollback
- Fail-closed crash after witness reservation
- **Limitation**: restoring both primary and witness state permits replay

## Architecture and assumptions

A primary SQLite database marks opaque nonce identifiers burned.
The independent witness is a second SQLite database stored **outside**
the primary database's failure/rollback domain. It reserves identifiers
durably before the primary is updated. Failure after external reservation
sacrifices availability (burned IDs may become unusable), not safety.

This is not by itself distributed consensus or a real monotonic hardware
counter. In real deployments an attacker who can roll back both databases
defeats the modeled protection. This test is **not proof of cryptographic
security**. No secret signing nonces, key shares, or FROST signatures exist.
The simplistic mark-after-use sequence is an intentionally unsafe baseline.

## Project scope

To be implemented: vetted RFC 9591 library and 2-of-3 signing testbed;
real crash termination and recovery; multi-process fault harness;
benchmarks with repeatable methodology. Do not deploy this model for signing.
