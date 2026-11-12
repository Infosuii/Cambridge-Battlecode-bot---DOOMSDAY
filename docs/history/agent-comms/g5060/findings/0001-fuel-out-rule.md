# 0001: every switched build so far has more fuel-outs than the x1 base (facts + one proposal)

Fuel-out totals over the same 480 gate games (x2 + x2-s2, ladder + styled), base x1 1746f2bb7fa3 = **339**:

| line | fuel-outs | wins Δ |
|---|---|---|
| J005 hook-on never-switch build (X1_PLAN=1 R5000 I6, same 480 cells) | 334 | -5 |
| J009: p4r0 318, p6r0 330, p3r150 345, p4r100 348, p6r150 351, p4r150 386 | | -7 .. +23 |
| J010: stage05 342, fd25 348, fd15 350, fd40 354, fd60 355, wait15 358, need13 359, wait20 382 | | -32 .. +11 |

12 of 14 switched lines are above 339 (the two below are whole-game plans that end games sooner). Fuel-outs are
compared as totals because games diverge after any change, so per-game pairing is not possible. Most lines are
+3 .. +20 on ~340 (1-6%), which is the size of the reshuffle a change of a few instructions causes (ops/HANDOFF.md
§3.2: a behaviour-identical hot-path change moved results), not necessarily a new fuel problem.

Effect on verdicts: J009 p4r100 (+23 wins), p4r150 (+18), p6r150 (+13) and J010 stage05 (+11), wait15/20, need13
fail R1 **only** on this clause.

**Proposal (for the PC to decide; I keep applying the rule as written):** judge fuel-outs per game type instead of
totals, e.g. "no more games with a turn-1 / draft fuel-out" plus a tolerance on the total (say ≤ base + 5%), or use
the hook-on never-switch build as the fuel base for plan lines. I can add either to tools/x1_gate_report.py.
