#!/usr/bin/env bash
# Cube-and-Conquer: march_cu splits the CNF into cubes, kissat solves each cube, P jobs at a time.
# usage: cnc.sh <cnf> <march_cu> <kissat> <jobs> [march options, e.g. -n 300 or -d 12]
# Prints "s UNSATISFIABLE" when every cube is UNSAT and "s SATISFIABLE" when some cube is SAT.
set -u
cnf=$1; march=$2; kissat=$3; jobs=$4; shift 4
work=$(mktemp -d -p "${TMPDIR:-/tmp}")
trap 'rm -rf "$work"' EXIT
"$march" "$cnf" -o "$work/cubes" "$@" > "$work/march.log" 2>&1
ncubes=$(grep -c '^a' "$work/cubes" || true)
echo "c cubes $ncubes"
if [ "$ncubes" -eq 0 ]; then
  # march decided the instance itself
  grep -E '^s ' "$work/march.log" || "$kissat" -q "$cnf"
  exit 0
fi
read -r _ _ nv nc < <(grep -m1 '^p cnf' "$cnf")
body=$(mktemp -p "$work"); grep -v '^p cnf' "$cnf" | grep -v '^c' > "$body"
solve_cube() {
  local i=$1 line=$2
  local lits=$(echo "$line" | sed 's/^a //; s/ 0$//')
  local k=$(echo $lits | wc -w)
  local f="$work/cube_$i.cnf"
  { echo "p cnf $nv $((nc + k))"; cat "$body"; for l in $lits; do echo "$l 0"; done; } > "$f"
  "$kissat" -q "$f" > "$work/res_$i" 2>&1
  local r=$?
  rm -f "$f"
  if [ $r -eq 10 ]; then echo SAT > "$work/found"; fi
  echo $r
}
export -f solve_cube; export work nv nc body kissat
grep '^a' "$work/cubes" | nl -ba -w1 -s$'\t' | \
  xargs -P "$jobs" -d '\n' -I{} bash -c 'i=$(echo "{}" | cut -f1); l=$(echo "{}" | cut -f2-); [ -f "$work/found" ] || solve_cube "$i" "$l"' > "$work/codes"
if [ -f "$work/found" ]; then echo "s SATISFIABLE"; exit 10; fi
if [ "$(grep -c '^20$' "$work/codes")" -eq "$ncubes" ]; then echo "s UNSATISFIABLE"; exit 20; fi
echo "s UNKNOWN"; exit 0
