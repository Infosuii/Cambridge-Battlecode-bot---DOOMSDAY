# V53 plan and experiment ledger

2026-10-25. Baseline: platform v52, live since 12:02 UTC. Read docs/setup.md and all of docs/handoff.md before changes. All additions must run once per call/turn, outside candidate/camp loops. No credentials entered.

## Evidence available at start

- Ranked since 12:05 UTC: 2/5, all against Manta; islands won, fracture/monolith/ambush lost. Too small for causal conclusions.
- Unranked since 12:02 UTC: 4/15. Named queued groups: Hidden Altar Keepers 1/5, meow 0/5; stampede is the single win. Combined 6/20. Separate ranked and unranked in all reports.
- Saved match listings and top-100 ladder under data/ladder/v52_* and v53_*. All 14 current losses and seven recent top-team wins downloaded and decoded successfully (21/21); raw ZIPs/JSONL remain local-only.
- Setup smoke: v52 vs heuristic-v1 rows 2/2, +168 mean gems. Documented stampede v52-v51 smoke reproduces archived results exactly: 5/6, +536. The handoff's blanket 6/6 description does not describe the archived all-seed sweep.
- Logging reproduces boss-battle carriers holding 136-482 gems at R1200, several in cmicro at unchanged positions. Concentrated-wealth has long respawn waits. Profile: scoring ~17-27k fuel/call; yellow-brick-road world turns >60k. Instrumentation changes fuel and is diagnostic only.

## Ranked improvements

| Priority | Hypothesis and implementation boundary | Expected ladder impact (hypothesis) | Measurement / rejection |
|---|---|---|---|
| 1 | Reduce repeated job/claim work in score_groups: compute invariant earlier-ally open-call status once per call. No new candidate-loop branches. | Broad, possibly 1-3 percentage points if fewer turns suspend; uncertain. | bench2 168 vs v52; fuel-exhausted turns, scoring profiles, per-map score. Reject release if target-map gate fails. |
| 2 | Boss-battle objective conversion: compare winner gate timing, damage, draft, item tiers and nearby bodies; remove caster stalemate or choose a proven durable objective draft before trying another rush. | Historically 15/16 losses; recovering half could add ~1 ladder point over uniform 40 maps. | Six boss-battle games must all win clearly; first bank round, banked/carried gems, deaths and gate kills. Then full bench2 and release holdout. |
| 3 | Concentrated-wealth, elkring, swirl, yellow-brick-road: identify repeated idle modes and lost farming tempo from replay and local logs; one cheap fix at a time. | Each historically weak map offers ~0.5-1 overall point if its win rate rises 20-40 points. | Per map six-game both-side/all-seed sweep, capture order, early gold/items, deaths, first bank and bag size; full bench2 for each retained change. |
| 4 | Fit a regularized draft win model using map, both drafts and opponent strength; split by match group/team to prevent duplicate leakage. Compare calibrated held-out log loss to a map/strength baseline. Counter-pick only during draft, where fuel is ample. | Potential several points; raw pick win rates 39-58% are confounded and are not causal effect estimates. | Held-out predictive gain, legal picks and deterministic inference; six target-map games plus full gate before enabling. |
| 5 | Inspect monolith/fracture ladder losses for planning ideas. Preserve the 12 final maps as release-only local holdout. | Unknown until next release; no tuning on local holdout results. | One 72-game holdout per release; disclose ties, regressions and faults separately. |

## Strategy to translate into experiments

