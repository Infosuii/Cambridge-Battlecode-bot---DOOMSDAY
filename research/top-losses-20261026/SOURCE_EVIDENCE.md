# Source evidence snapshots

Exact excerpts from the local v62c source inspected during the audit. These explain code paths; they are not a causal attribution for every game. The duel arm maps to platform63 by recorded group IDs. This review did not rebuild to prove binary-to-source equivalence. Earlier unconditional definitions can override later defaults; use effective-macros.txt for the preprocessed values.

## bots/v62c/src/bot.cpp:58

SHA256: 9fed2bbf32eafd40d14ddae2b79fac8d9b38311adb70a460d5ad33ca0224afc5

```cpp
58:     // 2: v58's passive emblems, then Bruiser stacks in place of Greed (a 25-shard Greed emblem pays nothing until its
59:     // 750th gold; our champions rarely got there). 3: only the first three v58 emblems before the stacks.
60:     {
61:         using ct = bc::champion_type;
62:         const bool focus_user = t == ct::cassi || t == ct::stellar || t == ct::prism || t == ct::willow || t == ct::marcella;
63:         const bool tank = t == ct::heart_of_ruin, ranged = t == ct::vesper_vale || t == ct::tavi;
64:         std::vector<BuildStep> v;
65:         if (t == ct::marcella) v = {{it::jungle_shard_of_strength,5}, {it::prospector_shard_of_focus,5}, {it::durability_shard_of_health,5},
66:             {it::monster_shard_of_focus,5}, {it::capture_shard_of_health,5}};
67:         else if (tank) v = {{it::prospector_shard_of_health,5}, {it::jungle_shard_of_focus,5}, {it::durability_shard_of_health,5},
68:             {it::capture_shard_of_health,5}, {it::monster_shard_of_focus,5}};
69:         else if (focus_user) v = {{it::prospector_shard_of_focus,5}, {it::durability_shard_of_health,5}, {it::monster_shard_of_focus,5},
70:             {it::capture_shard_of_health,5}};
71:         else {
72:             v = {{ranged ? it::prospector_shard_of_strength : it::prospector_shard_of_health,5}};
73:             if (t != ct::tavi) v.push_back({it::jungle_shard_of_strength,5});
74:             v.push_back({it::durability_shard_of_health,5});
75:             v.push_back({it::monster_shard_of_strength,5});
76:             v.push_back({it::capture_shard_of_strength,5});
77:         }
78:         if (V59_ITEMS == 2) v.push_back({focus_user || tank ? it::collectors_shard_of_focus : it::collectors_shard_of_strength,5});
79:         else v.resize(3);
80:         const it main = focus_user || tank ? it::bruiser_shard_of_focus : it::bruiser_shard_of_strength;
81:         for (int k = 1; k <= 12; ++k) {
82:             if (t == ct::marcella && k % 2 == 0) v.push_back({it::bruiser_shard_of_strength, 5 * (k / 2)});
83:             v.push_back({main, 5 * k});
84:             const int per_health = tank ? 1 : ranged || focus_user ? 3 : 2;
85:             if (k % per_health == 0) v.push_back({it::bruiser_shard_of_health, 5 * (k / per_health)});
86:         }
87:         return v;
88:     }
```

## bots/v62c/src/bot.cpp:1341

SHA256: 9fed2bbf32eafd40d14ddae2b79fac8d9b38311adb70a460d5ad33ca0224afc5

```cpp
1341: // Team layer, join: a healthy, light champion that sees an ally within 8 fighting (a visible enemy within 3 of it, and
1342: // that ally not outnumbering its enemies) walks to stand beside that ally, so the fight is taken together. Local and
1343: // visible only (long-range distress calls lost); never while hurt, carrying, capturing or channelling.
1344: bool Bot::a2_join_fight() {
1345:     if (hp < max_hp * 0.6f || gems >= 20 || !bc::self().can_move()) return false;
1346:     if (target_group >= 0 && target_group < static_cast<int>(w.groups.size()) &&
1347:         w.groups[static_cast<std::size_t>(target_group)].state == GroupState::reward && bit(w.groups[static_cast<std::size_t>(target_group)].tiles, pos))
1348:         return false;
1349:     const AllyRec* best = nullptr;
1350:     int best_d = 99;
1351:     for (const auto& a : w.allies) {
1352:         const int d = cheb(a.pos, pos);
1353:         if (d > 8 || d <= 2 || a.hp < a.max_hp * 0.25f) continue;
1354:         int foes = 0, friends = 1;
1355:         for (const auto& e : w.enemies) foes += e.hp > 0 && cheb(e.pos, a.pos) <= 3;
1356:         if (foes == 0) continue;
1357:         for (const auto& b : w.allies) friends += b.id != a.id && cheb(b.pos, a.pos) <= 3;
1358:         if (friends > foes + 1) continue; // already winning there without us
1359:         if (d < best_d || (d == best_d && a.id < best->id)) best = &a, best_d = d;
1360:     }
1361:     if (!best) return false;
1362:     bc::bitboard goal;
1363:     goal.clear();
1364:     goal.draw_chebyshev(best->pos, 1.0f);
1365:     const bool moved = walk_toward(goal);
1366:     if (moved) mode = "join";
1367:     return moved;
1368: }
1369: #endif
```

