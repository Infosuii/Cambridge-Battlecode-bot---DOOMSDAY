# EXP-016 release result — reactive ward cooldown preflight

MEASURED. Two independent release builds of the unsubmitted `codex-ward-preflight` match SHA-256 `e3a23a1e04be4c4408e9d054e4e9094c2f15dc8efdfeaddc7961876f4f4a947d`. The switch-off build matches platform v80 / repo v92 / local SHA-256 `5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47`.

The corrected [charged diagnostic](DIAGNOSTIC_CORRECTIONS.md) observed 756 late positive-cooldown checks across 14 of 16 development cells. The earlier zero count came from disabled stdout. This clean release moves the check before reactive bush work. The diagnostic confirms the opportunity, while the release comparison measures the resulting safety.

The [172-pair pool screen](WARD-PREFLIGHT_POOL_SAFETY.json) recorded 81 versus 86 wins, b/c 8/13, delta -2.907 percentage points (95% map-cluster interval -6.977 to +1.163). This uses a single fixed opponent draw. Total fuel suspensions were 162 versus 160, with 28 in round one in each arm. 3 cells increased, including 1 from zero. No round-one cell increase, faults or engine diagnostic codes in either arm.

Verdict: rejected at the original L0 safety gate. No L1/L2, ladder action or holdout use.
