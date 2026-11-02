# FROSTBITE
**Crash-Safe Nonce Management in FROST Threshold Signatures**

B.Tech cryptography research | NIIT University | Research progress: 2 November 2026

## Question
When an application using pre-generated FROST signing nonces crashes, retries, or restores an old database, can the same nonce be incorrectly used again?

## Current implementation
- **Phase 0**: SQLite model of opaque nonce IDs (available → burned), with basic unit tests.
- **Phase 1**: [Fault-injection model](experiments/README.md) comparing an intentionally unsafe mark-after-exposure sequence, atomic burn-before-use, rollback of a primary DB, and a separately durable witness.
- **Executed evidence (2 November 2026)**: 10/10 new deterministic tests passed, including a 16-contender race; 5 scenario experiments. See [reproducible results](experiments/results_2026-11-02.json).

Run:
```bash
cd experiments
python -m unittest -v
python run_matrix.py
```

Requires Python 3.10+ and the standard library only. See [experiment assumptions and limitations](experiments/README.md).

### Main observed limitation
Atomic transactions block ordinary duplicate claims, but restoring an older snapshot can revive nonce identifiers. A witness in an independent rollback domain rejects the observed primary-only rollback case, **but not rollback of both databases**.

## Not yet implemented
A real FROST signer, cryptographic nonce material, a vetted RFC 9591 signing integration, end-to-end process crash tests, multi-machine durability, or performance benchmarks.

**WARNING: simulation only; do not use for securing real keys, signatures or wallets.**

## References
1. [RFC 9591](https://www.rfc-editor.org/rfc/rfc9591)
2. [FROST (2020)](https://eprint.iacr.org/2020/852)
3. [Arctic (2024)](https://eprint.iacr.org/2024/466)
