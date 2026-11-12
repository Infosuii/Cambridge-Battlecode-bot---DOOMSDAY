# DOOMSDAY structural research, 2026-10-28

Mission: find a substantial strategy gain, provisionally >=5 percentage points, not declare another marginal version a success.
No submission, activation or live-version change is authorized. All frozen baselines remain untouched.

## Initial process audit

Official read-only status confirms repository v74 is live as **platform 68**; platform 69 is repository v75 and inactive.
Latest local v80 is not a proven improvement over v76; v76 remains the established local comparator. The old v67 portfolio's
220/240 in-sample result collapses to 137/240 on untouched seeds, and is not evidence that it is stronger than v76.
An independent-style v76/v80 check against the existing learned mimic completed on all 70 maps/both sides, seed 41;
it failed the opponent runtime check (see below).

Two material methodological errors:

1. `micro.py` calls a turn move-only only when its entire action set is exactly `{4}`. Opponents often also ward/channel/etc.
   Correct `move AND no basic attack AND no cast` changes the 90-loss comparison from **44.7% vs 20.9%** to
   **46.6% vs 42.9%**. The advertised factor-of-two action-waste gap is false. The narrower cast gap remains real.
   Frozen evidence is preserved; corrected output: `corrected_contact.txt` / `.json`, script `audit_strategy.py`.
2. `ladder_duel.py run` **activates** each arm. Submission approval alone would not permit the previously proposed
   "paired ladder tests without activation". No such action was executed. Any later proposal must disclose both operations.

Other weaknesses: proxies preserve our controller, map/seed selection has repeatedly overfit, loss-conditioned correlations
were promoted to causes, total lifetime gold was confused with income at a fixed round, and many apparently new architectures
were tested before proving their low-level farming/visibility/lifecycle contracts. The new experiments must isolate these.

Exact native ladder income in the same 90 losses: R100 283 vs 381, R200 631 vs 844, R300 996 vs 1,407;
R500 1,763 vs 2,767 on 87 game pairs that reach it. This includes kills and passives, avoiding net-wallet undercount.

## Three materially different candidate families

1. **Unified action-sequence planning.** Keep proven strategic/lifecycle decisions initially, replace fragmented combat execution
   with a legal sequence planner for step/dash/cast/attack/reset, using engine damage queries and explicit final position.
   Upside: close real damage/conversion gaps without forcing stationary casts or changing life-value thresholds.
   Cost: medium; bound enumeration and leave a hard fuel reserve. Falsifier: a shadow oracle finds few missed useful sequences,
   or engine action legality/damage predictions disagree. Existing tactical search omits/truncates actions and uses a model;
   simply switching it on would repeat previous experiments.
2. **Event-based team economy scheduling.** Allocate parallel crews to full clear/capture/reset cycles using camp state,
   arrival times and marginal team income, with explicit job ownership and completion events. No permanent carry pilgrimages.
   Upside: richer opening captures and less duplicated travel/staging. Cost: high; 8-byte shared-state contract is a core limit.
   Falsifier: on isolated uncontested maps, planned cycles do not beat baseline R200/R300 income after travel and health costs.
   Previous director/crew failures must be diagnosed rather than renamed.
3. **Opponent-conditioned strategic policy.** Learn/derive a compact policy from current top-vs-top games to select invade,
   farm, bank and fight contexts with draft-aware combat power, retaining legal exact execution. Upside: replace lineage-biased
   local objectives and raw-HP "even fight" assumptions. Cost: high data/model validation, low bounded runtime inference.
   Falsifier: out-of-team/off-map policy validation shows no predictive advantage over baseline decisions or no positive engine
   counterfactual value. Existing mimic is a diagnostic opponent, not proof imitation itself will win.

First implementation direction will be selected after the action-opportunity and current-replay audit. Do not repeat loose
threat sharing, forced nuke-before-flight, or stat/passive swaps as the main research effort.

## Executed research cycle

### Family A: bounded action sequences (bots/v81)

Implemented route/spell/basic/reset enumeration on top of frozen v76's strategic verdict. Spell damage uses official target
effect queries; basic damage/response are still approximations, not an exact simulator. Source `sequence.cpp`, initializer
`init_experiment.py`. Disabled control Wasm SHA equals v76 exactly: `42071fa6...`.

