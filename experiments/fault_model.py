"""FROSTBITE phase-1 failure model. Non-secret IDs only, NOT a FROST signer.

The witness is a separate durable database. Its benefit assumes it cannot
be rolled back together with the primary database.
"""
from contextlib import contextmanager
from pathlib import Path
import secrets
import sqlite3

@contextmanager
def connect(path):
    db = sqlite3.connect(str(path), isolation_level=None, timeout=10)
    try:
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("PRAGMA synchronous=FULL")
        db.execute("PRAGMA journal_mode=WAL")
        yield db
    finally:
        db.close()

class NoncePool:
    def __init__(self, path):
        self.path = Path(path)
        with connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS nonces (id TEXT PRIMARY KEY, state TEXT NOT NULL CHECK (state IN ('available','burned')), context TEXT)")

    def issue(self):
        identifier = secrets.token_hex(16)
        with connect(self.path) as db:
            db.execute("INSERT INTO nonces VALUES (?, 'available', NULL)", (identifier,))
        return identifier

    def get(self, identifier):
        with connect(self.path) as db:
            return db.execute("SELECT state,context FROM nonces WHERE id=?", (identifier,)).fetchone()

    def claim_atomic(self, identifier, context):
        with connect(self.path) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                cur = db.execute("UPDATE nonces SET state='burned',context=? WHERE id=? AND state='available'", (context, identifier))
                db.execute("COMMIT")
                return cur.rowcount == 1
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def claim_unsafe(self, identifier, context, crash_after_exposure=False):
        """Illustrative flaw: return nonce ID before persisting its burn."""
        with connect(self.path) as db:
            row = db.execute("SELECT state FROM nonces WHERE id=?", (identifier,)).fetchone()
            if row != ('available',):
                return False
            if crash_after_exposure:
                return True  # simulated crash after exposure; burn never persisted
            db.execute("UPDATE nonces SET state='burned',context=? WHERE id=?", (context, identifier))
            return True

class IndependentWitness:
    def __init__(self, path):
        self.path = Path(path)
        with connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS claims (id TEXT PRIMARY KEY, context TEXT NOT NULL)")

    def reserve(self, identifier, context):
        with connect(self.path) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                cur = db.execute("INSERT OR IGNORE INTO claims (id,context) VALUES (?,?)", (identifier, context))
                db.execute("COMMIT")
                return cur.rowcount == 1
            except BaseException:
                db.execute("ROLLBACK")
                raise

def claim_with_witness(pool, witness, identifier, context, fault_after_reservation=False):
    """Reserve externally before local burn; fail closed after partial failure.

    Simplified protocol-state simulation, NOT a cryptographic security proof.
    """
    if pool.get(identifier) != ('available', None):
        return False
    if not witness.reserve(identifier, context):
        return False
    if fault_after_reservation:
        return False
    return pool.claim_atomic(identifier, context)
