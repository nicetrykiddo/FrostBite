"""Reproduce five scenario outcomes: cd experiments && python run_matrix.py"""
import json
from contextlib import closing
import sqlite3
import tempfile
from pathlib import Path
from fault_model import NoncePool, IndependentWitness, claim_with_witness

def snapshot(source, target):
    with closing(sqlite3.connect(source)) as a, closing(sqlite3.connect(target)) as b:
        a.backup(b)

results = []
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    p = NoncePool(root/'unsafe.db'); n = p.issue()
    first = p.claim_unsafe(n, 'A', crash_after_exposure=True)
    results.append({'scenario':'Crash after exposure, before burn', 'strategy':'Unsafe mark-after-use',
                    'replay_possible':first and p.claim_unsafe(n,'B')})

    p = NoncePool(root/'atomic.db'); n = p.issue(); p.claim_atomic(n,'A')
    results.append({'scenario':'Ordinary repeated claim', 'strategy':'Atomic burn-before-use',
                    'replay_possible':p.claim_atomic(n,'B')})

    p = NoncePool(root/'rollback.db'); n = p.issue(); old = root/'rollback-old.db'
    snapshot(p.path,old); p.claim_atomic(n,'A')
    results.append({'scenario':'Primary database rollback', 'strategy':'Atomic burn-before-use',
                    'replay_possible':NoncePool(old).claim_atomic(n,'B')})

    p = NoncePool(root/'guard.db'); w=IndependentWitness(root/'witness.db'); n=p.issue()
    old = root/'guard-old.db'; snapshot(p.path,old);claim_with_witness(p,w,n,'A')
    results.append({'scenario':'Primary database rollback','strategy':'Independent witness',
                    'replay_possible':claim_with_witness(NoncePool(old),w,n,'B')})

    p = NoncePool(root/'both.db'); w=IndependentWitness(root/'both-w.db');n=p.issue()
    old = root/'both-old.db'; old_w=root/'both-w-old.db'
    snapshot(p.path,old);snapshot(w.path,old_w);claim_with_witness(p,w,n,'A')
    results.append({'scenario':'Primary and witness rollback','strategy':'Independent witness',
                    'replay_possible':claim_with_witness(NoncePool(old),IndependentWitness(old_w),n,'B')})

print(json.dumps({'kind':'nonce-ID state simulation (no FROST signing)','scenarios':results},indent=2))
