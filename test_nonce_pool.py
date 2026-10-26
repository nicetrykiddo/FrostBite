"""Run: python3 -m unittest -v"""
import concurrent.futures
import sqlite3
import tempfile
import unittest
from pathlib import Path

from nonce_pool import NoncePool


class NonceLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'nonces.sqlite'
        self.pool = NoncePool(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_first_claim_succeeds(self):
        n = self.pool.issue_id()
        self.assertTrue(self.pool.burn_before_use(n, 'message-A'))
        self.assertEqual(self.pool.get_state(n), ('burned', 'message-A'))

    def test_duplicate_claim_rejected(self):
        n = self.pool.issue_id()
        self.assertTrue(self.pool.burn_before_use(n, 'message-A'))
        self.assertFalse(self.pool.burn_before_use(n, 'message-B'))

    def test_race_only_one_claims(self):
        n = self.pool.issue_id()
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
            answers = list(ex.map(
                lambda i: self.pool.burn_before_use(n, f'message-{i}'), range(12)
            ))
        self.assertEqual(sum(answers), 1)

    def test_restart_does_not_unburn(self):
        n = self.pool.issue_id()
        self.assertTrue(self.pool.burn_before_use(n, 'message-A'))
        recovered = NoncePool(self.path)
        self.assertFalse(recovered.burn_before_use(n, 'message-B'))

    def test_old_snapshot_reopens_burned_id_expected_limit(self):
        n = self.pool.issue_id()
        snapshot = Path(self.tmp.name) / 'old.sqlite'
        with sqlite3.connect(self.path) as db:
            with sqlite3.connect(snapshot) as old:
                db.backup(old)
        self.assertTrue(self.pool.burn_before_use(n, 'message-A'))
        restored = NoncePool(snapshot)
        # Known limitation: an earlier snapshot revives the ID.
        self.assertTrue(restored.burn_before_use(n, 'message-B'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
