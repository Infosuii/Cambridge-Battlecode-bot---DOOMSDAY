# Current v70: fresh evidence and revised priorities

Updated 2026-10-29T00:31:01.197589+00:00. This is a separate **exploratory** follow-up to the completed v69 study. No old reserved-game trajectories, model refits, new shared-quota matches or production changes were used.

## What the extra information changes

1. **The active source changed.** The website showed v70, “home side,” Active/Verified. Its official archive has 33 files, of which four differ from frozen v69. It is a substantially different policy, not merely the old bot with a small recall fix.
2. **Count distinct trajectories.** The 85 downloaded matches contain 59 distinct raw replay hashes: 26 repeated BattleCats trajectories. All 70 BattleCats games are side A. Their raw record is 32/70 wins; one-per-trajectory is 18/44. These are descriptive records from different weighting schemes, not estimates of mirrored-side performance.
3. **The recall/banking defect is present in the current bot on two ordinary, non-gated maps.** Exact logging reproductions show five affected turns on split and ten on collision. This extends the mechanism beyond the earlier guardians case, but does not establish that a particular patch wins those races.
4. **The loss-side equipment gap widens after round 100.** In 34 distinct losses, mean cost gap is -33.5 at R100, map95 [-92.8, 18.3]; at R250 it is -180.0, map95 [-292.5, -75.8]. Focus on the R100–250 transition instead of assuming every loss was settled by the first purchase.
5. **Allocation differs by champion.** In 25 same-game Marcella pairs from distinct losses, our Marcella is behind by 68.0 earned gold and 61.2 inventory cost at R100. Vendetta is ahead by 35.2 earned gold and 22.2 cost in 27 loss-side pairs. A team-wide “buy earlier” rule would miss that imbalance.
6. **Guardians is a separate conversion failure worth reproducing.** One current loss banked 0 of 1,389 collected gems and lost 1,265, despite a +90 equipment lead at R100. That is not a simple bad-opening case.

## Source and dataset provenance

