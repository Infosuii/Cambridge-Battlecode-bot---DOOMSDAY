# Z14 carrier-policy draft refresh

Decision: keep `DZ_MAP_DRAFT_MATRIX=0`. The selected carrier release remains
5cf28cb74612e04e97910fed5ec7d5d69b514cf3c0f5319ddac7c52b99934a5d.

Eight global lineups ran on56 development maps, both sides:896 games. All other
policies stayed fixed. `DZ_MAP_DRAFT_TABLE=0` makes variant0 the global prior,
rather than accidentally comparing against the incumbent table again.
`dz_draft_refresh.py` compares each candidate with the actual incumbent lineup;
it can restore prior0, excludes all14 held-out maps, requires100 summed margin,
and cannot select a no-op for compilation/layout variation. There were zero
same-lineup differences. All eight global lineups bank less than the incumbent
on the matched112 cells; their per-map results generate18 override rows.

The optimistic best-of-eight training estimate is+44.22 margin per game. It is
not a compiled mixed-table result. `selection.json`, `TABLE.json` and
`CONFIRMATION_FREEZE.json` freeze the choices/signatures/hashes before v76.

## Independent confirmation and preservation

The compiled mixed table ran140 v76 games. Banked233.14 versus225.75:
+7.39 (descriptive paired SE6.34); margin+7.06 (SE6.80); wins1 each.
Development112 margin+8.82 (SE8.50), just passing the predeclared entry gate.
R500 banking+8.26 overall. All104 unchanged-map cells, including28 held-out
cells, have identical banking outcomes. This is preservation of unchanged
choices, not learned-policy holdout evidence. Some individual rows lose badly;
the modest aggregate gain is uncertain and relies heavily on a few maps.

The next140 trace-idle games retain the same three stuck episodes. However,
the447 matching R1000 slot snapshots show stall+0.07219 percentage points and
idle+0.02824 points, failing `GATES.md`. Work+0.26487 and travel progress-0.33957
points. Full trace banking is925.16 versus919.52 (+5.64), but this does not
override the frozen productivity requirement or establish release preservation.
The linked duo on the-pond adds two snapshots: full totals include449, matched
comparisons447. Both views are retained in PRODUCTIVITY.json.

All1176 new draft-study games have zero candidate native faults/fuel-outs.
The trace pool also has zero caught action/module errors. Full mixed-table
release-idle/v65 preservation pools were not run after the productivity gate
failed. No default promotion and no v76-based removal of losing rows.
The first ad-hoc gate command misspelled the `stall` field; the corrected gate
uses the same frozen results without rerunning or modifying a match.

## Reproduction and limits

RESULTS.json and the per-run capsules hold exact sources, binaries and outcomes.
Every completed comparison uses tools/dz_compare.py. The default release and
TRACE1/TRACE_TO0 productivity binary reproduce their selected SHA values from
an exported source/SDK/CMake tree; see DEFAULT_IDENTITIES.json. This is the same
host and pinned toolchain, not a second physical device.

49 Python tests,10 Node accounting tests,14,544 attack-clock and10,000
reset-damage reference cases pass. Native host ABI is still untested. All49
locally present evidence capsules verify. Deterministic cells are not independent
random seeds; SE describes dispersion. Formal parity/promotion gates and the
reserved release holdout remain unclosed/unused. No ladder action occurred.
