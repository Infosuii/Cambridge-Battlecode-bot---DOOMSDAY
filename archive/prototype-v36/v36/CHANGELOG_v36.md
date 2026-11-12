# v36 changelog (candidate, from frozen v34)

Only `bot_v36/src/draft.cpp` differs from `bot_v34/src`.

- **New:** `NOVA_V36_DRAFT` (on): unknown, spread-out maps draft C&I+Stellar+Ren (3 picks), C&I+Ren+Ryth+Varg
  (4), C&I+Stellar+Ren+Ryth+Varg (5). vs v34 on 640 untouched generated maps: 55.3% (52.7–57.8), +51 gems.
- **Fix:** draft test overrides (`APEX_DRAFT_LIST`, `APEX_DRAFT_T3/T4/T5`) now take effect; no release effect.
- **New, off:** `NOVA_MAPID_STRICT` official-map check by gem/gold totals.
- **New, probe only:** `NOVA_MAPFACTS_PRINT`.

Artifact `v36/release/bot_v36.zip`, manifests in `v36/release/`. Evidence: `v36/agent4/reports/DRAFT_REPORT.md`,
`v36/agent4/EXPERIMENTS.md`. Rollback: `bot v34.zip` or `NOVA_V36_DRAFT=0`.

## Engine 1.0.1 (patch 1.0.0/1.0.1) and the ML base bot
- v36 builds unchanged on cambc 3.0.2 and beats v34 68.5% (66.2–70.9) on 640 untouched maps (E8).
- Settings-only retuning for the new rules found nothing better (E9–E11: Heart of Ruin meta draft, carry size,
  end-of-game banking, gold weight, aggression). **v36 is the base bot for the ML approach**; submitted as platform
  version 38 (20 Oct). Note for tuning: `APEX_AGGRESSION` is inert while `APEX_BRAIN=1`.
