# Agent A working notes (memory across context compaction)

- bot/src == references/original-src except bot.h (friend decls) + untracked nn_config.h/nn_budget.h.
- Active macro config: common.h lines 1-96 (A2_ROUTE_FUEL 55000 at line 1, A2_LAB 1, A2_KNOBS ..., A2_GOV 1, ...).
- Fuel call sites (decision-gating): bot.cpp 702,1003,1064,2323,3258,4868,4869,5142,5186,5265,5369,5455,5456,5639,5640,5814,5829,5832,5834,5836,6349,6352;
  tsearch.cpp 124,532,560?,571?,609?,797,805,906?,939?,952?,994,1033?,1044?; draft.cpp 542 (A2_DPLAN=0 -> dead); world.cpp 643;
  runtime_budget.h:29 rb::left(). Telemetry-only: common.h prof/a2tel, bot.cpp 1917/1980 (f0 telemetry?), 2325-2334 APEX_ESC*, 6518, world.cpp 43-48, tsearch 447/778/931/963/1127 (check).
- lab exports in main.cpp (12 exports: lab_learner_w, lab_ctl, lab_knobs, lab_pol_w, lab_pol_cfg, lab_pol_log, lab_macro_feat, lab_cn_w, lab_cn_cfg, lab_cn_force, lab_cn_log, lab_builds).
- SDK: game constants runtime (cambc.h:31-56 struct, 83-176 constants). Champion designs runtime via sdk_champion_design. Plan: probe bot to dump metadata.


## Lab facts
- lab::knobs[48] = {A2_KNOBS 24 vals}, idx 24..47 = 0. Used: play_turn 5947-5989 (k0..15,22,23,33,34,43,44), handle_enemies 2807-2820 (16..21), LABK 35 items_of, 36,37 tribute, 38 cohesion score_groups 5037, 39 ward_ahead 1728, 40 mid 4903, 41 tf_engage 3479 (0 => block inert), 42 prelock 1573, tsearch 24..32 (884-896, 981, 1136).
- learner::on=true under A2_LAB with w_lab[16]=0 -> fix() == score*1.0 (identity); gather() at bot.cpp:5131 costs fuel. Without lab: on=NOVA_LEARNER(0)=false.
- lab::builds checked in build_for (bot.cpp:56-67), all zero -> inert.
- lab::ctl (champ=-1): play_turn 5994-6038 (macro_feat+ctl rec), 6149-6180 (kinds 6/7), handle_enemies 3525-3546 (4/5), tribute_if_needed 4036-4039 (2/3).
- pol_* only under A2_POLICY(=0) -> already compiled out. cn_* only under A2_CAMPNET(=0) -> already out. 4881 `(A2_MID_W != 1.0f || A2_LAB)` builds mid_group.
- main.cpp exports 7-23.

## play_turn chain (bot.cpp 5843+): brain::load/adapt -> knobs block -> lab ctl -> shared=read_shared -> dead: shop, write_claim(dead), build_fields, return
  -> refresh_self -> channel guard -> w.update -> beliefs -> read_sighting/share_sighting -> APEX_EVENTS publish -> shop if on spawn/tavi
  -> support_casts -> ward_reveal -> counter_ambush -> fought=handle_enemies() [~6315] -> chain: fought? opportunistic_attack : win_now&&tribute_if_needed "tribute-win" : go_home_if_needed : hunt : tribute_if_needed : farm (+opportunistic_attack, support_casts)
  -> drop_ward, ts_prewarm, prelock_altars, update_priority, build_fields.
## handle_enemies (2734-3784): try_lock_altar, try_burst_kill(kBurst), bush_ambush; target selection loop (key=ttk/worth) -> `target` (EnemyRec*), winning/in_danger flags;
  TFC/team_decide block (~2990) -> tactical_decide verdict (3228) -> TD_AUTH -> fightsim(off) -> teamfight LABK41 block (inert) -> lab ctl 4/5 -> deny_tribute -> bush-recall -> tactical_search (c1_acts) -> melee_caught(kStand2) -> caster_micro -> flee-hit -> escape_or_stand -> flee (ranged flee/run_escape/retreat_from) -> engage: kite-cast, kite_step, position_and_attack, attack/cast, gap-dash, fight-cast, chase walk_toward.
