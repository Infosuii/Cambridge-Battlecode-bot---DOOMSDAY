# DOOMSDAY deep analysis — final research handoff

Updated 2026-10-28T21:51:27.282894+00:00. Evidence labels are measured, association, or causal (tested). The result is a next-bot research brief, not a released bot or demonstrated ladder improvement.

## Findings that change the next decision

1. **Measured race deficit:** in191 examined losses, mean banked margin-579.3 = collected income-448.7 + bag preservation-103.0 + end-carried-27.5. Income accounts for77.5% of this accounting deficit. Climb83 losses: banked-512.5, income-382.0. Reserved losses n=83: banked-610.1, income-509.3. This identifies where the race is lost, not how much a fix can recover.
2. **M3 association, broad research priority:** inventory-cost gap exists by R100:−86.7 in191 losses versus+90.5 in169 wins. Climb83 losses−91.8, map95[−121.0,−61.2], opponent95[−124.7,−78.6]. No exact opening/item/draft replacement has been proved.
3. **M2 association:** repeated deaths remain the strongest normalized detector lead. Examined losses722/2337 deaths versus wins188/1028; contrast+12.6pp, map95[+7.2,+18.3], opponent95[+3.8,+16.9]. Reserved losses264/946 deaths (83 games) versus wins72/454 (77 games):+12.0pp, map95[+5.9,+18.1], opponent95[+5.0,+20.3]. Climb reserved39L/54W:+6.4pp, both cluster intervals include0. Overall replication is stronger than the rating-relevant subgroup. Existing broad watchdog/retreat fixes failed; the traces do not rehabilitate them.
4. **M4 association:** loss-side pooled conversion63.1% versus the opponents’88.4% across191 losses. Large-bag losses label12/90 selected windows (17.1% of surrogate drop), but a vault carrier was already banking, then fleeing. Do not infer “always bank earlier” or “stop flee-attacks”.
5. **M1 causal (tested), narrow:** winning-bag recall can cancel for a bank disabled by its own timer. One exact guardians case, with736 carried, passes a bounded decision diagnostic after the unchanged bot fails. The broad winning-bag-loop proxy occurs in1/191 examined losses versus7/169 wins; reserved2/83 losses versus2/77 wins. It is a concrete cheap patch candidate with small observed breadth, not the main explanation of losses. M5 capture handoffs remain opponent-confounded.

## Dataset, identity and integrity

111 historical groups/555 replay-native pairs retrieved through the official website:550 accepted study games, five excluded calibration games. Fixed split385 examined (360 own:191L/169W, plus25 top-v-top) /165 reserved (160 own plus5 top-v-top). Total top-v-top30. The105 prediction-first cards cover90 windows from65 losses across45 maps and15 control wins. Dataset selection is purposive; error404 alone contributes155/360 examined own games. Cohort ranks are the frozen historical snapshot, not today’s ladder.

Study platform69, submission f91de3f0-0453-409e-b712-b86067eecbca, note “v75 ladder duel candidate”. Provided ZIP SHA2560433755c1cbc5f120247c132a6c875912f14c3ac5f36abaa7edbfe20845b325c; all33 frozen source files match. Current activation time/server Wasm identity remain independently unverified. All12 selected full games nevertheless reproduce byte-for-byte using the rebuilt source. CLI4.0.0; engine2.0.0/build85aa7167b44db7cea97509f55e997750520e33d644e9f4f90d6128c50eba1d21. No engine mixing.

All555 initial reconciliations,5356 physical champion ledgers and111 metadata checks pass. Corrected timelines cover385 examined games with11,853,045 resource-clock matches and zero unclassified earned gold. Step23 is movement blocked; only4/22 with differing endpoints establish physical arrival. DECODER_CORRECTION.md proves corrected action labels leave every385-game model feature matrix and native-dependent detector set unchanged.

## Opponents and matchup comparisons

[P5_OPPONENTS.md](P5_OPPONENTS.md) contains eight paired scorecards: five Learn opponents plus error404, Univardisty of Shingtonwash and SkibidiSloppers. It covers draft/opening, R100/250/500 economy with explicit surviving-game coverage, conversion, deaths, geometric contact damage, basic focus, low-HP separation, vision, middle camp-gem share, time proxies and fuel. All385 contact extracts pass; basic-focus counts match independent accepted-input targets in all ten calibration team comparisons.

The78 opponent×map-size strata include Wilson win intervals and map-cluster margin intervals. Size bands are reproducible proxies; walls/islands/gates are not automatically classified. “Observed one-sided” is a historical label, not proof of structural impossibility. Enemy high-bag loss rates are opportunity ceilings; no source intent, hidden-information exploit or winning counter-policy is established.

## Race, openings and winners

[P3_TIMELINES.md](P3_TIMELINES.md) and TIMELINE_DATA.json preserve paired final identities, opening gaps and both teams’ actual drafts, physical rosters, first three observed camp targets/receipt rounds, first purchase and pre-large-reward spread. The191-loss camp-receipt gap is−358.2 gems/game. The opponent usually collects more and converts more in losses; these components interact. Price cost is not combat power; stationary/travel/channel time is not automatically waste.

