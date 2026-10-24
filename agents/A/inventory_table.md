| id | function (file:line) | head | status | teacher choice | hook (line) |
|---|---|---|---|---|---|
| chain | Bot::play_turn (behaviour chain) (bot.cpp:5843) | strategy (1) | active | the first branch whose function returns true (it also acts); captured  | before 6373 |
| brain_adapt | brain::load/adapt (class profile -> tune::*) (strategy.h:472) | deterministic - keep | active | tune::kAggression, kTributeCarry, kRetreatHp, kDangerTtd, kShopGold, k | after 495 |
| lab_knobs | Bot::play_turn lab knob block (A2_LAB) (bot.cpp:5843) | deterministic - keep | active | scaled tune values | after 5987 |
| channel_guard | Bot::play_turn channel guard (cancel recall/tribute) (bot.cpp:5843) | bank (4) | active | `incoming * (left + 1) * kChannelGuard < hp` (return = keep) | after 6122 |
| shop | Bot::shop (bot.cpp:533) | shop (5) | active | first step with want > 0 (bought immediately; loop continues while gol | before 546 |
| build_for | build_for (item build order) (bot.cpp:54) | shop (5) | active | returned vector of (item, total) steps | after 204 |
| go_home | Bot::go_home_if_needed (bot.cpp:3948) | strategy (1) | active | return true + heading_home = true | after 3982 |
| hunt | Bot::hunt (bot.cpp:3879) | strategy (1) | active | `best` (const Sighting*) | before 3939 |
| tribute | Bot::tribute_if_needed (bot.cpp:4031) | bank (4) | active | `go` (bool); altar implicit in the distance field | after 4112 |
| farm_waits | Bot::farm respawn wait (APEX_USE_WAITS) (bot.cpp:5442) | bank (4) | active | force_tribute + tribute_if_needed() or heading_home + go_home_if_neede | after 5720 |
| score_groups | Bot::score_groups (bot.cpp:4780) | objective (2) | active | `best` (+ best_need, best_score); after route_search: top[pick] | before 5200 |
| route_search | Bot::route_search (bot.cpp:5234) | deterministic - keep | active | returned index into top | after 5188 |
| farm_commit | Bot::farm (target commit) (bot.cpp:5442) | objective (2) | active | `best`, `best_need` | before 5665 |
| duo | Bot::farm NOVA_DUO / buddy() (bot.cpp:5442) | role (3) | active | best = buddy claim (ranged member) or duo_ignore_slot (melee leader) | after 5611 |
| claims | shared-memory claims (write_claim / claims_split / senior_claims / open_call_by_lower) (bot.cpp:411) | deterministic - keep | active | claim code in our slot | after 421 |
| sighting | share_sighting / read_sighting / APEX_EVENTS respawn publication (bot.cpp:435) | deterministic - keep | active | shared word bits 42-63 | after 453 |
| enemy_gate | Bot::handle_enemies (entry gates) (bot.cpp:2734) | deterministic - keep | active | `!nearest // nearest_d > 8` -> false | after 2765 |
| target | Bot::handle_enemies target selection (bot.cpp:2734) | combat (7) | active | `target` (const EnemyRec*), target_ttk | before 2829 |
| verdict_formula | Bot::handle_enemies fight-or-flight formula (bot.cpp:2734) | engage (8) | active | `winning`, `in_danger` (bool pair) | before 2969 |
| team_decide | Bot::team_decide (APEX_TFC) (tsearch.cpp:991) | engage (8) | inactive | order 1/2/0 + focus_handle | after 1051 |
| tactical_decide | Bot::tactical_decide (fight-or-run search) (tsearch.cpp:766) | engage (8) | active | return +1 / -1 / 0 | after 3229 |
| verdict_final | Bot::handle_enemies final verdict (bot.cpp:2734) | engage (8) | active | `winning`, `in_danger`, threat_on_me | before 3547 |
| deny_tribute | Bot::deny_tribute (APEX_TRIB_DENY & 2) (deny.cpp:12) | combat (7) | active | `best` (EnemyRec*), best_altar, best_kill | after 76 |
| try_lock_altar | Bot::try_lock_altar (bot.cpp:1590) | deterministic - keep | active | lock.use(altar) | before 1600 |
| bush_ambush | Bot::bush_ambush (bot.cpp:1615) | combat (7) | active | `victim`, `step` | before 1671 |
| bush_recall | Bot::handle_enemies bush recall (bot.cpp:2734) | strategy (1) | active | recall() + heading_home | before 3553 |
| caster_micro | Bot::caster_micro (APEX_CMICRO) (tsearch.cpp:1072) | move (6) | active | `best` (Option) | before 1373 |
| flee_hit | Bot::handle_enemies NOVA_FLEE_HIT (bot.cpp:2734) | combat (7) | active | `adj` | before 3606 |
| escape_or_stand | Bot::escape_or_stand (APEX_STAND) (bot.cpp:2619) | move (6) | active | branch taken + victim | before 2669 |
| dash_away | Bot::dash_away (bot.cpp:2255) | move (6) | active | cands[0..3] tried in order | before 2285 |
| ranged_flee | Bot::handle_enemies ranged flee (APEX_RANGED_FLEE, kKiteCast & 4) (bot.cpp:2734) | combat (7) | active | cast_done | before 3657 |
| retreat_from | Bot::retreat_from (bot.cpp:1192) | move (6) | active | cands in order (first legal move) | before 1240 |
| kite_step | Bot::kite_step (APEX_KITE) (bot.cpp:2189) | move (6) | active | `best` | before 2208 |
| cast_on_enemy | Bot::cast_on_enemy (bot.cpp:1396) | combat (7) | active | `best` slot, `dash_slot` + `dash_aim` | before 1452 |
| engage_exec | Bot::handle_enemies engage execution (kite-cast, kite, fight-champ, gap-dash, fight-cast, chase) (bot.cpp:2734) | combat (7) | active | branch taken | after 3686 |
| reset_attack | Bot::use_reset_and_attack / attack_unit / opportunistic_attack (bot.cpp:1287) | deterministic - keep | active | side effect | after 1312 |
| support_casts | Bot::support_casts (shield / heal) (bot.cpp:1510) | combat (7) | active | cast or not; `best` ally | before 1553 |
| priority | Bot::update_priority (APEX_PRIORITY 5) (bot.cpp:1693) | deterministic - keep | active | `want` | before 1712 |
| follow_field | Bot::follow_field (bot.cpp:648) | move (6) | active | cands in order (first legal move) | after 668 |
| walk_toward | Bot::walk_toward (bot.cpp:696) | deterministic - keep | active | via follow_field | after 837 |
| try_dash | Bot::try_dash (travel dash) (bot.cpp:598) | move (6) | active | `best` | before 624 |
| ward_ahead | Bot::ward_ahead (NOVA_WARD_AHEAD 6) (bot.cpp:1726) | ward (9) | active | `best` tile | before 1792 |
| ward_reveal | Bot::ward_reveal (APEX_WARD_REVEAL 2) (bot.cpp:1890) | ward (9) | active | cands[0..2] tried | before 1940 |
| reveal_bush_camp | Bot::reveal_bush_camp (NOVA_BUSH_WARD) (bot.cpp:4536) | ward (9) | active | `at` | before 4567 |
| counter_ambush | Bot::counter_ambush (bot.cpp:1967) | move (6) | active | `best` tile | before 2058 |
| drop_ward | Bot::drop_ward (bot.cpp:5751) | ward (9) | inactive | first legal tile | after 5752 |
| fight_camps | Bot::fight_camps (stage / siege / disengage / approach / attack) (bot.cpp:4271) | move (6) | active | branch + `t` camp index | before 4451 |
| cast_on_camp | Bot::cast_on_camp (bot.cpp:1347) | deterministic - keep | active | `best` | before 1380 |
| break_out | Bot::break_out (NOVA_UNBOX) (bot.cpp:4510) | deterministic - keep | active | attack | after 4510 |
| ml_draft | ml_draft_pick (A2_MLDRAFT 1: every map) (draft.cpp:578) | draft_pick (0) | active | `best` (argmax z of draft_net, first maximum) | before 674 |
| lineup_draft | play_draft lineup tables / pick_from (fallback when the net fails) (draft.cpp:709) | draft_pick (0) | active | pick in pick_from | before 58 |
| draft_memory | brain::record_draft (draft memory header) (strategy.h:412) | deterministic - keep | active | 6-byte header {magic, team, casters, class, max_group, flags} | after 422 |
| world_update | World::update / observe_* / sightings (world.cpp:692) | deterministic - keep | active | EnemyRec/AllyRec lists, group states, sightings, hot_zone | after 692 |
| build_fields | Bot::build_fields (bot.cpp:5795) | deterministic - keep | active | n/a | after 5795 |
| episode | Bot::episode_tick (episode.cpp:105) | deterministic - keep | inactive | - | after 106 |
| tactical_search | Bot::tactical_search / ts_prewarm (APEX_TSEARCH) (tsearch.cpp:385) | engage (8) | inactive | - | after 385 |
| melee_caught | Bot::melee_caught (APEX_STAND2) (bot.cpp:2690) | move (6) | inactive | - | after 2690 |
| fight_sim | simulate_fight (APEX_FIGHT_SIM) (bot.cpp:2734) | engage (8) | inactive | - | after 3258 |
| rush | Bot::rush (NOVA_RUSH_UNTIL) (bot.cpp:3812) | strategy (1) | inactive | - | after 3812 |