## shop() 533: altar_lock if kAltarLocks; then build_for(type) steps, buys `want` shards (30g each). build_for 54.
## walk_toward 696 (fuel gate 702), follow_field 648 (candidate steps sorted), try_dash 598, retreat_from 1192 (cands sorted), regroup_from 1172, greedy_step 1027, travel_around_threats 1063 (fuel 1064).
## Shared mem: 8 bytes u64: 6 claim slots x7 bits (0-41), sight x 42-48, y 49-55, round 56-61, distress 62, bit63 = APEX_EVENTS group-event flag (x field = group, y field = respawn round mod 256). Claim codes: group idx, 112-117 fight order engage enemy k, 118 retreat order, 126 dead, 127 idle.


## Objective/bank/strategy hooks (read)
- score_groups 4780-5200: locals `top[8]` RouteCand {gi,need,value,cost,score,finish} sorted desc (keep=clamp(kRouteK,1,8) since APEX_ROUTE_DEPTH=2), `best`, best_need, best_score; fuel gates 4868 (kDet: evaluated>=kDetScoreN || fuel<kDetSafety), 5142 belief (kBelief), 5186 route gate (> kRouteFuel=A2_ROUTE_FUEL 55000) -> route_search/plan_search(kPlan) returns pick idx into top. Hook: after route block (line ~5195), before `#if A2_CAMPNET` / `return best;` (5197-5200). learner gather/fix at 5131-5141 (A2_LAB).
- farm 5442-5740: low_fuel (5454-5456) keeps target_group; escort/rolesquad/squads/duo/pair; `if (best<0) best=score_groups(...)` 5636; chip-at-big 5639; plan-bank; commit: `if (best != target_group) {...} target_group = best; write_claim(best);` (~5662-5667). Hook objective: immediately before `if (best != target_group)` at ~5662 (after plan-bank block). Then switch on g.state -> capture/to-capture/wait-respawn (UseWaits: force_tribute/go_home)/fight_camps(g,best_need).
- tribute_if_needed 4031-4178: verdict `go` (4111-4112) from force_tribute|wins|late|end_bank|rhythm|edge|gems>=kTributeCarry|dist<=kTributeNearDist+..|threatened. Altar = nearest via w.altar_field (or safe_field when gems>=15 & threat), at dist==0 loops w.altars (lock attack / submit_gems). Hook bank: after `go` computed (line 4112), before `#if A2_ALTARFIX & 2` (4113).
- go_home_if_needed 3948-4029: on_spawn heal stay; low/rich(gold>=kShopGold)/heading_home; recall if dist>kShopWalkDist && !enemy_close; else follow_field(spawn_field).
- hunt 3879-3946: snipe(kSnipe), distress rescue (kDistress), hunt sighting (kHunt, kHuntGems, kHuntHp, kHuntRange). 
- Chain in play_turn at ~6315-6338.
- support_casts 1510 (shield/heal target best by missing hp), cast_on_enemy 1396 (best slot by value; striking dash aim), cast_on_camp 1347, use_reset_and_attack 1287, attack_unit 1270.
- drop_ward 5751 (kWards=APEX_WARDS 0 -> returns immediately).


## PROGRESS (after ~111 matches)
- 01 fuel patch: agents/A/patches/01_fuel_routing.diff; p01 wasm byte-identical to original (sha eb0ea88f...). evidence/p01_build_compare.json
- 02 strip: NN_STRIP_LAB=0 identical (evidence/p02_strip0...). =1: code 283470 vs 291789 bytes, 12 lab_* exports removed (14->2). eq vs original 12 maps x2: 4/24 equal, 9 outcome changes, cand wins 15 vs ref 12 (evidence/eq_strip_lab_1_vs_original.json). variant s2 (keep learner+mutable knobs, strip exports/ctl/builds): 6/8 equal (eq_strip_variant_s2.json) -> any fuel change perturbs.
- 03 capture: nn_teacher.h/.cpp in bot/src; patch 03; heads off -> byte-identical (p03_off, stack_off of 01+02+03). Shadow selftest (all heads shadow + kFuelCredit) 4 matches + draft check: 0 violations (evidence/capture_selftest.json).
- equivalence tool: tools/audit_equivalence.py; schedule tests/fixtures/teacher/schedule.json; reference_digests.json (48 cells). orig A/B pairs identical 12/12; repeat 8/8 equal; first-hour 0/16 equal.
- SDK probe: evidence/sdk_probe_facts.jsonl (2 matches). printf ~65 fuel/char. replay.repl26a has no names/paths.
- B is editing bot/src concurrently (nn_budget.h includes nn_registry.h). Scratch uses frozen base (git HEAD + agents/A/base_stubs + nn_teacher.*).
- TODO: sdk_facts.json, AUDIT.md, decision_inventory.json, INVARIANTS.md, REPORT.md, final git apply --check.

## DONE (wave 1): all deliverables written; final_* evidence supersedes earlier stack/plain builds. 111 matches total.
