# Builder handoff — local validation complete

Delivered candidate: CONTACT3 + PROGRESS1 + GOV5 (CPG), accepted as a measured local improvement; not release-qualified
for the official ladder. Frozen v80/v92 remains the official baseline. No submission, activation, duel or ladder lock
was requested, performed or indirectly authorized. The user prohibits official ladder activity for this work.

## Measured result

2232 matched cells on186 maps (86 pinned pool maps, including70 official maps from the handoff, plus100 untouched
generated maps), six frozen opponents and both sides. Same actual engine seeds, engine build and map hashes in both
arms; no missing/failed/excluded confirmation games. Engine2.0.0 and official fuel throughout.

| Frozen variant | Wins vs1537 baseline wins | Paired gain (95% map-cluster CI) | Fuel suspensions vs1532 | Status |
|---|---:|---|---:|---|
| CPG — delivered |1621 (+84)|+3.763pp (+1.523,+6.004)|803|Accepted local evidence; qualification limits below|
| CG — alternative |1636 (+99)|+4.435pp (+2.240,+6.586)|806|Experimental: C2 crosses regression threshold|
| GOV5 control |1562 (+25)|+1.120pp (-0.762,+3.047)|790|Fuel infrastructure; strength gain inconclusive|

CPG unseen generated-map gain is+3.75pp (+0.917,+6.583). Development gain+5.00pp; selection+4.75pp. No faults or official
diagnostic codes in the final arms. CPG has no category/opponent point delta below-10pp; C2 is-6.25pp on only4 maps,
with wide uncertainty. CG has higher aggregate score but C2 is-12.5pp, so it is not the candidate passing that gate.
The CPG-minus-CG difference is inconclusive (-0.672pp,CI-2.554,+1.210). Neither bot is a category-specific fit.

## Running artifacts

Primary source archive: `candidate-source.zip`; release WASM: `candidate.wasm`, SHA-256
`a06ae0655dc5a473db4c783e4b436487ac39959e04eb02573090b938625657a4`.
Experimental CG WASM SHA-256: `e36f44134ed7ca2e9fc914bee73c0b76a826519e0b74446e88c43140a72fe0a2`.
Frozen v92 SHA-256: `5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47`.
Both official source-only archives were cleanly extracted, rebuilt to exact hashes and tested in18 matched smoke cells.
Current committed source also rebuilds both exact hashes. Source archive sizes are682898/682892 bytes; offline official
packager accepted them. The live server size limit was not queried. Neither archive was uploaded.

Candidate source lives in `bots/jd-g5070-resume-0715/src`. Every switch defaults off to retain the exact v92 control.
The packaged primary variant explicitly enables JD_CONTACT=3,JD_PROGRESS=1,JD_GOV=5. Use these flags/the archive to
reproduce the scored candidate; a default build is the baseline. Policy freeze30aa8ead preceded all final data.

One exact next command from this checkout (use a new name for each reproduction):

`python "C:\Users\omdha\.codex\worktrees\g5070-resume-0715\doomsday\tools\jd_g5070_resume_0715\reproduce.py" --variant cpg --name user-check-01`

## Supporting work and limits

The exact float32 neural exporter preserves the lightly trained seed and completed iteration31 checkpoints. Both
headers have56609 verified literals; seeded golden checks pass121/121 WASM observations and185/185 native rows with
64 extreme cases. The fast-kernel configuration is enforced. Corrected-runtime checkpoint conformance fails release
fuel/quality gates; neural heads remain off. No training job was restarted; lineage is in TRAINING_LINEAGE.json.

The pending-last-pick roster codec passes108384 legal prefixes and88 engine body instances across team sizes3-6 and
all six body slots. It is outcome-neutral on800 selection cells and stays off. Early field construction stays off:
it activates on small maps but cannot fit useful full fields in the sampled heavy first-turn budgets. Retry required.

Fuel and memory contracts, mechanisms, failed attempts and reproduction commands are in this evidence directory.
FUEL_FINAL.md/fuel_bench.json report ordinary/stage percentiles and the profiler's substantial perturbation. Profiled
scores are excluded. Lower total suspensions do not prove zero new failure modes in every cell. Silent SDK action
false returns are not separately instrumented. Public opponents have ceiling effects; per-opponent results are retained.
Generated maps have size/opponent strata; C1-C7 labels are limited to measured atlas maps. Small categories remain uncertain.

No authenticated live map-pool refresh or ladder validation occurred. The claimed result is improvement on these pinned
local suites, not leaderboard superiority. Preserve v92 for official use; any later platform work needs separate explicit
authorization and the coordination rules. No live version was changed by this session and no lock is held by it.

## Publication and ownership

Branch: `johndoe/qualifier-builder-g5070-resume-0715`. New candidate/tools/evidence only; original checkout changes,
frozen v92/x1 and training outputs preserved. Issue #6 records epoch3 assignment and all boundaries.
Automatic approval review rejected git push for source-export authorization. Commits are local only; no alternate
publication route was used. The remaining action is explicit user approval to push this exact branch and its source /
compact evidence to Infosuii/neural-networkk-battlecode. Large checkpoints/data/replays remain outside Git.
