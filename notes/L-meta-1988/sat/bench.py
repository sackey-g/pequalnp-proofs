#!/usr/bin/env python3
# Wall-clock benchmark of SAT solvers on the exact-circuit CNFs.
# usage: bench.py <timeout_s> <out.tsv> <name=command-with-{cnf}> ... -- <cnf> ...
import subprocess, sys, time, os, re

def run(cmd, timeout):
    t = time.time()
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        out = p.stdout + p.stderr
        dt = time.time() - t
    except subprocess.TimeoutExpired:
        return 'TIMEOUT', timeout
    out = re.sub(r'\x1b\[[0-9;]*m', '', out)
    if re.search(r'^s UNSATISFIABLE', out, re.M):
        return 'UNSAT', dt
    if re.search(r'^s SATISFIABLE', out, re.M):
        return 'SAT', dt
    return 'UNKNOWN(rc=%s)' % p.returncode, dt

def main():
    timeout = int(sys.argv[1]); tsv = sys.argv[2]
    i = sys.argv.index('--')
    solvers = [a.split('=', 1) for a in sys.argv[3:i]]
    cnfs = sys.argv[i + 1:]
    new = not os.path.exists(tsv)
    with open(tsv, 'a') as f:
        if new:
            f.write('instance\tsolver\tresult\tseconds\n')
        for c in cnfs:
            for name, tmpl in solvers:
                r, dt = run(tmpl.replace('{cnf}', c), timeout)
                line = '%s\t%s\t%s\t%.1f' % (os.path.basename(c), name, r, dt)
                print(line, flush=True); f.write(line + '\n'); f.flush()

if __name__ == '__main__':
    main()
