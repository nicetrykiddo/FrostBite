"""FROSTBITE Phase-0 nonce lifecycle simulation.

Tracks non-secret nonce identifiers ONLY. Not a FROST implementation and
not suitable for production cryptographic keys, nonces or wallets.
"""
from __future__ import annotations

import secrets
import sqlite3
from pathlib import Path


class NoncePool:
    def __init__(self, path: str | Path):
        self.path = str(path)
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("""CREATE TABLE IF NOT EXISTS nonces (
                nonce_id TEXT PRIMARY KEY,
                state TEXT NOT NULL CHECK(state IN ('available', 'burned')),
                context TEXT
            )""")

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=5.0, isolation_level=None)
        db.execute("PRAGMA busy_timeout=5000")
        db.execute("PRAGMA synchronous=FULL")
        return db

    def issue_id(self) -> str:
        """Register an opaque test ID, not actual secret nonce material."""
        nonce_id = secrets.token_hex(16)
        with self._connect() as db:
            db.execute("INSERT INTO nonces VALUES (?, 'available', NULL)", (nonce_id,))
        return nonce_id

    def burn_before_use(self, nonce_id: str, signing_context: str) -> bool:
        """Atomically burn ID before any simulated use.

        Does NOT protect against older database snapshot restoration.
        """
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                cur = db.execute(
                    "UPDATE nonces SET state='burned', context=? "
                    "WHERE nonce_id=? AND state='available'",
                    (signing_context, nonce_id),
                )
                result = cur.rowcount == 1
                db.execute("COMMIT")
                return result
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def get_state(self, nonce_id: str):
        with self._connect() as db:
            return db.execute(
                "SELECT state, context FROM nonces WHERE nonce_id=?", (nonce_id,)
            ).fetchone()
