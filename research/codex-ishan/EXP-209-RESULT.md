# EXP-209 result — Route ablation is a promising exploratory lead; no release qualified

MEASURED: LIVE111_HEAVY_RESULT.json completes1440 real100k release games,240 per arm,12 established dev maps/five opponents/both sides/two fresh paired seeds54347/57787. All modified exact releases build twice; all-off0896a189. No draft changes,faults,opponent faults,codes orR1fuel-outs. The independent LIVE111_HEAVY_RECOUNT.json checks every saved native hash,engine,map,seed,outcome and safety event,then reproduces every overall/stratum report.

| Arm | Wins/240 | Delta pp and map-cluster95% interval | Fuel-outs | Per-cell increases vs stock |
|---|---:|---:|---:|---:|
| Stock |146|reference|928|reference|
| Legacy lab stack off |177|+12.917[+3.333,+22.917]|1262|142|
| Forced A3 off |154|+3.333[-2.500,+9.583]|972|60|
| Duo off |141|-2.083[-10.833,+6.667]|1015|112|
| Tactical verdict search off |163|+7.083[-1.667,+15.833]|1030|101|
| Multi-stop route search off |177|+12.917[+3.333,+23.750]|789|75|

These are exploratory multiple-arm estimates,not multiplicity-adjusted or ladder proof. Lab-off increases exhaustion substantially. Route-off exact release3ad0ab94f3a5c7d843d73aaf9b1edd2f92cd20cc5dfa423b0580ef0e4852a134 has lower total fuel and mean paired production-margin change+57.217 gems,but75 native cell increases; it is not qualified. Its opponent deltas are exact109+14.583,p65pack+16.667,public-khiri0,v92+35.417,x3inv-2.083. Category deltas range0to+30 and size+8.333to+19 on this panel. All other arms remain visible; don't combine whichever bits happened to win.

Next: freeze a disjoint development-map confirmation and a controlled route/runtime interaction to distinguish target-policy from freed-budget effects. Same-state route-choice/cost diagnostic must report if the selected fixture never invokes route search. Original full safety gate versus v92 remains mandatory; no individual official-pool failures inspected for tuning. Current source route-off has no selection,holdout,upload,activation or duel result.