12-game diagnostic, six combat maps/both sides, seed 42, identically logged control:
- First implementation: 2/12 vs control 7/12, own fuel 35.92/game. Invalid strategic evidence: candidate generation lacked
  a fuel guard. This was fixed before any broad benchmark.
- Fuel-corrected: 4/12, paired margin -532 [-821,-243], deaths +3.8, gold -1,513/game. Runtime 0.50 vs 0.17 fuel/game;
  2,771 plans, zero logged action errors, zero cross-round execution, median plan cost 10,691 fuel/max 19,033.
  Contact act share rises 56.2% -> 57.0% while health lost rises 3.0% -> 3.5% of max/contact turn. Immediate damage and
  complete sequences are not a sufficient combat objective. Do not run 140 games to confirm this diagnostic failure.
  Preserve as a research tool; pivot to another strategic family rather than tune risk constants.

### Family B: event-based coalition scheduler (bots/v82)

Implemented atomic joint assignments in the existing 8-byte protocol, explicit ready handshake, persistent clear jobs,
single-capturer release and all available coalitions priced in worker-turns. Preserves baseline combat/items/roster/SDK
executor. Domain: <=48 groups through R300; fallback thereafter. Disabled control is also byte-identical to frozen v76.

First uncontested 12-game mechanism test (idle81, no competitive-strength claim): R100 gold -89, R200 -95, R300 -115;
R200 collected gems -67. Inspection found a real execution contract failure on 02arena: Cassi assigned group 6 (corner
gold at 1,1) alternated tiles (4,4)/(5,5) from R20 to R200 with zero gold. Durable scheduling kept a job the old local
chooser would abandon. Added a progress contract based on approaching the job or reducing remaining camp HP, with a
bounded release and reauction on failure. Corrected SCHED82D-contract still loses R100/R200/R300 gold by 88/96/110
and R200 gems by 76 on the same 12 games (10 pairs reach R300). This fails even the uncontested acceleration premise.
Do not broaden this auction model without a new model of actual travel/clear execution. Frozen output:
`scheduler_contract_economy.txt`. Baseline and candidate have zero bot faults; candidate fuel 0.17/game.

### Family C: learned tactical intent (bots/v83)

Extracted 50,912 legal top-side contact observations from 120 ladder replays, first 500 rounds. NumPy histogram CART,
33 features, depth 5, min leaf 250, 57 nodes. Four whole-opponent folds: accuracy 56.0-61.3%, majority 53.0-56.4%;
confidence >=0.65 covers 34.4-47.1% with 69.1-79.3% accuracy. Labels are observed retreat/hold/engage, **not**
counterfactual value. Frozen model `intent_model.h`, full results `intent_validation.json`. Native C++ predictions on
1,019 actual held vectors are class-identical with <1e-5 confidence error. This verifies inference, not transfer value.

Runtime chooses an engagement stance before the mature v76 executor; no hold prediction overrides. V83_INTENT=0 is
byte-identical to frozen v76. Initial 12-game screen: 7/12 vs 7/12 control, margin -43, no runtime collapse. Broadened
once to 140 paired games/opponent, all 70 maps/both sides, seed 42:

| Opponent | Win delta | Map-cluster 95% win interval | Gem margin delta | 95% margin interval |
|---|---:|---:|---:|---:|
| v65 | +3/140 = +2.14 pp | [-8.57,+12.14] pp | -20.1 | [-139.1,+104.3] |
| proxy per team | -8/140 = -5.71 pp | [-13.57,+2.86] pp | -65.3 | [-167.4,+33.4] |

Deaths rise +0.4/+1.5 per game. Exact R300 income falls -19 [-86,+46] / -39 [-95,+15]. Original ladder measures,
now with corrected movement definition, show early equal-number/HP fight deaths rising .41 -> .59 and .32 -> .56;
split-hit-out improves 17.2% ->15.5% only versus v65, not enough to offset worse survival. R500 dead share rises
11.8% ->12.8% and10.8% ->12.3%. Reject this imitation arbitration; matching top action labels lacks fight-value and
coordination context. Do not interpret classification accuracy as competitive strength. Results `intent_*paired.txt`,
`intent_replay_metrics.txt`, `intent_*native.txt`; run prefixes INT83-base/policy. All schedules/provenance verified.

### New user evidence: match group 18208504

