# v306 runtime knob reference

[Project home](../../../README.md) · [Architecture overview](../../../docs/architecture.md) · [Results](../../../docs/RESULTS.md)

The first 96 entries are the baked A2_KNOBS values; later entries are zero-initialized. These values can be replaced or adjusted by recognised-map tables, hybrid presets and fitted map corrections. They are not the final live tuning values on every map.

References below are literal source lines, including disabled experiments. Within the main lab tuning block, `k` aliases `lab::knobs`. Elsewhere only explicitly named lab/RT references are collected. The complete compiler snapshots remain in this directory.

| Index | Baked value | Source use(s) |
|---|---|---|
| 0 | -0.2324 | [bot.cpp:8307](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8307): `tune::kAggression *= std::exp(0.3f * k[0]);` |
| 1 | 0.0063 | [bot.cpp:8308](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8308): `tune::kRetreatHp = std::clamp(tune::kRetreatHp + 0.1f * k[1], 0.05f, 0.95f);` |
| 2 | 0.0843 | [bot.cpp:8309](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8309): `tune::kDangerTtd *= std::exp(0.3f * k[2]);` |
| 3 | -0.2104 | [bot.cpp:8310](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8310): `tune::kDangerHp = std::clamp(b_dhp + 0.05f * k[3], 0.0f, 0.9f);` |
| 4 | -0.1657 | [bot.cpp:8311](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8311): `tune::kTributeCarry = std::max(8, ri(static_cast<float>(tune::kTributeCarry) * std::exp(0.3f * k[4])));` |
| 5 | -1.1852 | [bot.cpp:8312](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8312): `tune::kHuntRange = std::max(0, b_hunt_range + ri(3.0f * k[5]));` |
| 6 | 1.2152 | [bot.cpp:8313](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8313): `tune::kHuntHp = std::clamp(b_hunt_hp + 0.1f * k[6], 0.1f, 1.0f);` |
| 7 | 0.2588 | [bot.cpp:8314](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8314): `tune::kChaseRange = std::max(0, b_chase + ri(2.0f * k[7]));` |
| 8 | 0.8167 | [bot.cpp:8315](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8315): `tune::kGoldWeight *= std::exp(0.4f * k[8]);` |
| 9 | 1.0175 | [bot.cpp:8316](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8316): `tune::kWaitWeight = b_wait * std::exp(0.4f * k[9]);` |
| 10 | 1.4503 | [bot.cpp:8317](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8317): `tune::kNeedPool = b_need * std::exp(0.3f * k[10]);` |
| 11 | -0.7013 | [bot.cpp:8318](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8318): `tune::kCohesion = std::max(0.0f, tune::kCohesion + 0.05f * k[11]);` |
| 12 | 1.6018 | [bot.cpp:8319](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8319): `tune::kShopGold = std::max(30, tune::kShopGold + ri(30.0f * k[12]));` |
| 13 | -0.2131 | [bot.cpp:8320](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8320): `tune::kHuntGems = std::max(0, b_hunt_gems + ri(5.0f * k[13]));` |
| 14 | 0.3883 | [bot.cpp:8321](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8321): `tune::kStageTimeout = std::max(1, b_stage + ri(3.0f * k[14]));` |
| 15 | 1.2392 | [bot.cpp:8322](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8322): `if (k[15] > 1.0f) tune::kHunt = true;`<br>[bot.cpp:8323](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8323): `else if (k[15] < -1.0f) tune::kHunt = false;`<br>[fbstyle.h:54](../../../bots/mainline/v306AltarPressureReach/src/fbstyle.h#L54): `lab::knobs[15] = 2.0f; // hunt on` |
| 16 | 0.0052 | No literal-index use found by this index; may be accessed through a table or loop. |
| 17 | -0.5969 | No literal-index use found by this index; may be accessed through a table or loop. |
| 18 | 0.7784 | No literal-index use found by this index; may be accessed through a table or loop. |
| 19 | -1.1362 | No literal-index use found by this index; may be accessed through a table or loop. |
| 20 | 1.1544 | No literal-index use found by this index; may be accessed through a table or loop. |
| 21 | -0.1137 | No literal-index use found by this index; may be accessed through a table or loop. |
| 22 | 0.4351 | [bot.cpp:8324](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8324): `tune::kAggression *= std::exp(0.3f * (range > 1 ? k[23] : k[22])); // melee / ranged aggression` |
| 23 | -0.0003 | [bot.cpp:8324](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8324): `tune::kAggression *= std::exp(0.3f * (range > 1 ? k[23] : k[22])); // melee / ranged aggression` |
| 24 | -0.4823 | [tsearch.cpp:898](../../../bots/mainline/v306AltarPressureReach/src/tsearch.cpp#L898): `wts.alive *= std::exp(0.3f * LABK(24));` |
| 25 | 0.7086 | [tsearch.cpp:899](../../../bots/mainline/v306AltarPressureReach/src/tsearch.cpp#L899): `wts.hp *= std::exp(0.3f * LABK(25));` |
| 26 | 0.8082 | [tsearch.cpp:900](../../../bots/mainline/v306AltarPressureReach/src/tsearch.cpp#L900): `wts.threat *= std::exp(0.3f * LABK(26));` |
| 27 | 0.4128 | [tsearch.cpp:901](../../../bots/mainline/v306AltarPressureReach/src/tsearch.cpp#L901): `wts.gem *= std::exp(0.3f * LABK(27));` |
| 28 | -0.5672 | [tsearch.cpp:902](../../../bots/mainline/v306AltarPressureReach/src/tsearch.cpp#L902): `if (LABK(28) != 0.0f &#124;&#124; LABK(29) != 0.0f)`<br>[tsearch.cpp:904](../../../bots/mainline/v306AltarPressureReach/src/tsearch.cpp#L904): `mdl.flee[1] = std::clamp(mdl.flee[1] + 0.1f * LABK(28), 0.02f, 0.9f);` |
| 29 | 0.1350 | [tsearch.cpp:902](../../../bots/mainline/v306AltarPressureReach/src/tsearch.cpp#L902): `if (LABK(28) != 0.0f &#124;&#124; LABK(29) != 0.0f)`<br>[tsearch.cpp:905](../../../bots/mainline/v306AltarPressureReach/src/tsearch.cpp#L905): `mdl.flee[0] = std::clamp(mdl.flee[0] + 0.1f * LABK(29), 0.02f, 0.9f);` |
| 30 | -0.7099 | [tsearch.cpp:995](../../../bots/mainline/v306AltarPressureReach/src/tsearch.cpp#L995): `const float margin = std::max(0.0f, tune::kTsDecideMargin + LABK(30)); // lab knob 30: decide margin` |
| 31 | 0.2795 | [tsearch.cpp:910](../../../bots/mainline/v306AltarPressureReach/src/tsearch.cpp#L910): `int rounds = std::max(1, tune::kTsDecideRounds + static_cast<int>(std::lround(LABK(31)))); // lab knob 31: horizon` |
| 32 | 0.9522 | [tsearch.cpp:1150](../../../bots/mainline/v306AltarPressureReach/src/tsearch.cpp#L1150): `float risk = tune::kCMicroRisk * std::exp(0.3f * LABK(32)) * (1.0f + 1.5f * (1.0f - frac)); // lab knob 32` |
| 33 | -0.2219 | [bot.cpp:8332](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8332): `if (type == bc::champion_type::marcella) tune::kTributeCarry = std::max(8, ri(static_cast<float>(tune::kTributeCarry) * std::exp(0.3f * k[33])));` |
| 34 | -0.0928 | [bot.cpp:8333](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8333): `if (type == bc::champion_type::prism) tune::kTributeCarry = std::max(8, ri(static_cast<float>(tune::kTributeCarry) * std::exp(0.3f * k[34])));` |
| 35 | 0.2524 | [bot.cpp:449](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L449): `if (t == bc::champion_type::vesper_vale) items -= 3.0f * LABK(35);` |
| 36 | -1.6983 | [bot.cpp:5519](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L5519): `dist <= tune::kTributeNearDist + static_cast<int>(std::lround(2.0f * LABK(36))) &#124;&#124; (threatened && gems >= 20 && dist <= 8);` |
| 37 | 0.6817 | [bot.cpp:5493](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L5493): `std::max(ally_score, enemy_score) >= tune::kEndBank + static_cast<int>(std::lround(150.0f * LABK(37)));` |
| 38 | -0.1998 | [bot.cpp:6777](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L6777): `const int over = dmin - (tune::kCohesionDist + static_cast<int>(std::lround(2.0f * LABK(38))));` |
| 39 | 0.5488 | [bot.cpp:2253](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L2253): `if (ward_pos.x >= 0 && cheb(ward_pos, pos) <= NOVA_WARD_AHEAD + static_cast<int>(std::lround(2.0f * LABK(39)))) return false; // our ward still covers this area` |
| 40 | 0.3169 | [bot.cpp:6601](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L6601): `const float mid_mult = gi < mid_group.size() && mid_group[gi] ? A2_MID_W * std::exp(0.3f * LABK(40)) : 1.0f;` |
| 41 | 2.0716 | [bot.cpp:4324](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L4324): `const float tf_engage = (A2_TEAMFIGHT & 1) ? A2_TF_ENGAGE : LABK(41) > 0.0f ? 3.0f / (1.0f + LABK(41)) : 1e30f;` |
| 42 | 1.0775 | [bot.cpp:2098](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L2098): `const bool prelock = tune::kPrelock &#124;&#124; LABK(42) > 0.0f;`<br>[bot.cpp:2099](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L2099): `const int prelock_score = tune::kPrelock ? tune::kPrelockScore : std::max(0, static_cast<int>(600.0f - 300.0f * LABK(42)));` |
| 43 | -0.2822 | [bot.cpp:8328](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8328): `tune::kAggression *= std::exp(0.3f * k[43]);` |
| 44 | 1.2772 | [bot.cpp:8329](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8329): `tune::kHuntRange = std::max(0, tune::kHuntRange + ri(3.0f * k[44]));` |
| 45 | -0.5667 | [bot.cpp:8251](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8251): `lab::knobs[45] = lab::knobs[46] = lab::knobs[47] = 0.0f;`<br>[bot.cpp:8347](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8347): `tune::kAggression *= std::exp(0.3f * k[45]) * std::max(0.2f, 1.0f + 0.5f * k[46] * miss);` |
| 46 | -0.9572 | [bot.cpp:8251](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8251): `lab::knobs[45] = lab::knobs[46] = lab::knobs[47] = 0.0f;`<br>[bot.cpp:8347](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8347): `tune::kAggression *= std::exp(0.3f * k[45]) * std::max(0.2f, 1.0f + 0.5f * k[46] * miss);` |
| 47 | 1.5081 | [bot.cpp:8251](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8251): `lab::knobs[45] = lab::knobs[46] = lab::knobs[47] = 0.0f;`<br>[bot.cpp:8348](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8348): `tune::kRetreatHp = std::clamp(tune::kRetreatHp + 0.1f * k[47], 0.02f, 0.95f);` |
| 48 | -0.3549 | [bot.cpp:8388](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8388): `if ((A2_STANCE & 1) && RTG(48) && round - st_last > A2_ST_QUIET) tune::kTerritory = std::max(tune::kTerritory, A2_ST_EXP_TERR);` |
| 49 | 0.3643 | [bot.cpp:8389](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8389): `if ((A2_STANCE & 2) && RTG(49) && st_inv > A2_ST_HI) tune::kTerritory *= A2_ST_DEF_TERR, tune::kAggression *= A2_ST_DEF_AGGR;` |
| 50 | -0.5579 | [bot.cpp:4935](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L4935): `if (!RTG(50) &#124;&#124; round < A2_PH_FROM &#124;&#124; round > A2_PH_UNTIL &#124;&#124; team_size < 3 &#124;&#124; slot > 1) return false;` |
| 51 | -0.2293 | [common.h:122](../../../bots/mainline/v306AltarPressureReach/src/common.h#L122): `#define A2_PH_RANGE (12 + static_cast<int>(std::lround(4.0f * lab::knobs[51])))` |
| 52 | 1.2729 | [common.h:123](../../../bots/mainline/v306AltarPressureReach/src/common.h#L123): `#define A2_PH_HP std::clamp(0.55f + 0.1f * lab::knobs[52], 0.3f, 0.9f)` |
| 53 | -0.2749 | [bot.cpp:6761](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L6761): `if (RTG(53) && round >= A2_RD_FROM && slot == team_size - 1 && team_size >= 3 && w.enemy_ready && w.group_margin[gi] < -tune::kTerritoryMargin &&` |
| 54 | 1.5455 | [common.h:125](../../../bots/mainline/v306AltarPressureReach/src/common.h#L125): `#define A2_RD_MULT std::exp(0.3f * lab::knobs[54])` |
| 55 | 0.8006 | [bot.cpp:4678](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L4678): `if ((tune::kPosition &#124;&#124; RTX(55)) && dist <= range + 1 && position_and_attack(*target)) {` |
| 56 | -1.6255 | [bot.cpp:2747](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L2747): `if (!(melee &#124;&#124; (A2_TPS && RTG(56))) &#124;&#124; !me.can_move()) return false;`<br>[bot.cpp:2751](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L2751): `if ((e.id != target.id &#124;&#124; (A2_TPS && RTG(56) && !melee)) && cheb(q, e.pos) <= e.range + 1) threat += e.strength + e.focus * 0.25f;`<br>[bot.cpp:2756](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L2756): `if (RTG(56) && cheb(a.pos, q) <= 2 && a.hp >= 0.3f * a.max_hp) threat -= A2_TPS_ALLY * (a.strength + a.focus * 0.25f);` |
| 57 | 0.5251 | [bot.cpp:2759](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L2759): `if (SPACING &#124;&#124; RTX(57)) {` |
| 58 | -0.9368 | [bot.cpp:4376](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L4376): `if ((A2_CMDR & 1) && RTG(58) && nearest) {` |
| 59 | -0.0538 | [common.h:128](../../../bots/mainline/v306AltarPressureReach/src/common.h#L128): `#define A2_CM_FIGHT std::clamp(0.55f + 0.05f * lab::knobs[59], 0.5f, 0.9f)` |
| 60 | -0.0849 | [bot.cpp:4970](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L4970): `if (!((A2_CMDR & 2) && RTG(60)) &#124;&#124; round > A2_CM_UNTIL &#124;&#124; hp < max_hp * 0.5f &#124;&#124; gems >= 40 &#124;&#124; !bc::self().can_move()) return false;` |
| 61 | 0.4845 | [bot.cpp:3680](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L3680): `if (RTG(61) && !w.enemies.empty()) {` |
| 62 | -0.0464 | [bot.cpp:8357](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8357): `tune::kTerritory = HOME_TERR * RTV(62, 0.3f);` |
| 63 | -0.7602 | [draft.cpp:532](../../../bots/mainline/v306AltarPressureReach/src/draft.cpp#L532): `if (RTG(63) && !have && chosen.size() >= at) {` |
| 64 | -0.0164 | [bot.cpp:5011](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L5011): `if (!RTG(64) &#124;&#124; w.enemies.empty() &#124;&#124; w.allies.empty() &#124;&#124; !bc::self().can_move()) return false;` |
| 65 | -0.2232 | [bot.cpp:2351](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L2351): `if (!RTG(65) &#124;&#124; !w.enemies.empty() &#124;&#124; w.allies.empty()) return false;` |
| 66 | -0.1354 | [bot.cpp:3706](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L3706): `if (NOVA_BURST_K * RTV(66, 0.3f) > 0.0f) {`<br>[bot.cpp:3733](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L3733): `if (burst > 0.0f && my_hp < NOVA_BURST_K * RTV(66, 0.3f) * burst && !sure_kill) {` |
| 67 | 0.6741 | No literal-index use found by this index; may be accessed through a table or loop. |
| 68 | 0.5647 | No literal-index use found by this index; may be accessed through a table or loop. |
| 69 | -0.3054 | No literal-index use found by this index; may be accessed through a table or loop. |
| 70 | -0.3439 | No literal-index use found by this index; may be accessed through a table or loop. |
| 71 | 0.1171 | No literal-index use found by this index; may be accessed through a table or loop. |
| 72 | 0.4163 | No literal-index use found by this index; may be accessed through a table or loop. |
| 73 | -0.3921 | No literal-index use found by this index; may be accessed through a table or loop. |
| 74 | 0.4346 | No literal-index use found by this index; may be accessed through a table or loop. |
| 75 | 0.6407 | No literal-index use found by this index; may be accessed through a table or loop. |
| 76 | -0.1769 | No literal-index use found by this index; may be accessed through a table or loop. |
| 77 | 0.2024 | No literal-index use found by this index; may be accessed through a table or loop. |
| 78 | 0.8318 | No literal-index use found by this index; may be accessed through a table or loop. |
| 79 | 1.0071 | No literal-index use found by this index; may be accessed through a table or loop. |
| 80 | -0.0116 | No literal-index use found by this index; may be accessed through a table or loop. |
| 81 | 0.0373 | No literal-index use found by this index; may be accessed through a table or loop. |
| 82 | 0.6371 | No literal-index use found by this index; may be accessed through a table or loop. |
| 83 | -0.4819 | No literal-index use found by this index; may be accessed through a table or loop. |
| 84 | 0.0910 | No literal-index use found by this index; may be accessed through a table or loop. |
| 85 | -0.3740 | No literal-index use found by this index; may be accessed through a table or loop. |
| 86 | 0.3058 | No literal-index use found by this index; may be accessed through a table or loop. |
| 87 | 0.6491 | No literal-index use found by this index; may be accessed through a table or loop. |
| 88 | 0.4807 | No literal-index use found by this index; may be accessed through a table or loop. |
| 89 | -0.5459 | No literal-index use found by this index; may be accessed through a table or loop. |
| 90 | -1.0419 | No literal-index use found by this index; may be accessed through a table or loop. |
| 91 | -0.8667 | No literal-index use found by this index; may be accessed through a table or loop. |
| 92 | -0.5335 | No literal-index use found by this index; may be accessed through a table or loop. |
| 93 | -0.4068 | No literal-index use found by this index; may be accessed through a table or loop. |
| 94 | -0.1135 | No literal-index use found by this index; may be accessed through a table or loop. |
| 95 | -0.2327 | No literal-index use found by this index; may be accessed through a table or loop. |
| 96 | 0 | [bot.cpp:8281](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8281): `for (int j = 0; j < 16; ++j) lab::knobs[kLadIdx[j]] += ladfit::kFit[m][j] + lab::knobs[96 + j];` |
| 97 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 98 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 99 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 100 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 101 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 102 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 103 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 104 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 105 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 106 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 107 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 108 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 109 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 110 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 111 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 112 | 0 | [bot.cpp:8282](../../../bots/mainline/v306AltarPressureReach/src/bot.cpp#L8282): `for (int j = 0; j < 8; ++j) lab::knobs[kLadSw[j]] += ladfit::kFit[m][16 + j] + lab::knobs[112 + j];` |
| 113 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 114 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 115 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 116 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 117 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 118 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
| 119 | 0 | No literal-index use found by this index; may be accessed through a table or loop. |
