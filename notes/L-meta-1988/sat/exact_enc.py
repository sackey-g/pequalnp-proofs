#!/usr/bin/env python3
# Exact SAT model: is there a monotone fan-in-2 AND/OR circuit with s gates
# computing f_G (G bipartite), optionally with a free final AND of <= 2 wires?
# Correctness is checked only on minterms (edges) and maximal false points
# (maximal independent sets, as (P',L') pairs) -- sufficient for monotone circuits.
import sys, itertools, argparse
from pysat.formula import CNF, IDPool
from pysat.card import CardEnc, EncType

def plane(q):
    if q == 2:
        m = 7; D = [0, 1, 3]
    elif q == 3:
        m = 13; D = [0, 1, 3, 9]
    else:
        raise ValueError
    inc = lambda p, l: (p + l) % m in D
    return m, inc

def rows_for(m, inc):
    n = 2 * m
    pos = []
    for p in range(m):
        for l in range(m):
            if inc(p, l):
                v = [0] * n; v[p] = 1; v[m + l] = 1; pos.append(v)
    # maximal independent pairs (P',L') with L'=avoid(P'), P'=avoid(L')
    neg = set()
    for mask in range(1 << m):
        P = [p for p in range(m) if mask >> p & 1]
        L = [l for l in range(m) if all(not inc(p, l) for p in P)]
        P2 = [p for p in range(m) if all(not inc(p, l) for l in L)]
        if P2 == P:
            v = [0] * n
            for p in P: v[p] = 1
            for l in L: v[m + l] = 1
            neg.add(tuple(v))
    return pos, [list(v) for v in sorted(neg)]

def build(m, inc, s, free_and=True, distinct=True, used=True, lexsb=True):
    n = 2 * m
    pos, neg = rows_for(m, inc)
    rows = [(r, 1) for r in pos] + [(r, 0) for r in neg]
    R = len(rows)
    pool = IDPool(); cnf = CNF()
    W = n + s
    isand = lambda i: pool.id(('and', i))
    A = lambda i, j: pool.id(('a', i, j))  # first input of gate i is wire j
    Bv = lambda i, j: pool.id(('b', i, j))  # second input of gate i is wire j
    val = lambda w, r: pool.id(('v', w, r))  # value of wire w (>= n) on row r
    ua = lambda i, r: pool.id(('ua', i, r))
    ub = lambda i, r: pool.id(('ub', i, r))

    def wv(w, r):  # literal or constant
        if w < n:
            return rows[r][0][w] == 1
        return val(w, r)

    for i in range(s):
        g = n + i
        # exactly one choice each, a < b
        cnf.extend(CardEnc.equals([A(i, j) for j in range(g)], 1, vpool=pool, encoding=EncType.seqcounter).clauses)
        cnf.extend(CardEnc.equals([Bv(i, j) for j in range(g)], 1, vpool=pool, encoding=EncType.seqcounter).clauses)
        for j in range(g):
            for k in range(j + 1):
                # forbid b <= a
                cnf.append([-A(i, j), -Bv(i, k)])
        for r in range(R):
            for j in range(g):
                x = wv(j, r)
                for sel, u in ((A(i, j), ua(i, r)), (Bv(i, j), ub(i, r))):
                    if x is True:
                        cnf.append([-sel, u])
                    elif x is False:
                        cnf.append([-sel, -u])
                    else:
                        cnf.append([-sel, -x, u]); cnf.append([-sel, x, -u])
            v = val(g, r); a = ua(i, r); b = ub(i, r); t = isand(i)
            # AND: v <-> a & b
            cnf.append([-t, -v, a]); cnf.append([-t, -v, b]); cnf.append([-t, v, -a, -b])
            # OR: v <-> a | b
            cnf.append([t, v, -a]); cnf.append([t, v, -b]); cnf.append([t, -v, a, b])

    last = n + s - 1
    if free_and:
        # outputs: last gate and o1 (any gate, possibly the last itself)
        O = lambda w: pool.id(('o', w))
        cnf.extend(CardEnc.equals([O(w) for w in range(n, n + s)], 1, vpool=pool, encoding=EncType.seqcounter).clauses)
        for r, (row, lab) in enumerate(rows):
            y = pool.id(('y', r))
            for w in range(n, n + s):
                cnf.append([-O(w), -val(w, r), y]); cnf.append([-O(w), val(w, r), -y])
            if lab == 1:
                cnf.append([val(last, r)]); cnf.append([y])
            else:
                cnf.append([-val(last, r), -y])
    else:
        for r, (row, lab) in enumerate(rows):
            cnf.append([val(last, r)] if lab == 1 else [-val(last, r)])

    if used:
        for i in range(s - 1):
            g = n + i
            lits = [A(k, g) for k in range(i + 1, s)] + [Bv(k, g) for k in range(i + 1, s)]
            if free_and:
                lits.append(pool.id(('o', g)))
            cnf.append(lits)

    if distinct:
        # all wire vectors on the rows pairwise distinct (gates vs gates and gates vs inputs)
        for i in range(s):
            g = n + i
            for j in range(g):
                d = []
                for r in range(R):
                    x = wv(j, r)
                    if x is True:
                        d.append(-val(g, r))
                    elif x is False:
                        d.append(val(g, r))
                    else:
                        e = pool.id(('d', g, j, r))
                        # e -> v_g != v_j
                        cnf.append([-e, val(g, r), x]); cnf.append([-e, -val(g, r), -x])
                        d.append(e)
                cnf.append(d)
        # no constant gates
        for i in range(s):
            g = n + i
            cnf.append([val(g, r) for r in range(R)])
            cnf.append([-val(g, r) for r in range(R)])

    if lexsb:
        # consecutive independent gates: (a_i, b_i) <=lex (a_{i+1}, b_{i+1})
        for i in range(s - 1):
            g = n + i
            dep = [A(i + 1, g), Bv(i + 1, g)]
            for j in range(g):
                for k in range(j):
                    # a_i = j, a_{i+1} = k < j  forbidden unless dependent
                    cnf.append(dep + [-A(i, j), -A(i + 1, k)])
            for j in range(g):
                for b1 in range(g):
                    for b2 in range(b1):
                        cnf.append(dep + [-A(i, j), -A(i + 1, j), -Bv(i, b1), -Bv(i + 1, b2)])
    return cnf, pool, rows

def decode(model, pool, m, s, free_and):
    n = 2 * m
    ms = set(l for l in model if l > 0)
    out = []
    for i in range(s):
        a = [j for j in range(n + i) if pool.id(('a', i, j)) in ms][0]
        b = [j for j in range(n + i) if pool.id(('b', i, j)) in ms][0]
        t = 'AND' if pool.id(('and', i)) in ms else 'OR'
        out.append((t, a, b))
    o = None
    if free_and:
        o = [w for w in range(n, n + s) if pool.id(('o', w)) in ms][0]
    return out, o

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('q', type=int)
    ap.add_argument('s', type=int)
    ap.add_argument('--plain', action='store_true')
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    m, inc = plane(a.q)
    cnf, pool, rows = build(m, inc, a.s, free_and=not a.plain)
    print('rows', len(rows), 'vars', pool.top, 'clauses', len(cnf.clauses), file=sys.stderr)
    cnf.to_file(a.out)