## bots/v62c/src/bot.cpp:1783

SHA256: 9fed2bbf32eafd40d14ddae2b79fac8d9b38311adb70a460d5ad33ca0224afc5

```cpp
1783: bool Bot::cast_on_camp(int ci) {
1784:     const auto& c = w.camps[ci];
1785:     if (tune::kSpellHold & 1) {
1786:         // An enemy is (or was just) near: keep the spells for it.
1787:         for (const auto& e : w.enemies)
1788:             if (cheb(e.pos, pos) <= tune::kSpellHoldRange) return false;
1789:         for (const auto& sg : w.sightings)
1790:             if (round - sg.round <= tune::kSpellHoldAge && cheb(sg.pos, pos) <= tune::kSpellHoldRange) return false;
1791:     }
1792: #if V55_HEART_CAMP
1793:     if (cast_camp_strike(ci)) return true;
1794: #endif
1795:     int best = -1;
1796:     float best_value = 0;
1797:     for (int s = 0; s < 2; ++s) {
1798:         if (!spell_ready(s)) continue;
1799:         const auto& sp = spells[s];
1800:         if (sp.excludes_walk && walked) continue;
1801:         if (cheb(pos, c.pos) > static_cast<int>(sp.range)) continue;
1802:         // Stuns win champion fights; on a camp they only add a little damage.
1803:         if ((tune::kSpellHold & 2) && (sp.kind == bc::ability_kind::cc || (type == bc::champion_type::ryth && s == 0)))
1804:             continue;
1805:         float value = 0;
1806:         if ((sp.kind == bc::ability_kind::damage || sp.kind == bc::ability_kind::cc) && sp.camps)
1807:             value = sp.modifier * focus;
1808:         else if (sp.kind == bc::ability_kind::aoe_damage && sp.camps) {
1809:             int hits = 0;
```

## bots/v62c/src/bot.cpp:3301

SHA256: 9fed2bbf32eafd40d14ddae2b79fac8d9b38311adb70a460d5ad33ca0224afc5

```cpp
3301:     const int outnumbered_k = round < NOVA_EARLY_SAFE_UNTIL ? NOVA_EARLY_SAFE_K : tune::kOutnumbered;
3302:     if (outnumbered_k > 0) {
3303:         // Most ladder deaths were a lone champion caught by two or more enemies: leave before they
3304:         // close in, at any health, unless the fight is already a sure kill.
3305:         int foes = 0, friends = 1;
3306:         for (const auto& e : w.enemies) foes += cheb(e.pos, pos) <= 8;
3307: #if A2_BELIEF
3308:         foes += a2_hidden_near(8, 0);
3309: #endif
3310:         for (const auto& a : w.allies) friends += cheb(a.pos, pos) <= 5 && a.hp >= a.max_hp * 0.4f;
3311:         const bool sure_kill = target && target_ttk <= 1.0f;
3312:         // V59_ALONE: a champion with no healthy ally within 5 also leaves two enemies (34% of our ladder deaths had no
3313:         // ally within 8; with the general margin at 2 a lone champion otherwise stays against two).
3314:         const bool lone_pair = V59_ALONE && friends == 1 && foes >= 2;
3315:         if ((foes >= friends + outnumbered_k || lone_pair) && !sure_kill) {
3316:             in_danger = true;
3317:             winning = false;
3318:             if (threat_on_me <= 0) threat_on_me = 1.0f;
3319:         }
3320:     }
```

## bots/v62c/src/bot.cpp:5212

SHA256: 9fed2bbf32eafd40d14ddae2b79fac8d9b38311adb70a460d5ad33ca0224afc5

