"""Failure scenario tests: cd experiments && python -m unittest -v"""
import concurrent.futures
from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path
from fault_model import NoncePool, IndependentWitness, claim_with_witness

def snapshot(src, dst):
    with closing(sqlite3.connect(src)) as source, closing(sqlite3.connect(dst)) as target:
        source.backup(target)

class FaultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp.name)
        self.pool = NoncePool(self.dir/'pool.db')
        self.witness = IndependentWitness(self.dir/'witness.db')
        self.identifier = self.pool.issue()

    def tearDown(self):
        self.temp.cleanup()

    def test_01_unsafe_crash_before_burn_allows_reuse(self):
        self.assertTrue(self.pool.claim_unsafe(self.identifier, 'A', crash_after_exposure=True))
        self.assertTrue(self.pool.claim_unsafe(self.identifier, 'B'))

    def test_02_atomic_no_duplicate(self):
        self.assertTrue(self.pool.claim_atomic(self.identifier, 'A'))
        self.assertFalse(self.pool.claim_atomic(self.identifier, 'B'))

    def test_03_atomic_survives_restart(self):
        self.assertTrue(self.pool.claim_atomic(self.identifier, 'A'))
        self.assertFalse(NoncePool(self.pool.path).claim_atomic(self.identifier, 'B'))

    def test_04_atomic_16_way_race_one_winner(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            outcomes = list(executor.map(lambda x: self.pool.claim_atomic(self.identifier, str(x)), range(16)))
        self.assertEqual(sum(outcomes), 1)

    def test_05_atomic_snapshot_restore_allows_reuse(self):
        old = self.dir/'old-pool.db'
        snapshot(self.pool.path, old)
        self.assertTrue(self.pool.claim_atomic(self.identifier, 'A'))
        self.assertTrue(NoncePool(old).claim_atomic(self.identifier, 'B'))

    def test_06_external_witness_blocks_pool_snapshot_replay(self):
        old = self.dir/'old-pool.db'
        snapshot(self.pool.path, old)
        self.assertTrue(claim_with_witness(self.pool, self.witness, self.identifier, 'A'))
        self.assertFalse(claim_with_witness(NoncePool(old), self.witness, self.identifier, 'B'))

    def test_07_witness_crash_after_reservation_fails_closed(self):
        self.assertFalse(claim_with_witness(self.pool, self.witness, self.identifier, 'A', fault_after_reservation=True))
        self.assertFalse(claim_with_witness(self.pool, self.witness, self.identifier, 'B'))

    def test_08_witness_db_rollback_breaks_assumption(self):
        old_pool = self.dir/'old-pool.db'
        old_witness = self.dir/'old-witness.db'
        snapshot(self.pool.path, old_pool)
        snapshot(self.witness.path, old_witness)
        self.assertTrue(claim_with_witness(self.pool, self.witness, self.identifier, 'A'))
        self.assertTrue(claim_with_witness(NoncePool(old_pool), IndependentWitness(old_witness), self.identifier, 'B'))

    def test_09_unknown_nonce_rejected(self):
        self.assertFalse(self.pool.claim_atomic('not-issued', 'A'))
        self.assertFalse(claim_with_witness(self.pool, self.witness, 'not-issued', 'B'))

    def test_10_no_pool_mutation_after_fault_before_local_burn(self):
        self.assertFalse(claim_with_witness(self.pool, self.witness, self.identifier, 'A', fault_after_reservation=True))
        self.assertEqual(self.pool.get(self.identifier), ('available', None))
        self.assertFalse(claim_with_witness(self.pool, self.witness, self.identifier, 'B'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
