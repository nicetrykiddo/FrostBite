# FROSTBITE

**Crash-Safe Nonce Use in FROST Threshold Signatures**

B.Tech research project | NIIT University | 26 October 2026

## Research question

Can a pre-generated FROST nonce pair be reused after a crash, concurrent retry, or restoration of an older database snapshot?

## Current status

- Research scope, literature review, goals and fault-injection plan outlined.
- Phase-0: small SQLite-based **nonce identifier** lifecycle simulation and tests.
- **Not implemented:** a full 2-of-3 FROST cryptographic signer, integrated fault-injection harness, production-grade protection, or performance benchmarks.

The simulation uses opaque IDs, **not FROST nonces or keys**. It cannot be used for real cryptographic systems.

## Run demo

```sh
python3 -m unittest -v
```

No external dependencies. Tests check a first claim, replay rejection, concurrent claims, persistence across restart, and the known limitation of a stale DB snapshot.

## Planned milestones

1. Integrate a vetted RFC 9591 FROST library in a local 2-of-3 testbed.
2. Implement persistent nonce pair lifecycle and reference unsafe baseline.
3. Inject crashes, retries, races, and database snapshot rollback.
4. Evaluate transaction-based burn-before-use and independent monotonic/witness logging.
5. Measure reuse violations, successful signatures, latency, storage overhead, and recovery.

## Sources

- [RFC 9591](https://www.rfc-editor.org/rfc/rfc9591)
- [FROST (2020)](https://eprint.iacr.org/2020/852)
- [Arctic (2024)](https://eprint.iacr.org/2024/466)

**This is research/test code, not a security-reviewed signing system.**