- MOBA jungling: clear a route that reaches an item threshold before committing bodies to the gate; compare objective attempts with item spending and allies present. A long forced walk or futile fight costs multiple camp cycles. [Jungling](https://wiki.leagueoflegends.com/en-us/Jungling).
- RTS economy/harassment: evaluate raids by resource denial and our own lost farm, not kills alone; split farming until a time-limited objective warrants grouping. [Harassment](https://liquipedia.net/starcraft2/Harassment).
- Battlecode: early compute overruns and target oscillation can dominate strategic sophistication. Om Nom's 2025 postmortem explicitly describes both as costly bugs; optimize measured work and verify in actual matches. [Money Is All You Need](https://battlecode.org/assets/files/postmortem-2025-om-nom.pdf).
- These are hypotheses for this game's mechanics. Replay measurements and the gate, not analogy, decide what ships.

## Gate and release

For each single change, bench2 against bots/v52. Require clear wins on both sides across all three seeds on declared behavioral target maps; overall win rate >=0.47 and mean margin >=-30; zero faults. For a general fuel optimization, no map-specific behavioral target is claimed. Use the aggregate holdout interpretation documented by the prior v52 release: wins >=50%, margin >=0, zero faults; disclose individual map tradeoffs. The initial plan's extra requirement to identify a target-map sweep for a general optimization was my stricter interpretation, not a handoff requirement. Each release candidate gets its 12-map holdout once; failed variants and repeated exposure must be disclosed, never presented as an untouched holdout. Keep A2_GATE_JOB=0. Record rejected experiments as well as accepted ones. Submit only after all requirements, with measured CHANGES.md; commit/push evidence and update handoff. Then refresh ranked/unranked, queue focused matches, and start v54 from the actual submitted version.

## Experiment ledger

- F1, invariant open-call scan: 87-81 / 168 (51.8%), -2.1 mean gems, zero faults, fuel exhaustion 235 vs 274. Aggregate floor passes. Boss-battle 0/6 (four 0-0 ties); yellow-brick-road 4/6. No target-map gate yet: exploratory, not authorized for submission on this evidence alone.
- Control: unchanged source against v52 reproduces 84-84, exactly zero aggregate margin, mirrored per-map margins, equal fuel counters (265/265). The output prefix `v53-fuel-clear-vs-v52` was launched before the edit applied and is the control, not the optimization.
- F2, 35 redundant immediate bitboard clears removed: 83-85, -8.9, zero faults, fuel 250/246. No clear target sweep. Rejected; patch archived as v53-fuel-clear.patch, source restored.
- D1 exploratory caster-heavy boss draft: 5/6 but four zero-score ties, -601 on the loss; fails clear-margin requirement. D2 exact winning reference draft: 2/6, -60.8. Both rejected. Platform draft-choice IDs differ from champion-type IDs after the linked pair; use the SDK enum.
- D3 draft model: 243,904 archive games, 31 map signatures, 743 team strengths; disjoint unordered team pairs across train/validation/test. Test logloss 0.5925 vs baseline 0.6004; accuracy 64.4% vs 62.8%. Greedy partial-draft match screen: 8/30, -147.1; elkring/swirl/boss each 0/6, concentrated/yellow each 4/6. Rejected for gameplay, retained as an analysis artifact with training/export scripts.
- B1 concentrated-wealth 20-gem safe-bank rule: 3/6, -74.2. Rejected.
- M1 release no-action caster micro verdict to normal controller: 14/30, -65.3; no map 6/6. Rejected.
- S1 sole-gem objective at R700: 4/6, +104.7. S2 R900: 4/6, +125.3. Both rejected by target gate.
- S3 R1100: stampede 6/6, +343.2, minimum margin +54, zero faults. Mean deaths 10 vs 20; mean banked 510 vs 166. Root cause: the R500 forced objective interrupts the gold/item phase too early against the live version. Change is one existing cold-path threshold, A2_GATE_JOB remains 0. Full 168-game gate running; holdout and submission depend on it passing.
- Latest API refresh: ranked 8/20, unranked 27/55 (75 total); downloads/report refresh in progress. Initial 20-game snapshot is preserved separately.
- Refresh complete: all 40 losses plus seven reference wins downloaded, decoded and audited (47/47). The loss report now uses the 75-game snapshot; ranked and unranked subsets are also saved separately.
- S3 release checks: global delay dev 87/168 +12.3, holdout 36/72 -12.2 (elk_arena also qualifies as sole-gem); cached map signature dev 86/168 +11.8, holdout 35/72 -4.1; direct signature dev 83/168 +1.2 but target only 3/6, no further holdout; cached member dev 86/168 +13.2, target 6/6, holdout 35/72 -12.6. All rejected; strongest patch preserved, source restored.
- F3 observation buffer reuse: 79/168, -55.3, zero faults; fuel exhausted 196/241, diagnostic w_vis average about 757 vs 1524 on yellow-brick-road. Fails aggregate margin; rejected, patch preserved.
- F1 release evaluation: exact development source restored and byte-verified against the original recorded build. Holdout 39/72 (54.2%), +5.3, zero faults. Passes aggregate gate as a general optimization; no map-specific behavior fixes retained. This is the final v53 candidate; see bots/v53/CHANGES.md for per-map tradeoffs and limitations.
