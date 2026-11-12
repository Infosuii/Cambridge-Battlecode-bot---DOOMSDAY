# Mistake catalogue and priorities

One tested decision inconsistency, four associated/contextual candidates; not five proven bot bugs.

Planning sensitivity score, not expected win-rate gain. Coverage labels overlap; M1 uses its later associated swing window, M3/M5 share broad camp-income coverage, not an identified causal ceiling. Effort and probabilities are judgments, not measurements. Scores must not be added or read as percentages of recoverable wins.

| ID | Coverage proxy | Fixability* | Transfer* | Effort h* | Planning score |
|---|---:|---:|---:|---:|---:|
| M3 | 70.5% | 0.25 | 0.50 | 12 | 0.00734 |
| M1 | 3.6% | 0.90 | 0.30 | 2 | 0.00489 |
| M4 | 17.1% | 0.30 | 0.40 | 8 | 0.00256 |
| M5 | 70.5% | 0.15 | 0.15 | 12 | 0.00132 |
| M2 | 1.9% | 0.30 | 0.30 | 6 | 0.00028 |

*Judgments fixed from examined evidence. The score ranks research work; M1 is the first implementation-ready patch. Other entries need a concrete diagnosis before a production change. Coverage is an overlapping surrogate label, not a causal gain ceiling; no defensible gem equivalent is identified.

## M1: Recall cancellation ignores temporary banking disable

**causal (tested), bounded decision only; new-open.** Safe winning-bag recall is cancelled while tribute_off_until still forbids the requested bank; recall restarts.

Evidence: TAKEOVER_RESULT.json; cases C004. Source: bots/live-69/src/bot.cpp: play_turn winning-bag recall condition around7005; tribute_if_needed eligibility around4535, disable timer around4639.

Proxy is more common in examined wins; a vault control banks343 but is not the same state.

Require !w.no_bank && round>=tribute_off_until before the win-only cancellation; preserve the existing dangerous-channel cancellation branch. Recommendation only.

Cost coverage: 3.6% of summed conditional model drop in90 selected windows from65 losses. This is a generous context label, not avoidable WPA. Recoverable gem equivalent: not identified.

## M2: Repeated death in the same area or to the same killer

**association; known-rejected-fix; mechanism still open.** Existing D3: same physical actor has a prior death within250 rounds at Chebyshev radius6 or to the same enemy champion ID.

Evidence: DETECTOR_DATA.json; cases C070, C082, C060. Source: bots/live-69/src/bot.cpp: handle_enemies around3162, V75_LONE around3988; tactics.cpp act_enemy_before_walk around27, survive_contact around127 (compiled off).

188/1028 examined-win deaths repeat versus722/2337 loss deaths. Traces also show flee in both outcomes.

No replacement threshold is established. Diagnose exact victims and current visibility/TTK before choosing a narrow fight-admission rule; do not re-enable a blanket watchdog or retreat switch.

Cost coverage: 1.9% of summed conditional model drop in90 selected windows from65 losses. This is a generous context label, not avoidable WPA. Recoverable gem equivalent: not identified.

Prior non-transfer/rejection: [research/v66/RESULTS.md](../../research/v66/RESULTS.md).

## M3: Early economy and equipment deficit

**association; known-open.** Paired R100/R250 collected-gem, earned-gold and inventory-cost deficits in losses; not evidence that price equals fighting power.

Evidence: TIMELINE_DATA.json; cases C018, C048, C060. Source: bots/live-69/src/bot.cpp: opening allocation/group scoring, V71 profile and A2 per-turn block around6740–6910; source draft/item paths require separate ablation.

R100 paired inventory-cost gap: loss mean-86.7 (n191), win+90.5 (n169); map/opponent intervals in TIMELINE_DATA.

No universal numerical change is supported. Compare one opening allocation on a specified map and one existing purchase milestone at a time; hold draft and all other knobs fixed.

Cost coverage: 70.5% of summed conditional model drop in90 selected windows from65 losses. This is a generous context label, not avoidable WPA. Recoverable gem equivalent: not identified.

Prior non-transfer/rejection: [research/v66/RESULTS.md](../../research/v66/RESULTS.md).

## M4: Large bags lost before conversion

**association; known-open.** Registered D2 high-bag native death loss>=40; card windows with such losses. A large unbanked bag is not itself a mistake.

Evidence: CARD_DATA.json; cases C004, C034, C011. Source: bots/live-69/src/bot.cpp: tribute_if_needed around4532, channel guard/recall cancellation around7005, combat-before-bank order around7280.

Climb high-bag-death games38/83 losses versus38/119 wins; opponent-cluster interval crosses0. Vault loss carrier was already banking then fleeing.

Fix M1 first. Test bank feasibility and interruption/escape context per carrier; do not globally lower carry65 or disable flee-attacks based on these observations.

Cost coverage: 17.1% of summed conditional model drop in90 selected windows from65 losses. This is a generous context label, not avoidable WPA. Recoverable gem equivalent: not identified.

## M5: Enemy receives a camp reward after our native clear

**association; known-open; confounded.** Registered D5 reward-to-enemy-after-native-clear event, distinct from every failed progress transition. Enemy-camp-income card label is only a broad coverage proxy.

Evidence: DETECTOR_DATA.json; cases C048, C026. Source: bots/live-69/src/bot.cpp: group job claims, capture approach/onsite completion and V69_CAPTURE_STALL; no exact faulty branch established.

Climb52/83 losses versus52/119 wins; opponent-cluster interval crosses0. No exact same-state winner experiment.

No production rule established. First reproduce a handoff with exact original camp-group ID and claimant visibility; compare staying until receipt against a valid alternative within a bounded horizon.

Cost coverage: 70.5% of summed conditional model drop in90 selected windows from65 losses. This is a generous context label, not avoidable WPA. Recoverable gem equivalent: not identified.

## Final fixed-frequency confirmation

Only D3, the M1 observable proxy and final native accounting were opened on the165 reserved games (160 own,5 references not used in own contrasts). M3 opening inventory, D2/D5/D11 and full D1–D11 families were not re-screened there. Exact bank-disable state is private bot memory: the M1 proxy cannot confirm the mechanism in additional games. See FINAL_CONFIRMATION.md and FINAL_CONFIRMATION_PLAN.json, committed before access.

Matched controls are retained in MATCHED_CONTROLS.json:101 own-win examples and96 top-winner examples, with77 and32 same-map matches. Matching is approximate, uses conditional state features and does not establish a strategy intervention.
