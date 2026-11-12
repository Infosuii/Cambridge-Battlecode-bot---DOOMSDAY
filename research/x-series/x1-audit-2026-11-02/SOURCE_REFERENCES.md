# Exact attached-source evidence

These are read-only excerpts from the user-supplied x1 archive. They are findings evidence, not bot modifications. Original file hashes and archive identity are in SOURCE_PRESERVATION.json. Lines are original one-based source lines.

## botcpp-L680
Original `bot.cpp:680`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
677:     decode_claims();
678: }
679: 
680: void Bot::read_sighting() {
681: #if APEX_EVENTS
682:     if ((shared >> 63) & 1) {
683:         // A teammate's group event: group (7 bits) and its respawn-ready round mod 256 (8 bits).
684:         const int gi = static_cast<int>((shared >> kSightX) & 127);
685:         const int mod = static_cast<int>((shared >> kSightY) & 255);
686:         const int base = round - 64;
687:         const int ready = base + ((mod - base) % 256 + 256) % 256;
688:         w.apply_event(gi, ready, round);
689:         return;
```

## botcpp-L1042
Original `bot.cpp:1042`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
1039: }
1040: #endif
1041: 
1042: bool Bot::walk_toward(const bc::bitboard& goals_in) {
1043:     PROF(move);
1044: #if A2_TEL && X1_TEL
1045:     PROF_CHECK("wt_in");
1046:     struct X1Out { ~X1Out() { PROF_CHECK("wt_out"); } } x1_out;
1047: #endif
1048: #if A2_TEL
1049:     a2tel::CallCost a2_cost{9};
1050: #endif
1051:     walk_unreachable = false;
```

## botcpp-L3169
Original `bot.cpp:3169`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
3166: #if A2_BURST_HOLD
3167:     a2_hold_burst = false;
3168: #endif
3169:     if (w.enemies.empty()) return false;
3170: #if V58_CAMP_CONTACT
3171:     if (camp_contact()) return true;
3172: #endif
3173: #if V58_CAPTURE_STAND
3174:     if (capture_stand()) return true;
3175: #endif
3176: #if V58_DENY_CAP
3177:     if (deny_capture()) return true;
3178: #endif
```

## botcpp-L3678
Original `bot.cpp:3678`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
3675:     if (!tfc_applied && tune::kTsDecide && !(A2_TSX && tune::kTSearch) && target && nearest_d <= tune::kTsRange) {
3676:         // Fight or run by search (tactical_decide): both plans played forward with the full kits and judged with
3677:         // the learned exchange rates; a clear verdict overrides the formula, c1 still carries it out.
3678:         const int verdict = tactical_decide();
3679:         PROF_CHECK("e_td");
3680: #if A2_TD_AUTH
3681:         // A fight verdict may clear the formula's danger only for risks the model represents: every enemy that could
3682:         // hit us next turn is in it, no Cassi/Issac pair is split, and no awake camp reaches us (camps are not
3683:         // modelled). Otherwise the formula keeps its flags and the flee/stand logic (which stands and fights when the
3684:         // escape is blocked) decides. Run verdicts are always taken.
3685:         const bool unmodelled = a2ts::snap.omit_reach || a2ts::snap.link_partial || (!tune::kTsCamps && bit(w.hot_zone, pos))
3686: #if A2_BELIEF
3687:             || a2_hidden_near(5, 1) > 0
```

## botcpp-L4033
Original `bot.cpp:4033`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
4030:         else if (deny_tribute()) return true;
4031:     }
4032:     PROF_CHECK("e_mid");
4033:     if (in_danger && !winning) last_flee_round = round;
4034:     if (in_danger && !winning && tune::kBushRecall && hp < max_hp * 0.5f && hidden_here() && !bit(w.hot_zone, pos) &&
4035:         fdist(w.spawn_field, pos) > tune::kShopWalkDist) {
4036:         // Losing, hurt and hidden: recall from cover (nobody can hit us here to cancel it).
4037:         try {
4038:             bc::self().recall();
4039:             mode = "bush-recall";
4040:             heading_home = true;
4041:             return true;
4042:         } catch (const std::exception& e) {
```

## botcpp-L4408
Original `bot.cpp:4408`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
4405:     }
4406:     if (!tune::kHunt || gems >= tune::kHuntGems || hp < max_hp * tune::kHuntHp) return false;
4407:     // Hunting toward enemies we then flee from loops forever (and enemies on their spawn heal).
4408:     if (tune::kHuntFix && round - last_flee_round < 10) return false;
4409:     const Sighting* best = nullptr;
4410:     int best_d = tune::kHuntRange + 1;
4411:     for (const auto& s : w.sightings) {
4412:         if (round - s.round > 3) continue;
4413:         if (tune::kHuntFix && bit(w.enemy_spawn_zone, s.pos)) continue;
4414:         const int d0 = cheb(s.pos, pos);
4415:         if (d0 < best_d) {
4416:             best_d = d0;
4417:             best = &s;
```

## botcpp-L4741
Original `bot.cpp:4741`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
4738: 
4739: // Damage the tanks absorb while the team kills the dangerous camps, weakest first.
4740: float Bot::group_soak(const GroupRec& g, float team_dps) const {
4741:     std::array<std::pair<float, float>, 12> live{};
4742:     int n = 0;
4743:     float str_alive = 0;
4744:     for (int ci : g.camps) {
4745:         const auto& c = w.camps[ci];
4746:         if (c.strength <= 0 || n >= 12) continue;
4747:         if (g.state == GroupState::alive && c.dead) continue;
4748:         const float hp_c = g.state == GroupState::alive ? c.hp : c.max_hp;
4749:         live[n++] = {hp_c, c.strength};
4750:         str_alive += c.strength;
```

## botcpp-L4746
Original `bot.cpp:4746`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
4743:     float str_alive = 0;
4744:     for (int ci : g.camps) {
4745:         const auto& c = w.camps[ci];
4746:         if (c.strength <= 0 || n >= 12) continue;
4747:         if (g.state == GroupState::alive && c.dead) continue;
4748:         const float hp_c = g.state == GroupState::alive ? c.hp : c.max_hp;
4749:         live[n++] = {hp_c, c.strength};
4750:         str_alive += c.strength;
4751:     }
4752:     std::sort(live.begin(), live.begin() + n);
4753:     float soak = 0;
4754:     for (int i = 0; i < n; ++i) {
4755:         soak += str_alive * live[i].first / team_dps;
```

## botcpp-L4761
Original `bot.cpp:4761`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
4758:     return soak;
4759: }
4760: 
4761: int Bot::champions_needed(const GroupRec& g, float hp_left) {
4762:     if (g.harmless || hp_left <= 0) return 1;
4763:     // Camps focus one champion, but tanks can rotate out (camps never chase or heal),
4764:     // so the team's combined health pays for the fight.
4765:     const float dps = my_dps(&g);
4766:     const float coef = soak_coefficient(static_cast<int>(&g - w.groups.data()), hp_left) * camp_taken_mult;
4767:     for (int n = 1; n <= 6; ++n) {
4768:         const float pool = hp * tune::kNeedPool + static_cast<float>(n - 1) * max_hp * 0.7f;
4769:         if (coef / (dps * static_cast<float>(n)) <= pool) return n;
4770:     }
```

## botcpp-L4850
Original `bot.cpp:4850`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
4847:             for (int ci : g.camps)
4848:                 if (!w.camps[ci].dead) ring.draw_chebyshev(w.camps[ci].pos, static_cast<float>(w.camps[ci].range + 1));
4849:             PROF_CHECK("sg_ring");
4850: #if X1_FAST_SIEGE
4851:             // X1_FAST_SIEGE (telemetry: the siege line-of-sight scan caused most fuel suspensions on 02the-pack and
4852:             // 02gift-wrapping; a tiles x camps x steps loop exceeds a turn's fuel on big wolf groups). Camps and walls/
4853:             // bushes never move, so each camp's set of tiles within 4 with a clear line is computed once (lazily, a
4854:             // few camps per turn) as a bitboard; each turn is then ring & union(alive camps' sets): the same tiles as
4855:             // NOVA_SIEGE_LOS's per-turn scan, then the same danger mask and fallback.
4856:             if (NOVA_SIEGE_LOS) {
4857:                 static std::vector<bc::bitboard> los;
4858:                 static std::vector<std::uint8_t> los_ready;
4859:                 static std::vector<std::uint8_t> opq;
```

## botcpp-L4898
Original `bot.cpp:4898`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
4895:                 }
4896:                 ring &= ~danger_zone & ~w.static_blocked;
4897:                 bc::bitboard seeing = ring & any;
4898:                 if (!seeing.is_empty() && (complete || true)) ring = seeing;
4899:             }
4900:             if (false) {
4901: #else
4902:             ring &= ~danger_zone & ~w.static_blocked;
4903:             if (NOVA_SIEGE_LOS) {
4904: #endif
4905:                 // Spells need the camp in view: on contest the ring tile behind a wall row saw nothing and
4906:                 // champions "sieged" a monolith for 1,500 turns without one cast. Keep tiles with a clear
4907:                 // straight line (no wall, no foreign bush) to a live camp.
```

## botcpp-L5647
Original `bot.cpp:5647`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
5644:         const float mid_mult = gi < mid_group.size() && mid_group[gi] ? A2_MID_W * std::exp(0.3f * LABK(40)) : 1.0f;
5645: #endif
5646:         {
5647:             const float best_case = (static_cast<float>(g.gems) + gold_weight() * static_cast<float>(g.gold)) * mid_mult *
5648:                 tune::kStickiness / (static_cast<float>(approach + wait) + capture_time + 4.0f);
5649:             if (best_case <= prune_bound()) {
5650: #ifdef APEX_SCOREDBG
5651:                 if (g.harmless && g.gems > 0 && round < 60)
5652:                     std::printf("SDBG R%d slot%d G%zu pruned d%d st%d best_case %.3f bound %.3f\n", round, slot, gi, dist,
5653:                         static_cast<int>(g.state), best_case, prune_bound());
5654: #endif
5655:                 continue;
5656:             }
```

## botcpp-L5734
Original `bot.cpp:5734`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
5731:             (tune::kIncumbent ? senior_claims(static_cast<int>(gi)) : lower) > 0)
5732:             value *= 0.15f;
5733:         if (round - g.enemy_round < 15 && !(NOVA_BIGJOB > 0.0f && gi < big_group.size() && big_group[gi])) value *= UB_ENEMY_CAMP;
5734: #if A2_CAMPWATCH
5735:         // Camp watch (ladder replays: the top teams walk into contested camps, weight -0.32 against our -1.06): a group
5736:         // the enemy farmed recently that is about to respawn is where they come next. A healthy champion with an ally
5737:         // beside the group goes there first, so the fight starts with them under camp fire and outnumbered.
5738:         if (g.state == GroupState::respawning && g.respawn_round - round <= A2_CW_LEAD && round - g.enemy_round <= A2_CW_MEM &&
5739:             hp >= max_hp * 0.8f && gems < 20 && allies_near_group(g) >= 1)
5740:             value *= A2_CW_MULT;
5741: #endif
5742:         value *= mid_mult;
5743: #if A2_ZONES
```

## botcpp-L5760
Original `bot.cpp:5760`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
5757:                 }
5758:         }
5759: #endif
5760:         if (NOVA_BIGJOB > 0.0f && round >= NOVA_BIGJOB_FROM && gi < big_group.size() && big_group[gi]) value *= NOVA_BIGJOB_MULT;
5761:         // Altar-side groups (APEX_ALTAR_BONUS): their gems bank at once, without a trip.
5762:         if (tune::kAltarBonus > 0.0f && w.altar_ready && !g.camps.empty() && fdist(w.altar_field, w.camps[g.camps[0]].pos) <= 6)
5763:             value *= 1.0f + tune::kAltarBonus;
5764:         // Numbers (APEX_NUMBERS_INVADE): with enough extra living champions, take the enemy side's groups.
5765:         if (alive_us - alive_them >= tune::kNumbersInvade && w.enemy_ready && w.group_margin[gi] < 0) value *= 1.0f + tune::kNumbersBonus;
5766:         // Territory (APEX_TERRITORY, until round APEX_TERRITORY_UNTIL): our own side first. The evaluator puts
5767:         // early contact at -13 gems per champion; c1 spent 63% of its time on the enemy half against 46% for
5768:         // the top teams and earned 30% less in the first 150 rounds.
5769:         if (MONO_MULT != 1.0f)
```

## botcpp-L6191
Original `bot.cpp:6191`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
6188:     return official_map == 1;
6189: }
6190: 
6191: bool Bot::farm() {
6192:     PROF(farm);
6193:     PROF_CHECK("farm0");
6194:     if (avoid_until.size() != w.groups.size()) avoid_until.assign(w.groups.size(), 0);
6195: #if V58_DIRECTOR && V58_ROUTE
6196:     if (economy_release_capture()) return true;
6197: #endif
6198:     int best = -1, best_need = 1;
6199:     float best_score = 0;
6200: 
```

## botcpp-L6526
Original `bot.cpp:6526`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
6523:         goal.clear();
6524:         for (int ci : g.camps) goal.draw_chebyshev(w.camps[ci].pos, static_cast<float>(range));
6525:         goal &= ~g.tiles; // standing on a spawn tile delays the respawn
6526:         if (bit(g.tiles, pos) || !bit(goal, pos)) walk_toward(goal);
6527:         return true;
6528:     }
6529:     case GroupState::alive: {
6530:         PROF_CHECK("f_alive");
6531:         const bool r = fight_camps(g, best_need);
6532:         PROF_CHECK("f_camps");
6533:         return r;
6534:     }
6535:     }
```

## botcpp-L6653
Original `bot.cpp:6653`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
6650:     }
6651: }
6652: 
6653: void Bot::play_turn() {
6654:     PROF(turn);
6655: #if A2_TEL
6656:     a2tel::TurnGuard a2_guard;
6657: #endif
6658: #ifdef APEX_FUEL_NOISE
6659:     {
6660:         // Test only: burn a fixed extra amount of fuel each turn (checks how sensitive decisions are to fuel use).
6661:         volatile std::uint32_t sink = 0;
6662:         for (int i = 0; i < APEX_FUEL_NOISE; ++i) sink = sink + static_cast<std::uint32_t>(i);
```

## botcpp-L6879
Original `bot.cpp:6879`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
6876:         }
6877:         const float* k = lab::knobs;
6878:         auto ri = [](float v) { return static_cast<int>(std::lround(v)); };
6879:         tune::kAggression *= std::exp(0.3f * k[0]);
6880:         tune::kRetreatHp = std::clamp(tune::kRetreatHp + 0.1f * k[1], 0.05f, 0.95f);
6881:         tune::kDangerTtd *= std::exp(0.3f * k[2]);
6882:         tune::kDangerHp = std::clamp(b_dhp + 0.05f * k[3], 0.0f, 0.9f);
6883:         tune::kTributeCarry = std::max(8, ri(static_cast<float>(tune::kTributeCarry) * std::exp(0.3f * k[4])));
6884:         tune::kHuntRange = std::max(0, b_hunt_range + ri(3.0f * k[5]));
6885:         tune::kHuntHp = std::clamp(b_hunt_hp + 0.1f * k[6], 0.1f, 1.0f);
6886:         tune::kChaseRange = std::max(0, b_chase + ri(2.0f * k[7]));
6887:         tune::kGoldWeight *= std::exp(0.4f * k[8]);
6888:         tune::kWaitWeight = b_wait * std::exp(0.4f * k[9]);
```

## botcpp-L7289
Original `bot.cpp:7289`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
7286:     PROF_CHECK("shop");
7287: 
7288: 
7289:     support_casts();
7290:     PROF_CHECK("support");
7291:     mode = "idle";
7292:     if (ward_reveal()) w.update(round); // the ward shows the bush now: look again
7293:     PROF_CHECK("wardrev");
7294:     if (counter_ambush()) {
7295:         // We moved (into the attacker's bush, or away from it): look again before deciding.
7296:         w.update(round);
7297:     }
7298:     PROF_CHECK("ambush");
```

## botcpp-L7314
Original `bot.cpp:7314`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
7311: #if V58_DIRECTOR
7312:     economy_update(); // once per observation; the elected coordinator replans at most every ten rounds or completion
7313: #endif
7314:     const bool fought =
7315: #if V58_SURVIVE
7316:         survive_contact() ||
7317: #endif
7318: #if V58_ACT & 2
7319:         act_enemy_before_walk() ||
7320: #endif
7321:         handle_enemies();
7322: #if A2_SHIELDLATE
7323:     if (fought && !cast_done) {
```

## botcpp-L7334
Original `bot.cpp:7334`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
7331:     // Flee-hit check: after the hit, did the turn still move and cast? (kind 13: bit 0 moved, bit 1 cast)
7332:     if (a2tel::fleehit_round == round) a2tel::bump(13u * 4096 + (walked ? 1u : 0u) + (cast_done ? 2u : 0u));
7333: #endif
7334:     if (fought) {
7335:         if (std::string_view(mode) == "idle") mode = "enemy";
7336:         if (tune::kDistress && std::string_view(mode).starts_with("flee")) share_sighting(true);
7337:         opportunistic_attack();
7338:     } else if (win_now() && hp >= max_hp * tune::kDangerHp && tribute_if_needed()) {
7339:         // Our bag finishes the race: bank it before anything else (shopping can wait).
7340:         mode = "tribute-win";
7341:     } else if (go_home_if_needed()) {
7342:         if (std::string_view(mode) == "idle") mode = "home";
7343: #if (A2_TEAM & 2)
```

## botcpp-L7354
Original `bot.cpp:7354`, source SHA256 `32b1c347ef408f9d518eb4f9e3cb2d4c64c7aeae95928076a45ad6d09506df6a`.
```text
7351:     } else if (tribute_if_needed()) {
7352:         mode = "tribute";
7353:     } else {
7354:         if (!farm()) mode = "nofarm";
7355:         PROF_CHECK("d_farm");
7356:         opportunistic_attack();
7357:         PROF_CHECK("d_opp");
7358:         support_casts();
7359:     }
7360:     PROF_CHECK("decide");
7361: #if A2_MICLOG
7362:     {
7363:         // MT round slot type hp% nd0 nd inr mode cd0 cd1 used canatk0 canatk walked allies3 enemies3 gems x y ntype
```

## both-L427
Original `bot.h:427`, source SHA256 `088bfd4278e0677d224e23099d93b1e22bd61e763a138ad13cda07bc2ca9c3fe`.
```text
424:         const float t = std::min(1.0f, static_cast<float>(ally_score) / static_cast<float>(tune::kGoldTaper));
425:         return weight * (1.0f - 0.8f * t);
426:     }
427:     bool win_now() const { return tune::kWinFirst && gems > 0 && ally_score + gems >= static_cast<int>(bc::constants::winning_gems); }
428:     vec2 ward_pos{-100, -100};
429:     int ally_score = 0, enemy_score = 0;
430:     int team_kills_seen = 0;
431:     bool v71_done_ = false, ladder_known = false; // LADDER_TABLES
432:     bool fs_team_died = false; // FIRST_SAFE: one of our champions has died
433: };
```

## tsearchcpp-L55
Original `tsearch.cpp:55`, source SHA256 `78d6f9989474067f23df47ae0e6daf1f70a2275db67750be593270bbdf801abd`.
```text
52:                     if constexpr (requires { a.modifier; }) ks.mod = a.modifier;
53:                     if constexpr (requires { a.radius; }) ks.radius = static_cast<std::int8_t>(a.radius);
54:                     if constexpr (std::is_same_v<A, bc::ability_dash>)
55:                         if (TS_DASHX && a.duration > 0) ks.flags |= ts::SF_STUN; // striking dash stun
56:                 },
57:                 *info);
58:             if (ks.kind == ts::K_CC) ks.flags |= ts::SF_STUN;
59:             if (ks.kind == ts::K_AOE && type == bc::champion_type::ryth) ks.flags |= ts::SF_STUN; // Ryth's area stun
60:             if (ks.kind == ts::K_RESET && type == bc::champion_type::marcella) ks.flags |= ts::SF_ENH;
61:             if (ks.kind == ts::K_DASH && ks.range <= 0) ks.range = 2;
62:         }
63:     } catch (...) {
64:     }
```

## tsearchcpp-L84
Original `tsearch.cpp:84`, source SHA256 `78d6f9989474067f23df47ae0e6daf1f70a2275db67750be593270bbdf801abd`.
```text
81:     if (type == bc::champion_type::varg) u.flags |= ts::U_SPLASH;
82:     if (type == bc::champion_type::marcella) u.flags |= ts::U_STUN_IMMUNE;
83:     if (type == bc::champion_type::vendetta) u.flags |= ts::U_RESET_ON_KILL;
84:     if ((A2_KITFIX & 4) && type == bc::champion_type::heart_of_ruin) u.flags |= ts::U_RUIN;
85:     if (type == bc::champion_type::ren) u.retaliate = 0.2f * focus;
86:     const Kit& k = kit_of(type);
87:     for (int s = 0; s < 2; ++s) {
88:         const KitSpell& ks = k.sp[s];
89:         ts::SSpell& sp = u.sp[s];
90:         sp.kind = ks.kind;
91:         sp.range = ks.range;
92:         sp.radius = ks.radius;
93:         sp.flags = ks.flags;
```

## tsearchh-L228
Original `tsearch.h:228`, source SHA256 `670c6d6e84ca25dd64c8aa09a374e8987c662d849e8d85dc81f8cfb2c5831a93`.
```text
225: inline void deal(State& s, int src, int dst, float dmg, bool can_retaliate = true) {
226:     Unit& t = s.u[dst];
227:     if (!t.alive() || dmg <= 0) return;
228: #if A2_KITFIX & 4
229:     // Heart of Ruin: up to +50% damage, linear in missing health (shields do not count).
230:     if (src >= 0 && (s.u[src].flags & U_RUIN))
231:         dmg *= 1.0f + 0.5f * std::clamp(1.0f - s.u[src].hp / std::max(1.0f, s.u[src].max_hp), 0.0f, 1.0f);
232: #endif
233:     if (t.shield > 0) {
234:         const float a = std::min(t.shield, dmg);
235:         t.shield -= a;
236:         dmg -= a;
237:     }
```

## tsearchh-L301
Original `tsearch.h:301`, source SHA256 `670c6d6e84ca25dd64c8aa09a374e8987c662d849e8d85dc81f8cfb2c5831a93`.
```text
298:     return true;
299: }
300: 
301: #if TS_DASHX
302: // Striking dash landing (Heart of Ruin): damage and stun on every opponent within the radius of where it lands.
303: // `bits` names the context (A2_DASHX 1 our root action, 2 our playouts, 4 enemy playouts); off contexts land quietly.
304: inline void dash_land(State& s, int a, const SSpell& sp, int bits) {
305:     if (sp.value <= 0 || !(TS_DASHX & bits)) return;
306:     const Unit& u = s.u[a];
307:     const int r = std::max<int>(1, sp.radius);
308:     for (int j = 0; j < s.n; ++j)
309:         if (j != a && s.u[j].alive() && s.u[j].team != u.team && cheb(s.u[j].x, s.u[j].y, u.x, u.y) <= r) {
310:             if (sp.flags & SF_STUN) stun(s, j);
```

## worldcpp-L459
Original `world.cpp:459`, source SHA256 `e1b8bda73ee2d5fbee2d1ad754f6129ae57a248daeebdc172bc109f14d4beaeb`.
```text
456:     return ci < 0 ? -1 : camp_group[ci];
457: }
458: 
459: void World::apply_event(int gi, int ready_round, int round) {
460:     if (gi < 0 || gi >= static_cast<int>(groups.size())) return;
461:     if (!group_visible.empty() && group_visible[static_cast<std::size_t>(gi)]) return; // our own eyes win
462:     auto& g = groups[static_cast<std::size_t>(gi)];
463:     if (ready_round > round) {
464:         if (g.state == GroupState::respawning && std::abs(g.respawn_round - ready_round) <= 1) return;
465:         g.state = GroupState::respawning;
466:         g.respawn_round = ready_round;
467:         for (int i : g.camps) {
468:             camps[i].hp = camps[i].max_hp;
```

## worldcpp-L565
Original `world.cpp:565`, source SHA256 `e1b8bda73ee2d5fbee2d1ad754f6129ae57a248daeebdc172bc109f14d4beaeb`.
```text
562:     altar_ready = false;
563: }
564: 
565: void World::observe_champions() {
566:     PROF(champs);
567:     enemies.clear();
568:     allies.clear();
569:     const auto me = bc::self();
570:     for (vec2 p : bc::vision::champion_tiles().positions()) {
571:         std::uint32_t handle = 0;
572:         if (d::sdk_champion_at(p.x, p.y, &handle) != 0) continue;
573:         d::champion_info info{};
574:         if (d::sdk_champion(handle, &info) != 0) continue;
```

