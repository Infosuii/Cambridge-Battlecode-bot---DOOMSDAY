# J026 work stealing — Linux screens by g5070

Code 9c1bbde, branch build/z-plan-5070. K011 accepted by PC 0035; Linux default x3 hash bf3f65d009c0. Every line adds `--set X1_MAPFIT=1`. Own Linux mf-g5070 baseline is used for every pair. Pool: 86 maps, both sides, 172 records per opponent. WORKERS=DZ_MAX_PARALLEL=18. No bot source edits.

Promotion: screen >=102/172; immediately add v86h and x1bru. Pool pass requires >=347/516, paired z>=1.3, no opponent worse by >2 wins, no new faults, fuel-outs <=110% of own baseline. A screen or pool pass is not a claim of complete robustness validation.

| Row | Line | vs v92 /172 | Delta | Gained/lost | Paired z | Fuel-outs | Faults own/opp | Deaths/game | Linux hash | Exact switches | State |
|---|---|---:|---:|---|---:|---:|---|---:|---|---|---|
| 0 | mf-g5070 | 96 | +0 | 0/0 | +0.000 | 171 | 0/0 | 11.994186 | 8df6f3fe1c40 | `--set X1_MAPFIT=1` | baseline |
| 13 | bhold-g5070 | 95 | -1 | 13/14 | -0.192 | 189 | 0/0 | 11.627907 | dc5e8cfa1dc9 | `--set X1_MAPFIT=1 --set A2_BURST_HOLD=1` | screen below promotion |
| 12 | escort-g5070 | 95 | -1 | 32/33 | -0.124 | 156 | 0/0 | 11.017442 | 9b173d5ff971 | `--set X1_MAPFIT=1 --set APEX_ESCORT=1` | screen below promotion |
| 11 | soak64-g5070 | 90 | -6 | 22/28 | -0.849 | 183 | 0/0 | 11.901163 | 62fa91013ced | `--set X1_MAPFIT=1 --set X1_SOAK64=1` | screen below promotion |

Measured own supplied lines: **3/27**.

## Promoted pool gates


A3_ITEMS appears shadowed by an unconditional definition in common.h; actual build hashes are reported without editing bot source. Results, provenance and paired comparisons are under K014/<run>/. No raw replays committed. State and elapsed run times remain local in artifacts/local-only/g5070/k014-state.json.


Work stealing proceeds from the bottom. Reported g5060 lines are skipped; the next three unpublished lines after its last report are reserved for its active batch to avoid duplicate runs. Audit is saved locally in j026-worksteal-state.json.
