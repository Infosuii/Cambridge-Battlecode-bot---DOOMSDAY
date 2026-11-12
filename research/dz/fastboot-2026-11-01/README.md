# Opening fuel: draft memory and DZ_FAST_BOOT (2026-11-01)

Budgets (SDK `fuel_remaining`, fuel headers): first draft turn 10,000,000 (100x), each champion's first turn
200,000 (2x), others 100,000. DZ used ~80k (table build ~148k) of the draft turn and ~140k of the first turn.
Draft memory (1024 B) written in the draft is readable by every play guest on round 1 for ~1.3k fuel
(`dz-diag-draftmem-01`).

Boot paced itself (one step per turn, 25k caps on two loops): in trace builds 21 of 70 maps were not ready by
round 8 (`dz-diag-mapfeat-03`). `DZ_FAST_BOOT` keeps every `tc.allow()` check and drops the per-step returns and
caps: those maps are ready at rounds 2-6 with 0 fuel-outs (`dz-diag-fastboot-01`). Remaining boot time is the
whole-map fields (home, one per altar; per-guest memory, not transferable through 1 KB).

Full pool with the fuel set, paired with the identical binary at DZ_FAST_BOOT=0 (`dz-fuelctl4-*`):

| Opponent | Δ banked (SE) | Δ margin | R100 gold | R250 banked | fuel-outs |
|---|---|---|---|---|---|
| idle | +1.6 (3.0) | +1.6 | 191 vs 173 (**+10%**) | 154 vs 147 | 0 |
| v76 | -0.2 (13.4) | +16.4 | 145 vs 137 (+6%) | 72 vs 65 | 0 |
| v65 | -14.7 (14.5) | -37.9 | 142 vs 142 | 73 vs 79 | 0 |

V-E3 (R100 gold +10%) met against idle; contested results are within deterministic-chaos noise. Adopted into the
fuel set for the next table round (Z14d). Next: allow farming before altar fields finish (banking needs them),
and a draft-turn opening plan through draft memory.

## DZ_EARLY_JOBS (play once camps, masks, home and stats are ready; altar fields one per turn)

Paired with `dz-fastboot-*` (identical binary at DZ_EARLY_JOBS=0, 856a1e7be305): idle -1.7, v76 -0.5,
v65 -6.1 banked, 0 fuel-outs. Not adopted; DZ_FAST_BOOT alone stays in the fuel set.