```cpp
5212: // A clearly poorer ally will take this finished group's reward: it stands on the region, or (unless
5213: // on_tile_only) it claims the group and stands within 2 tiles of it.
5214: bool Bot::poorer_ally_takes(const GroupRec& g, int gi, bool on_tile_only) const {
5215: #if V58_DIRECTOR && V58_ROUTE
5216:     if (economy_enabled() && (gi == ec_job || gi == ec_capture)) {
5217:         if (economy_carry() == slot) return false;
5218:         // A handoff requires the carry already on the region: never leave an unoccupied reward waiting for it.
5219:         return economy_carry_on(g);
5220:     }
5221: #endif
5222:     const float mine = my_items();
5223: #if UB_GOLD_FUNNEL
5224:     // Gold funnel (top teams' Vesper earns 42% of her team's gold): Vesper gains 33% more from every gold gain, so
5225:     // she keeps the rewards she is on, and allies hand theirs to her instead of to the poorest teammate.
5226:     if (type == bc::champion_type::vesper_vale) return false;
5227: #endif
5228:     for (const auto& a : w.allies) {
5229:         const bool funnel = UB_GOLD_FUNNEL && a.type == bc::champion_type::vesper_vale;
5230:         if (!funnel && items_of(a.type, a.max_hp, a.strength, a.focus) + static_cast<float>(tune::kShareGold) >= mine) continue;
5231:         if (bit(g.tiles, a.pos)) return true;
5232:         if (on_tile_only) continue;
5233:         int s = -1;
5234:         for (int k = 0; k < std::min(team_size, kClaimSlots); ++k)
5235:             if (ally_handle[static_cast<std::size_t>(k)] == a.id) s = k;
5236:         if (s < 0 || claim_of(s) != gi) continue;
5237:         for (int ci : g.camps)
5238:             if (cheb(a.pos, w.camps[ci].pos) <= 2) return true;
5239:     }
5240:     return false;
```

## bots/v62c/src/bot.cpp:5394

SHA256: 9fed2bbf32eafd40d14ddae2b79fac8d9b38311adb70a460d5ad33ca0224afc5

```cpp
5394:     // team clears it again and again; our job calls never filled and it was never attacked. One check per call, never
5395:     // inside the group loop (hot-path instructions cost games: the bot runs at its fuel limit).
5396:     if (sole_gem_group == -2) {
5397:         sole_gem_group = -1;
5398:         float total = 0.0f;
5399:         for (const auto& g2 : w.groups) total += static_cast<float>(g2.gems);
5400:         for (std::size_t k = 0; k < w.groups.size(); ++k)
5401:             if (total > 0.0f && static_cast<float>(w.groups[k].gems) >= 0.9f * total) sole_gem_group = static_cast<int>(k);
5402:     }
5403:     if (sole_gem_group >= 0 && round >= A2_SOLE_FROM && hp >= max_hp * 0.6f && gems < tune::kTributeCarry) {
5404:         best_need = team_size;
5405:         best_score = 1e9f;
5406:         return sole_gem_group;
5407:     }
5408: #endif
5409: #if V61_OPEN_PACK
5410:     // Opening pack (ported from the rejected v58 experiment; rejected only by self-play). Claudus Maximus's first
5411:     // elk-size clear starts at round 21 with 3.7 champions and is captured at round 50; ours start at 36 with 2.7
5412:     // and capture at 79; by round 250 they take 4.0 such groups for 655 gold against our 2.3 for 266. Every
5413:     // champion picks the same group from static data: the best value per spawn distance among elk-size groups on our side.
5414:     if (open_group == -2) {
5415:         open_group = -1;
5416:         float ex = 0, ey = 0, en = 0;
5417:         for (vec2 p : w.enemy_spawn.positions()) ex += static_cast<float>(p.x), ey += static_cast<float>(p.y), ++en;
5418:         float best_v = 0.0f;
5419:         for (std::size_t k = 0; en > 0 && k < w.groups.size(); ++k) {
5420:             const auto& g = w.groups[k];
5421:             if (g.harmless || g.camps.empty() || g.gems == 0 || g.max_hp < 2400.0f || g.max_hp > 6000.0f) continue;
5422:             const vec2 c = w.camps[static_cast<std::size_t>(g.camps[0])].pos;
5423:             const int d = fdist(w.spawn_field, c);
5424:             const float de = std::max(std::fabs(static_cast<float>(c.x) - ex / en), std::fabs(static_cast<float>(c.y) - ey / en));
5425:             if (d > 30 || static_cast<float>(d) >= 0.8f * de) continue;
5426:             const float v = (static_cast<float>(g.gems) + gold_weight() * static_cast<float>(g.gold)) / (static_cast<float>(d) + 15.0f);
5427:             if (v > best_v) best_v = v, open_group = static_cast<int>(k);
5428:         }
5429:     }
5430:     if (open_group >= 0) {
5431:         const auto& og = w.groups[static_cast<std::size_t>(open_group)];
5432:         if (round >= V61_OPEN_UNTIL || og.state == GroupState::respawning) open_group = -1; // captured: the opening is over
5433:         else if (og.state == GroupState::alive && hp >= max_hp * 0.5f && gems < tune::kTributeCarry) {
5434:             best_need = std::min(team_size, V61_OPEN_N);
5435:             best_score = 1e9f;
5436:             return open_group;
5437:         }
5438:     }
5439: #endif
5440: #if A2_GATE_JOB
```

