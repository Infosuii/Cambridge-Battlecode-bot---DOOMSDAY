# botx3 experimental foundation

Local research copy of x1 at source 2732245. All new switches default off;
the final off build must equal original x1 `1746f2bb7fa3` byte for byte.
No configuration is approved for competition use.

- `X3_PLAN_END`: expire an enabled X1_PLAN at this round; zero preserves the original indefinite plan.
- `X3_COVER_SAFE`: hide provisional bush IDs and query current wards before claiming hidden cover.
- `X3_BANKCYCLE=1`: experimental delivery-cost candidate ranking.
- `X3_BANKCYCLE=2` with `APEX_PLAN=1`: existing rolling-horizon camp/bank planner with gem-only carry discount and all-member bank distance.
- `X3_BANKCYCLE=3` with `APEX_PLAN=1`: additionally bound optional planning fuel, candidates and depth.
- `X3_TRACE=1`: separate activation diagnostics, excluded from competitive comparisons.

See `research/botx3-20261102/REPORT.md` for frozen builds, failure investigations,
focused retries and limitations. Existing shared claims coordinate reservations;
this prototype is not yet a new team-wide scheduling system.
