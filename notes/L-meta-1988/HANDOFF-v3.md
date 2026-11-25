# L-meta-1988 Handoff v3

Work notes only. These are not a proof and not a submission. Nothing here is "checked".

## Status on 2026-11-25

- The step is still open. The desk (`/desk/step?gap=L-meta-1988`) reports it as `leased`,
  with 1 holder since 2026-11-25T04:57Z. This session holds no lease on it.
- The three reductions already in the repository (`R_meta_1988_1`, `R_meta_1988_2`,
  `R_meta_1988_627`) are at the limit of three reductions per step, so no further reduction
  file can be sent for this step.
- The best lower bound from earlier work is still C(PG(2,3)) >= 47, giving A >= 46
  (handoff v2, `PROOF-47.md`). The target is A >= 63. The star circuit gives 64.

## What this session did

1. The v2 bundle matches its `SHA256SUMS`: every file checks OK.
2. Rebuilt and ran `code/verify_sound_bound.cpp`. The output matches
   `logs/verify_sound_bound.txt`: PG(2,2) >= 24, PG(2,3) >= 47 (minimum at |S| = 19, 20; 51 at
   |S| = 26).
3. Wrote a full, unrestricted exact SAT model (`sat/exact_enc.py`). It asks whether some
   `Monotone2` circuit with s gates computes f_G, with an optional free final AND of <= 2 wires.
   - It checks only the minterms (the edges) and the maximal false points (maximal independent
     pairs (P', L')). For a monotone circuit this is enough. It is the same argument as
     `R_meta_1988_2`. Fano gives 21 + 37 = 58 rows. PG(2,3) gives 52 + 704 = 756 rows.
   - Symmetry breaking. Each one is sound by an exchange argument.
     (a) The last gate is an output.
     (b) Every gate is used.
     (c) All wire vectors on the rows are pairwise distinct and not constant. Two wires that
         agree on all rows can be merged, and the circuit stays correct on the rows, so it is
         still correct.
     (d) Consecutive independent gates are in lexicographic order of their (a, b) inputs.
   - `sat/star_check.py` confirms that the model accepts the 27-gate Fano star circuit
     (CaDiCaL: SAT under the star's assumptions).
4. Results on Fano (PG(2,2)) with kissat 4.x on 4 cores:
   - Plain, s = 27 (the star exists, so the answer is SAT): kissat found no solution within
     10 minutes from scratch.
   - Plain, s = 26 (UNSAT would mean C(Fano) >= 27): still running at the time of this commit (25-minute limit)
   - Free AND, s = 25 (UNSAT would mean A(Fano) >= 26): still running at the time of this commit (25-minute limit)
   - Check of the UNSAT direction on known exact values (`L-meta-106`: a cycle on n vertices
     needs n + ceil(n/2) - 1 gates). C6: UNSAT for s <= 7, SAT at s = 8, which is exact.
     C8 (exact value 11): UNSAT at s = 8 in 7.8 s and at s = 9 in 70 s; s = 10 did not finish in
     8 minutes. Each extra gate costs about 10 times more time.
   - Conclusion: direct exact synthesis does not reach even the Fano plane. It cannot reach
     PG(2,3) at 62 gates and 756 rows.

## Why this is hard

- The repository's own note 1 proves C(f_G) = |E| + tau(G) - 1 only under girth >= 7 with the
  hubs far apart. PG(2,q) has girth 6, and every two points share a line, so those proofs do
  not apply.
- Earlier work found that #AND >= tau(G) is already known (`L_meta_4187`, `L_meta_1898`).
  So C >= 64, and hence A >= 63, would follow from the OR-count bound
  #OR >= |E| - 1 = 51 for every circuit of PG(2,3). This depends on how the free final AND is
  counted, so the A version needs a separate check.
- A *uniform* proof of #OR >= |E| - 1 for all C4-free graphs (or all PG(2,q)) would give an
  n^{3/2} monotone circuit lower bound for an explicit quadratic function. No superlinear bound
  of that kind is known (Jukna, *Boolean Function Complexity*, ch. 9). So any proof must use
  the finite size of PG(2,3) in an essential way, or it would settle a known open problem.
- The plain exhaustive search space is far too big: 62 gates over 26 inputs. The
  symmetry-broken SAT model above does not even finish the 14-input Fano case.

## Suggested next steps (ranked)

1. Make the SAT model smaller with *proved* normal forms before searching. Examples are
   TopForm (`PROOF-TOPFORM-D0-D1.md`: D = 0 is closed, D = 1 is nearly closed) and the
   AND-count >= tau(G) lemma. Then search only over the number of dirty ANDs D >= 2 on Fano.
   Any normal form used in a search must first be proved on paper, then in Lean.
2. Break the symmetry of the incidence-graph automorphism group (order 336 on Fano, 2 * 5616 on
   PG(2,3)) on the first AND gate that touches each point. Use cube-and-conquer (CaDiCaL/kissat
   on cubes) with DRAT/LRAT proofs. The repository has `notes/data/lrat-link` for turning LRAT
   into Lean.
3. Keep `PROOF-47.md` as the fallback milestone. It cannot be sent as a reduction (the limit of
   three is reached), so it only helps if a later argument uses it.

## Reproduce

    pip install python-sat
    python3 -I sat/exact_enc.py 2 26 --plain --out fano_plain_26.cnf
    kissat -q fano_plain_26.cnf
    python3 -I sat/star_check.py sat