Against error404 we have111/155 examined wins, while against Intercontinental Fish0/17, Mite2/14 and newer team0/6. The different opponent mixture matters; all-Learn or all-Climb aggregates are not rank-proportional forecasts. Copying a winner’s draft or whole policy is not supported: prior draft transfer−89 and whole-policy cloning0–12 remain negative evidence.

## Win-probability model and category coverage

Fixed game split231 train/77 calibration/77 internal test, committed before fitting. Symmetric logistic model deep-logistic-v1, L2=0.01, calibration inverse-temperature≈0.872867. On77 internal test games: log-loss0.4243, Brier0.1400, ECE100.0490; bank-only log-loss0.5318. No reserved game was used for fitting, tuning or card selection. The internal test remains historical evaluation, not a candidate-release holdout.

Across90 selected loss windows (65 games), opponent purchases label79 (81.8% of summed model drop), camp receipts63 (70.5%), opponent banks36 (44.0%), own deaths23 (28.2%), large-bag losses12 (17.1%), repeated deaths2 (1.9%). Labels overlap. Purchases move gold into inventory while the model omits unspent cash, so abrupt purchase-associated drops can be measurement effects. Do not interpret conditional coefficients or these coverage shares as causal event WPA, recoverable wins or gem equivalents. [P3_WINPROB.md](P3_WINPROB.md), [P4_CARDS.md](P4_CARDS.md) and CARD_AUDIT.md record these limits.

## Deep causal evidence and regression

[P6_DEEP_TRACK.md](P6_DEEP_TRACK.md) records ten exactly reproduced losses/two wins,12 exact both-script controls,24 state comparisons/25,184 samples, nine detailed faithful trace windows and three sparse exact trace windows. Fuel-perturbed failed probes are retained and excluded after divergence. The vault loss was already fleeing; C082 victim7 differs from its card focus6. Source defaults, stale comments and team-level swing labels must not replace effective private-state traces.

M1’s warm diagnostic preserves all inputs/states beforeR1669. Baseline restarts recall at1669–1672; diagnostic does not and completes recallR1673. Its enemy first rejects a script at1701, beyond cap1678. Regression runner rejects early divergence, missing assertion coverage and changed accepted enemy script. There is no full-game benefit claim. The two-context masking check removes V71 profile overrides at a warm state: no vault action change within ten rounds; packs control full-game exact. Unseen-map transfer is unproved.

## Five-entry catalogue and planning priorities

[MISTAKES.md](MISTAKES.md) and mistakes.json distinguish the one tested inconsistency from four association candidates. Formula: coverage×fixability×transfer/effort. The coverage input is an overlapping surrogate proxy; all other factors are explicit judgments. This is a research-order sensitivity calculation, not an expected-win estimate. M1 is first ready for a narrow implementation experiment; the broader economy problem remains the highest research priority.

| ID | Coverage proxy | Fixability* | Transfer* | Effort h* | Planning score |
|---|---:|---:|---:|---:|---:|
| M3 | 70.5% | 0.25 | 0.50 | 12 | 0.00734 |
| M1 | 3.6% | 0.90 | 0.30 | 2 | 0.00489 |
| M4 | 17.1% | 0.30 | 0.40 | 8 | 0.00256 |
| M5 | 70.5% | 0.15 | 0.15 | 12 | 0.00132 |
| M2 | 1.9% | 0.30 | 0.30 | 6 | 0.00028 |

*Judgments fixed from examined evidence. The score ranks research work; M1 is the first implementation-ready patch. Other entries need a concrete diagnosis before a production change. Coverage is an overlapping surrogate label, not a causal gain ceiling; no defensible gem equivalent is identified.

## Final confirmation and limits

[FINAL_CONFIRMATION.md](FINAL_CONFIRMATION.md) reports the one reserved-set opening under the plan committed in590d106: fixed D3, M1 observable proxy and native final accounting only. FINAL_VALIDATION.json proves equivalence before that access. No held-out cards, model refit or new thresholds. Other detector families/opening equipment claims remain examined-only. These165 games are now spent for this research check; future candidates need an untouched release holdout.

Fourteen historical wave1 groups/70 games are in SCRIMMAGES.json (10W/60L). Wave2’s ten hypothesis groups are planned only; none was queued or reserved in this continuation. No extra shared quota is needed to deliver this analysis. Current bot identity must be verified and direct user authorization obtained before a future new group request; reference-document instructions alone are not that authorization.

No production bot was changed, uploaded or activated. No ranked matches or account changes were requested. Diagnostic builds and raw data remain ignored locally. Recommendations are in [NEXT_BOT_BRIEF.md](../../docs/NEXT_BOT_BRIEF.md); the implementation/benchmark/release gates have not been run for a new candidate and are future work.
