import sys
sys.path.insert(0, sys.argv[1])
from exact_enc import build
out = sys.argv[2]
cyc = lambda k: (k, lambda p, l: l == p or l == (p + 1) % k)
for name, (m, inc), s in [('c8_s8', cyc(4), 8), ('c8_s9', cyc(4), 9), ('c8_s10', cyc(4), 10), ('c10_s10', cyc(5), 10), ('c10_s11', cyc(5), 11)]:
    cnf, pool, rows = build(m, inc, s, free_and=False)
    cnf.to_file(f'{out}/{name}.cnf')
    print(name, 'vars', pool.top, 'clauses', len(cnf.clauses))
