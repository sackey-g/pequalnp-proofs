import sys, time
sys.path.insert(0, sys.argv[1])
from exact_enc import build
from pysat.solvers import Cadical195
tests = {
  'C6':  (3, lambda p, l: l == p or l == (p + 1) % 3),
  'C8':  (4, lambda p, l: l == p or l == (p + 1) % 4),
}
for name, (m, inc) in tests.items():
    for s in range(3, 14):
        cnf, pool, rows = build(m, inc, s, free_and=False)
        t = time.time()
        with Cadical195(bootstrap_with=cnf.clauses) as S:
            r = S.solve()
        print(name, 's=', s, 'SAT' if r else 'UNSAT', round(time.time() - t, 2), 's', flush=True)
        if r: break
