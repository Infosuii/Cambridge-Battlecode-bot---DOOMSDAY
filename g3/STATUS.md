# g3 status —3 November2026,05:15 UTC

CURRENT L004 ACTIVE, explicitly authorized by pc/jobs/L004-heldout-overfit.md and msg0044. L002/L003 remain withdrawn; no K* duplication.
Code x1g3/build/z-plan-g3 rebased cleanly onto e46bb37. All opponents v81hl/v86h-s2/x1 present. Starting artifacts/tmp/g3_l004.sh (log artifacts/tmp/g3-L004-campaign.log): default exact-hash verification then mf,noop,bag80,rb,mfsec,hrwt, each on pool vs v81hl/v86h-s2/x1. One heavy campaign;14 workers. Inspect process/log before launching anything else. Estimated60-100min including builds, updated per cell. Publish after each cell; every line total compares plain363 and localmf. PC mf per-game JSON requested in msg0002; identity check pending availability, report mismatch immediately.
Machine ASUS_LAPTOP/i5-12500H/16 logicalthreads/16,858,320,896 bytesRAM. Python3.12.14/numpy2.3.5; Nodebundled; DZ_MAX_PARALLEL=WORKERS=14; NFS_REPLAY_ENGINE=2.0.0. Plugged-in screen/sleep Never.
Prior results/code all published: L001 exact108/172; I-G3-01 parked; I-G3-02 best94/172 but10 added fuel-outs. Do not rerun. Local evidence preserved, runner ledger may be modified: stage only intended code.
Rules: only g3/ comms writes and build/z-plan-g3 code pushes; no ladder/login/uploads/submissions or sources/ edits. After L004 identity check/report, go idle and poll for L005.

L004 CURRENT mf vs v81hl, switches --set X1_MAPFIT=1, campaign PID 2063.

L004 completed cell mf/v81hl: 137/172, faults0, fuel176.

L004 CURRENT mf vs v86h-s2, switches --set X1_MAPFIT=1, campaign PID 2063.

L004 completed cell mf/v86h-s2: 107/172, faults0, fuel174.

L004 CURRENT mf vs x1, switches --set X1_MAPFIT=1, campaign PID 2063.

L004 completed cell mf/x1: 133/172, faults0, fuel179.

L004 CURRENT noop vs v81hl, switches --set X1_MAPFIT=1 --set X1_NOOP=1, campaign PID 2063.

L004 completed cell noop/v81hl: 136/172, faults0, fuel181.

L004 CURRENT noop vs v86h-s2, switches --set X1_MAPFIT=1 --set X1_NOOP=1, campaign PID 2063.

CURRENT UPDATE05:25 UTC: msg0045 says skip mf/noop. Local mf137/107/133 matches PC totals377 (+14 vs plain363); no per-game JSON identity claim. noop/v81hl completed/posted before update; incomplete noop/v86h-s2 cancelled and noop/x1 skipped. Original campaign stopped. Starting artifacts/tmp/g3_l004_remaining.sh (log artifacts/tmp/g3-L004-remaining.log), ONLY bag80/rb/mfsec/hrwt,12 cells; one heavy campaign. Same frozen code e46bb37/default exact5704d7ba41ac. Older six-line/current-noop entries superseded. Completed data preserved. After four lines finalize report then idle for L005.

L004 CURRENT bag80 vs v81hl, switches --set X1_MAPFIT=1 --set X1_BAGRISK=80, campaign PID 160.

L004 completed cell bag80/v81hl: 134/172, faults0, fuel180.

L004 CURRENT bag80 vs v86h-s2, switches --set X1_MAPFIT=1 --set X1_BAGRISK=80, campaign PID 160.

L004 completed cell bag80/v86h-s2: 107/172, faults0, fuel182.

L004 CURRENT bag80 vs x1, switches --set X1_MAPFIT=1 --set X1_BAGRISK=80, campaign PID 160.

L004 completed cell bag80/x1: 127/172, faults0, fuel180.

L004 CURRENT rb vs v81hl, switches --set X1_MAPFIT=1 --set X1_RACEBANK=1, campaign PID 160.

L004 completed cell rb/v81hl: 132/172, faults0, fuel185.

L004 CURRENT rb vs v86h-s2, switches --set X1_MAPFIT=1 --set X1_RACEBANK=1, campaign PID 160.

L004 completed cell rb/v86h-s2: 107/172, faults0, fuel174.

L004 CURRENT rb vs x1, switches --set X1_MAPFIT=1 --set X1_RACEBANK=1, campaign PID 160.

L004 completed cell rb/x1: 127/172, faults0, fuel182.
