import sys
sys.path.insert(0, sys.argv[1])
from exact_enc import plane, build
from pysat.solvers import Cadical195
m, inc = plane(2); n = 2*m
# star circuit on Fano: for each point p: OR of its 3 lines, AND x_p, then OR chain
gates = []  # (type, a, b)
def add(t, a, b):
    a, b = min(a, b), max(a, b); gates.append((t, a, b)); return n + len(gates) - 1
terms = []
for p in range(m):
    ls = [m + l for l in range(m) if inc(p, l)]
    o = add('OR', ls[0], ls[1]); o = add('OR', o, ls[2]); terms.append(add('AND', p, o))
t = terms[0]
for x in terms[1:]: t = add('OR', t, x)
s = len(gates); print('star size', s)
cnf, pool, rows = build(m, inc, s, free_and=False, lexsb=False)
assum = []
for i, (t, a, b) in enumerate(gates):
    assum += [pool.id(('a', i, a)), pool.id(('b', i, b)), pool.id(('and', i)) * (1 if t == 'AND' else -1)]
with Cadical195(bootstrap_with=cnf.clauses) as S:
    print('star consistent with encoding:', S.solve(assumptions=assum))