## bots/v62c/src/common.h:1346

SHA256: 34852f056261335cabec41b40fee1a8bafb73e762003cb5cfce94f56d77e34f5

```cpp
1346: #ifndef APEX_OUTNUMBERED
1347: #define APEX_OUTNUMBERED 2 // v59: was 0; 1 is too passive (-228 vs v58), 2 is +24 pooled over v58 on the 70-map gauntlet
1348: #endif
1349: // Retreat when enemies within 8 outnumber us (and healthy allies within 5) by at least this; 0 = off.
1350: inline constexpr int kOutnumbered = APEX_OUTNUMBERED;
1351: #ifndef APEX_ENDGAME_MARGIN
1352: #define APEX_ENDGAME_MARGIN 0
```

## bots/v62c/src/common.h:1657

SHA256: 34852f056261335cabec41b40fee1a8bafb73e762003cb5cfce94f56d77e34f5

```cpp
1657: #ifndef APEX_SPELL_HOLD
1658: #define APEX_SPELL_HOLD 0
1659: #endif
1660: #ifndef APEX_SPELL_HOLD_RANGE
1661: #define APEX_SPELL_HOLD_RANGE 12
1662: #endif
1663: #ifndef APEX_SPELL_HOLD_AGE
1664: #define APEX_SPELL_HOLD_AGE 10
1665: #endif
1666: // Spells on camps leave them on an 8-turn cooldown when an enemy arrives. On the ladder (15 Oct, 110 games vs
1667: // the top 10) the same champions dealt half the top teams' champion damage (Cassi 83 vs 325, Ren 352 vs 725
1668: // per 100 rounds). Bits: 1 = no spell on camps while an enemy is visible or was sighted within RANGE tiles in
1669: // the last AGE rounds; 2 = never spend a stun (cc spells, Ryth's area stun) on camps.
1670: inline constexpr int kSpellHold = APEX_SPELL_HOLD;
1671: inline constexpr int kSpellHoldRange = APEX_SPELL_HOLD_RANGE;
1672: inline constexpr int kSpellHoldAge = APEX_SPELL_HOLD_AGE;
1673: #ifndef APEX_SAVE_DASH
1674: #define APEX_SAVE_DASH 0
1675: #endif
1676: // Dashes cut travel by one tile per 8 turns but sit on cooldown when an escape needs them. 1: no
1677: // travel dashes within 15 tiles of an enemy seen in the last 15 rounds; 2: never for travel (fights,
1678: // hunts and escapes still dash); 0 = off.
1679: inline constexpr int kSaveDash = APEX_SAVE_DASH;
```

## bots/v62c/src/common.h:1039

SHA256: 34852f056261335cabec41b40fee1a8bafb73e762003cb5cfce94f56d77e34f5

```cpp
1039: #ifndef A2_BELIEF // track enemies out of sight: recent ones that could be in reach count in danger checks
1040: #define A2_BELIEF 0
1041: #endif
1042: #ifndef A2_BELIEF_AGE
1043: #define A2_BELIEF_AGE 3
1044: #endif
1045: #ifndef A2_TSX // action search (APEX_TSEARCH) with a fuel-guarded scoring stage, replacing the fight/run verdict
1046: #define A2_TSX 0
1047: #endif
1048: #ifndef A2_TEAM // team fight layer: bit 1 hold out of enemy reach (hurt or outnumbered), bit 2 join a visible ally's fight
1049: #define A2_TEAM 2
1050: #endif
1051: #ifndef A2_THREAT // threat-aware camp choice and travel for exposed (hurt or carrying) champions
```