The official [Submissions page](https://2026a.battlecode.co.uk/game/submissions) showed platform70, submission78116168-a5b6-42f3-bb19-1f7d1b17c45d, note “home side.” Downloaded archive v74_home_side.zip SHA256: `7b84d6a7fa91ea24efdad5bb94d426c496d8918ff65428e69c034e3c46d1ae04`. The archive filename is not the platform version. Raw source is retained unchanged under the ignored follow-up folder, not added to a frozen bot directory.

The [version-filtered match history](https://2026a.battlecode.co.uk/game/matches?group-version=70) supplied all 17 selected completed groups: 15 ranked games and 70 existing unranked games against BattleCats. No game was queued by this continuation. All 17 ZIPs, 85 nested replay bundles and 85 server-native summaries were downloaded through official website controls. The JSON summary control failed once; the official binary export worked and CLI4.0.0 converted CAMSTAT files offline. PLAN.json fixes the intake IDs; MANIFEST.json and DOWNLOADS.json preserve provenance and hashes.

All 85 resource extracts pass native final cursor/outcome/score and physical gem identities, with 21,543 gold/gem/earned-gold clock checks. Zero unclassified sampled earned gold. Five excluded calibration games match the earlier validated timeline at every requested mark. Four new accepted-input scripts reapply byte-for-byte through official APIs with 4,318 round states matched. Unmodified current source versus enemy puppet and both-script controls reproduce one ranked loss and one win exactly; both new sparse logging builds also reproduce their complete original games. These are whole-game behavioural checks, not a server Wasm hash claim.

The new metadata/ladder snapshot was recorded at 2026-10-29 00:01 UTC (server update 23:55 UTC): DOOMSDAY rank49/rating1998.6; SkibidiSloppers40/2024.7, BattleCats43/2018.4, test4 44/2018.4, ha²t52/1993.8. These are timestamped observations, not live predictions.

| Current source feature | Effective source setting / difference |
|---|---|
| HOME_SIDE | On; enemy-territory weight 0.3, aggression multiplier 0.8 |
| V71 map knob profiles | Removed; prior per-map effective thresholds cannot be copied across versions |
| V70 per-map draft table | Removed; custom five-pick lineup uses Vendetta, Varg, Cassi & Issac, Marcella, Heart of Ruin |
| V75 lone-fight guard | Removed (was active in the v69 study) |
| A3 items / focus / numbers / single capture owner | All off, despite added code and later guarded default definitions |
| A3 back-off override | On; HP floor 40%, TTK/TTD factor 1.25, wounded target at equal numbers below 40% |
| A2_TEAM | 2, changed from 0 |
| Island escape and incremental siege scan | V69 island escape and V68 incremental siege paths removed |
| Recall cancellation / bank-disable timer | Same inconsistency remains, now at bot.cpp around 6844 / 4530 / 4634 |

Comments in source mentioning earlier searches or test win rates were not independently audited here. A code block can exist while its switch is zero. The two full source reproductions support behavioural fidelity in those contexts; source defaults alone do not prove every server build setting.

## Opponents, duplicates and side coverage

| Sample | Match IDs / distinct trajectories | Wins | Mean final margin | Side coverage |
|---|---|---:|---:|---|
| All raw IDs | 85 / 59 | 39/85 | 36.7 | A75, B10 |
| One per raw replay hash | 59 / 59 | 25/59 | -12.4 | Different map/opponent mixture from raw IDs |
| BattleCats, raw | 70 / 44 | 32/70 | 51.8 | A only |
| BattleCats, deduplicated | 44 / 44 | 18/44 | -5.2 | A only |
| SkibidiSloppers, ranked | 5 / 5 | 1/5 | -233.8 | {'a': 5} |
| test4, ranked | 5 / 5 | 2/5 | -104.8 | {'b': 5} |
| ha²t, ranked | 5 / 5 | 4/5 | 238.4 | {'b': 5} |

Nineteen hash groups have duplicates. Repeating deterministic games supplies no new policy evidence. Deduplicated rows use the first occurrence of each exact replay hash; outcome is not used to choose representatives. Every match ID is still retained for audit. Sampling is narrow, mostly one opponent and one side; Wilson intervals in ANALYSIS_DATA are occurrence summaries, not a remedy for this selection bias. No causal v70-versus-v69 improvement is inferred.

## Where the fresh losses separate

Below, every gap is ours minus the opponent in the **same game**, using 34 distinct loss trajectories. Native gold sources are capture, kills and bank bonuses. Inventory is purchase-cost value, not combat power.

| Round | n | Collected gems | Earned gold | Capture gold | Kill gold | Bank-bonus gold | Inventory cost | Unspent gold | Deaths |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 25 | 34 | -1.6 | -7.6 | -7.6 | +0.0 | +0.0 | -1.8 | -5.9 | +0.0 |
| 50 | 34 | -4.8 | -17.2 | -12.2 | -2.9 | -2.1 | -24.7 | +10.1 | +0.2 |
| 75 | 34 | -0.8 | -37.2 | -22.7 | -11.8 | -2.7 | -39.7 | +9.6 | +0.2 |
| 100 | 34 | +0.6 | -46.3 | -45.9 | +5.9 | -6.2 | -33.5 | -1.6 | +0.1 |
| 150 | 34 | +1.6 | -72.2 | -52.5 | -1.0 | -18.8 | -99.7 | +45.4 | +0.2 |
| 250 | 34 | -11.2 | -187.2 | -110.4 | -28.0 | -48.8 | -180.0 | +8.4 | +0.4 |
| 500 | 33 | -37.9 | -557.0 | -403.0 | -61.8 | -92.2 | -560.0 | -11.0 | +0.8 |

R250 cost-gap group-bootstrap95 [-260.8, -97.1]; R100 [-76.0, 7.9]. These exploratory intervals resample historical maps or groups, not independent tactical experiments. The exact R100 deficit is uncertain; the later gap is clearer in this sample.

At R100 the 34 distinct losses have almost equal collected gems (55.4 ours vs54.8 opponent). Their gold is already lower (254.5 vs300.8 earned), and by R250 the deficit is187.2 earned gold: capture110.4, kills28.0 and bank bonuses48.8. Unspent cash differs by only8.4 at R250 while costed inventory differs by180.0. This points toward income/conversion and allocation, not primarily a large unused team cash pile. First item purchase median is R71 ours versusR58.5 enemy (34 games); location and affordability still need exact-state review.

Final loss margin -477.9 = collected margin -370.9 + bag preservation -144.2 + end-carried adjustment 37.3 (n=34). Pooled conversion is 68.3% ours versus 86.8% enemy. These are accounting identities, not recoverable gains. The same lost bag can affect income and preservation.

Repeated deaths: 141/394 in distinct losses versus 31/156 in distinct wins, using the unchanged physical-body/radius6/window250 criterion. Large-bag deaths>=40: 52 events, 4917 lost gems across34 distinct losses. Do not infer that all of this is avoidable or restart a rejected generic watchdog.

## Which champion to inspect first

Same-game, same-hero R100 pairs reduce roster-type confusion. They still share map/draft/role and outcome-selection confounding. The means are per physical body; Cassi and Issac are separate bodies.

| Hero / team result | Paired games | Earned-gold gap | Capture-gold gap | Inventory-cost gap | Collected-gem gap |
|---|---:|---:|---:|---:|---:|
| Cassi / loss | 12 | -7.5 | -15.8 | -2.5 | -1.4 |
| Cassi / win | 5 | +54.0 | +14.0 | +18.0 | +1.2 |
| Issac / loss | 12 | +41.2 | +32.9 | +35.0 | -0.5 |
| Issac / win | 5 | -4.0 | -4.0 | +0.0 | +2.4 |
| Marcella / loss | 25 | -68.0 | -52.3 | -61.2 | -12.4 |
| Marcella / win | 17 | -3.3 | -20.9 | +8.8 | -5.5 |
| Vendetta / loss | 27 | +35.2 | +35.2 | +22.2 | +13.4 |
| Vendetta / win | 21 | +58.1 | +43.8 | +32.9 | +12.5 |

The most specific opening lead is Marcella funding: 25 loss-side pairs versus17 win-side pairs. Her loss-side earned-gold deficit is68.0, including52.3 capture gold; the matching win-side deficit is only3.3. Vendetta instead leads both categories. Inspect the first claimed/captured groups and reward distribution before changing everyone’s shopping threshold.

Within our own pair, Cassi averages9.5 earned gold and4.5 inventory cost atR100 in20 distinct losses; Issac70.2/48.0. In15 distinct wins the direction reverses: Cassi70.7/46.0 versus Issac24.7/8.0. This is a resource-allocation association, not proof that transferring gold, copying a draft or changing twin behaviour would help. Per-appearance denominators and zero-receipt counts are retained in ANALYSIS_DATA.

## Exact current recall/bank timer conflict

The three raw winning-bag-loop matches reduce to **two distinct trajectories** (2/34 distinct losses,0/25 distinct wins). Generic loops remain common in wins too. The following two diagnostic trace builds match their entire original replay bytes; all19 emitted records are trusted. Both maps have no_bank=0 and gated=0, so the observed cause is the private disable timer, not a gated altar.

| Map / actor | Restart rounds | Banked + bag | Enemy banked | Disable-until | HP | Full replay exact |
|---|---|---:|---:|---:|---:|---|
| 00split / 0 | 932–936 | 978 + 30 | 973 | 1011 | 1861.4/2000 | yes |
| 00collision / 0 | 1241–1250 | 891 + 165 | 994 | 1283 | 3129.0/4200 | yes |

At current bot.cpp around6844, safe recall is cancelled because banked+bag is winning. `tribute_if_needed` around4530 refuses while `round < tribute_off_until`; around4634 assigns the80-round backoff after non-progress. At split R932 the timer runs until1011, beyond the original game’s end at937. The trace explains the restart loop, but it does not prove a feasible bank could beat the opponent or that preserving recall wins. The prior v69 bounded cancellation fix is a decision regression result, not a tested v70 release.

Current implementation research should distinguish (a) checking bank eligibility before win-only recall cancellation, from (b) allowing a winning bag to reconsider a stale bank-disable timer after route feasibility changes. The first addresses inconsistent control flow; the second is an untested race-policy hypothesis. Preserve the dangerous-channel escape guard. Do not shorten80 globally or claim these games as rescued wins.

A first split trace attempt failed only when the CLI published a bundle at a long Windows path; it produced no usable trace evidence. That folder is preserved. Shorter output paths succeeded. Failed runs are not omitted from CURRENT_BANK_TRACES.json.

## Concrete map and fuel leads

- **Guardians, 4ed82bb4…:**0–1557, own collected1389/lost1265/carried124,21 deaths and zero fuel-outs. Own R100 cost lead+90 becomes−240 byR250. Our team never banks; enemy first banksR1528. This is a new, separate conversion/capture-state case, not proof that the winning-bag timer conflict caused it. Seven large-bag deaths lose1136 gems. It merits exact bank-route/private-state reproduction before another opening change.
- **Islands:** one distinct loss trajectory repeated twice, margin−184 and10 own fuel-outs per copy. The current source removed the earlier island-escape path. That is a code-risk lead; stranding, fuel origin and whether reintroducing it helps are not yet established.
- **Vault:** the ranked win has28 own fuel-outs; this is28 of50 own fuel-outs across59 distinct trajectories. A second vault trajectory also wins. The incremental siege-scan path was removed in current source, but the native counts alone do not identify the costly call or prove a lost-game effect. Profile that path before modifying it.

## Recommended next research order

1. Keep the two current exact recall cases as source-specific regression contexts. Test eligibility-gated cancellation and stale-timer reconsideration separately with warm state, short horizon and fuel fidelity; then apply the development/cluster/Bayes/release gate to any candidate.
2. Deep-reproduce the new guardians zero-bank loss. Measure altar accessibility, actual bank attempts, private disable timers and visible enemies for each carrier. A high early gem count did not convert into a bank.
3. Review Marcella’s first three assignments/reward receipts in the25 matched loss pairs versus17 win pairs. Diagnose who receives capture gold, who returns to shop and who protects the banker duringR100–250. No global numerical threshold is established.
4. Profile the vault fuel-outs and islands loss with faithful instrumentation. Reintroducing old fixes is a new candidate experiment, not an automatic improvement.
5. For any further match collection, seek existing missing-side and stronger-opponent v70 games. The present BattleCats set is all sideA and contains deterministic repeats. Fresh shared-quota probes would need direct authorization; none was created here.

ANALYSIS_DATA.json contains raw-ID and deduplicated summaries, paired curves, same-hero rows, native fault/fuel counts, duplicate hashes, map tables and per-game numbers. It contains no raw replay or credentials. All85 native summaries report zero bot faults on both sides. The old385/165 split, old predictions, old model and frozen source stay untouched. This addendum supplies new evidence; it does not constitute a production candidate or a ladder-strength claim.