The user directed us to `research/v75/MG_18208504.md`: a fresh 0-5 versus SkibidiSloppers. This changes priority.
Yellow brick road: our adjacent harmless 600-gold home group collected once (R740); opponent's home group generated
9,667 gold. We drift across the map and suffer an opening wipe. On fields we win 9 kills to4 and still lose by547.
Collision carriers orbit one contested altar with40-70 gems; ribs/famine expose objective trickling.

The geometry follow-up changes that explanation: group0 is30 camps `(5..34,17)` and group1 is30 camps
`(34..5,12)`. Both600-gold strips span BOTH teams, so a first-camp territory classification is wrong. Group1 is
already clear/reward-available atR40 in the ranked loss. Capture control matters alongside clearing. The MG write-up
now records this correction, and all5 actual ranked games have exact-turn audit500 data.

### Family D: shared-region income denial (bots/v84)

Two guards occupy safe endpoints of the600-gold shared strips, contesting capture and preventing respawn while other
workers farm. Two-side yellow-brick-road proxy mechanism test:0/2 vs1/2 baseline; margin-886.5 vs+344.5. R300 own
income-1890, collected gems-36, deaths-3.5. Denial starves our development and does not convert to victory. Reject
this implementation; no broad benchmark. `denial_economy.txt`, `denial_captures.txt`.

Initial HOME84D-trace2 logging is INVALID behavior evidence: it called group_distance before checking has_field,
reading garbage distances and producing90.5 fuel-outs/game. No causal or strength claim uses that trace. Unmodified
HOME84D-baseidle/baseproxy and the actual ranked replay are the evidence. Do not rerun the trace initializer unchanged.

### Family E: concentrated-resource rendezvous and cycles (bots/v85)

Geometry detects >=60% gem value within a compact region, assembles a team at a safe approach, then clears/captures
and vacates spawn tiles for another cycle. Existing fight/home/bank execution remains higher priority.10 games,
5 concentrated maps/both sides vsv65:6/10 vs8/10; margin-231[-717,+307], gold-1790/game, fuel0.4vs0.1. Ribs R300
gem collection+93 but final margin-205; concentrated-wealth+686, stampede-975, boss-battle-713, famine+54. Initial
harvest improvement does not establish competitive strength. Gear prerequisites and bank/return phase are unresolved.
This is not a finalist. No full140 screen. Before broader use, bound geometry's nested loops by an explicit fuel
deadline. Disabled v84/v85 source controls were prepared but NOT built/checked; only v81-v83 have byte-equality proof.

**Paused at the user's request.** No experiments running. Precise continuation: `HANDOFF.md`; portable start:
`CONTINUE_HERE.md` at repository root. No platform action was taken.

### Evaluation repairs and new evidence

- `run_experiment.py` fails on build/run errors or incomplete/duplicate games, records CLI/SDK/frozen source/Wasm hashes,
  checks actual engine identities and faults for both teams. `paired_strict.py` verifies same complete schedules, exact
  opponent/map hashes and runtime identities, then reports map-cluster gem and win-rate uncertainty.
- Learned mimic opponent was tested once, all 70 maps/both sides, seed 41: v76/v80 each 140/140. Mimic averaged 81.7/86.7
  fuel-outs/game. This opponent is **invalid for strength evaluation**, not evidence of a breakthrough. No more such tests.
- Seven fresh ranked replays cover all current top-12 selections (several pairs share the same match). Data and listings
  under artifacts/local-only/v81-current, index `current_top_matches.json`, native summary `current_top_summary.txt`.
  These are descriptive checks, not a candidate evaluation. They warn against an economy-only success criterion: Mite
  and Trzy win some games despite less early gold; objective conversion and composition matter too.
- Actual top-12 now include newer team, Ad Astra, policy wonk and Sponge; the older duel/proxy set is incomplete.
- Found pinned public current-rule sources: Midnight Wardens (AboRokya/khiribot2) and gamebot submission-v9.
  Downloaded only inspected C++ source into bots/public-*, provenance `public_sources.json`. Compile helper now permits
  independent sources without our NOVA_SEED protocol, compiling those unchanged. Each played only12 diagnostic games;
  v76 won all but opponent fuel-outs/game were84/108/977. **Invalid competitive opponents**, no more strength tests.
  Earlier web search results for Coook13/TymonM/Ismail are the different Easter builders/conveyors ruleset, discarded.
  No published current top-12 source obtained. Official upstream GitHub is unavailable (404 through connected account).
