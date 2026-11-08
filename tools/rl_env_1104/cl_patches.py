"""Claude's bot patches on top of exact v112 source (agentic-1108:auto_bank_arrive_learned, WASM 932030e0).

usage: python -I tools/rl_env_1104/cl_patches.py <src_dir> <patch> [<patch> ...]

Patches (each is a small, guarded change with its own #define, default on when applied):
  contest   CL_CONTEST: contested-capture stall breaker. Engine capture_state() is checked while holding a reward
            region. After CL_CONTEST_T turns contested (or at once with a bag >= CL_CONTEST_BAG): push the weakest
            visible enemy on/near the region when we outnumber them; otherwise keep one healthy light-bagged anchor
            (lowest id) to deny the capture and release the others for CL_CONTEST_AWAY rounds; the anchor itself
            releases after 3 x CL_CONTEST_T. A big bag banks instead of standing in a standoff.
            Local evidence (v112-capture-trace-01): v112 held contested rewards for ~1,900 turns per game on 00vault
            and ~3,400 on 04lines with the engine timer frozen at 5.
"""
import os
import sys


def patch(src, name, old, new, count=1):
    p = os.path.join(src, name)
    t = open(p, encoding="utf-8", newline="").read()
    crlf = "\r\n" in t
    if crlf:
        t = t.replace("\r\n", "\n")
    assert t.count(old) == count, (name, old[:70], t.count(old))
    t = t.replace(old, new)
    if crlf:
        t = t.replace("\n", "\r\n")
    open(p, "w", encoding="utf-8", newline="").write(t)


def contest(src):
    patch(src, "common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_CONTEST 1\n")
    patch(src, "bot.h", "    int target_group = -1;\n", """    int target_group = -1;
#if CL_CONTEST
    int cl_cg = -1, cl_cturns = 0, cl_crelease_g = -1;
    bool cl_contest(GroupRec& g);
#endif
""")
    impl = r'''
#if CL_CONTEST
#ifndef CL_CONTEST_T
#define CL_CONTEST_T 12
#endif
#ifndef CL_CONTEST_AWAY
#define CL_CONTEST_AWAY 40
#endif
#ifndef CL_CONTEST_BAG
#define CL_CONTEST_BAG 40
#endif
// CL_CONTEST: we stand on a reward region. Returns true when this turn was spent here (push, bank or hold after a
// release decision), false to keep the normal capture hold.
bool Bot::cl_contest(GroupRec& g) {
    const int gi = static_cast<int>(&g - &w.groups[0]);
    d::camp_group_capture_state cs{};
    if (d::sdk_camp_group_capture_state(g.handle, &cs) != 0) return false;
    if (cs.state != 2 && cs.state != 3) { // not contested / enemy capturing: our capture runs
        cl_cg = gi;
        cl_cturns = 0;
        return false;
    }
    if (cl_cg != gi) cl_cg = gi, cl_cturns = 0;
    ++cl_cturns;
    const bool big_bag = gems >= CL_CONTEST_BAG;
    if (cl_cturns < CL_CONTEST_T && !big_bag) return false;
    const EnemyRec* weakest = nullptr;
    int theirs = 0;
    for (const auto& e : w.enemies) {
        if (e.hp <= 0 || !(bit(g.tiles, e.pos) || cheb(e.pos, pos) <= 3)) continue;
        ++theirs;
        if (!weakest || e.hp < weakest->hp) weakest = &e;
    }
    int ours = 1;
    for (const auto& a : w.allies)
        if (a.id != my_id && a.hp >= 0.5f * a.max_hp && (bit(g.tiles, a.pos) || cheb(a.pos, pos) <= 3)) ++ours;
    if (!big_bag && weakest && ours >= theirs + 1 && hp >= 0.6f * max_hp) {
        mode = "contest-push";
        FlagScope combat{combat_move};
        if (cheb(weakest->pos, pos) <= range) {
            cast_on_enemy(*weakest);
            if (attack_unit(weakest->unit, weakest->pos)) use_reset_and_attack(weakest->unit, weakest->pos);
            return true;
        }
        bc::bitboard goal;
        goal.clear();
        goal.draw_chebyshev(weakest->pos, static_cast<float>(range));
        walk_toward(goal);
        if (cheb(weakest->pos, pos) <= range) {
            cast_on_enemy(*weakest);
            attack_unit(weakest->unit, weakest->pos);
        }
        return true;
    }
    std::uint32_t anchor = (!big_bag && hp >= 0.6f * max_hp) ? my_id : 0xffffffffu;
    for (const auto& a : w.allies) {
        if (a.id == my_id || !bit(g.tiles, a.pos) || a.hp < 0.6f * a.max_hp) continue;
        int bag = 0;
        try {
            bag = static_cast<int>(a.unit.gem_count());
        } catch (...) {
            continue;
        }
        if (bag >= CL_CONTEST_BAG) continue;
        anchor = std::min(anchor, a.id);
    }
    if (anchor == my_id && cl_cturns < 3 * CL_CONTEST_T) return false; // the anchor keeps denying the capture
    if (gi < static_cast<int>(avoid_until.size())) avoid_until[gi] = std::max(avoid_until[gi], round + CL_CONTEST_AWAY);
    cl_crelease_g = gi;
    if (nn_group == gi) nn_group = -1;
    target_group = -1;
    write_claim(-1);
    cl_cturns = 0;
    if (big_bag) {
        force_tribute = true;
        if (tribute_if_needed()) {
            mode = "contest-bank";
            return true;
        }
        force_tribute = false;
    }
    mode = "contest-release";
    return true;
}
#endif

void Bot::opportunistic_attack() {'''
    patch(src, "bot.cpp", "\nvoid Bot::opportunistic_attack() {", impl)
    patch(src, "bot.cpp", """        mode = "capture";
        if (bit(g.tiles, pos)) return true; // capturing: hold position
""", """        mode = "capture";
#if CL_CONTEST
        if (bit(g.tiles, pos) && cl_contest(g)) return true;
#endif
        if (bit(g.tiles, pos)) return true; // capturing: hold position
""")
    # the network's override must not send us straight back into a released standoff
    patch(src, "bot.cpp", "#ifdef A2_NN_NEED\n    // E126", """#if CL_CONTEST
    if (cl_crelease_g >= 0 && cl_crelease_g < static_cast<int>(avoid_until.size()) && avoid_until[cl_crelease_g] > round) {
        if (nn_group == cl_crelease_g) nn_group = -1;
        if (best == cl_crelease_g) best = score_groups(1, best_need, best_score);
    }
#endif
#ifdef A2_NN_NEED
    // E126""")


def waitcap(src):
    """CL_WAITCAP: never stand waiting for a respawn more than CL_WAITCAP rounds away. The network's candidate set is
    the 10 nearest groups regardless of avoid_until, so after every override a far respawn is replaced by the v92
    pick (score_groups skips avoided groups); the group is avoided until CL_WAITBACK rounds before it respawns.
    Local evidence (v112-stall-trace-01): 04standing-stones home camps held 57-round waits from round 40."""
    patch(src, "common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_WAITCAP 20\n")
    patch(src, "bot.cpp", "#ifdef A2_NN_NEED\n    // E126", """#if CL_WAITCAP
#ifndef CL_WAITBACK
#define CL_WAITBACK 15
#endif
    for (int tries = 0; tries < 2 && best >= 0 && best < static_cast<int>(w.groups.size()); ++tries) {
        const auto& gw = w.groups[static_cast<std::size_t>(best)];
        if (gw.state != GroupState::respawning) break;
        const int wd = w.has_field(best) ? w.group_distance(best, pos) : 0;
        if (gw.respawn_round - round - std::min(wd, 60) <= CL_WAITCAP) break;
        if (best < static_cast<int>(avoid_until.size()))
            avoid_until[static_cast<std::size_t>(best)] = std::max(avoid_until[static_cast<std::size_t>(best)], gw.respawn_round - CL_WAITBACK);
        if (nn_group == best) nn_group = -1;
        best = score_groups(1, best_need, best_score);
    }
#endif
#ifdef A2_NN_NEED
    // E126""")


def hiderec(src):
    """A2_HIDEREC=1 (existing, default off in v112): a recall begun from a bush no enemy can see into is not cancelled
    by the channel guard. Without it the bush recall and the guard alternate every turn while an enemy waits outside
    (lab logs: 77% of bush recalls cancelled the next turn; JOHNDOE #171 stalled recall loop)."""
    patch(src, "common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define A2_HIDEREC 1\n")


def earlyshop(src, gold=90, until=300):
    """CL_EARLYSHOP: before round CL_EARLYSHOP_UNTIL the gold-only shopping trip starts at CL_EARLYSHOP gold instead of
    v112's knob-tuned ~174. Ladder evidence (2400+ teams vs v112): top teams have spent 91/168 of team gold by R50 and
    285/395 by R100 (us 31/147 and 176/341), and earn 25-31% more gold by R100-R300 with the same clear count by R50."""
    patch(src, "common.h", "#define A2_KITFIX 31\n", f"#define A2_KITFIX 31\n#define CL_EARLYSHOP {gold}\n#define CL_EARLYSHOP_UNTIL {until}\n")
    patch(src, "bot.cpp", "    tune::kShopGold = std::max(30, static_cast<int>(static_cast<float>(tune::kShopGold) * GT_SHOP));\n",
          """    tune::kShopGold = std::max(30, static_cast<int>(static_cast<float>(tune::kShopGold) * GT_SHOP));
#if CL_EARLYSHOP
    if (round < CL_EARLYSHOP_UNTIL) tune::kShopGold = std::min(tune::kShopGold, CL_EARLYSHOP);
#endif
""")


PROFILES = {  # tools/v67/c_profiles.py --list (deltas on the lab knob vector, research/v71)
    "aggr": {0: 1.0, 22: 1.0, 23: 1.0, 43: 1.0}, "caut": {0: -1.0, 22: -1.0, 23: -1.0, 43: -1.0, 3: 2.0, 1: 1.0},
    "bank": {4: -1.5, 36: 1.5, 37: -1.0}, "hoard": {4: 1.5, 36: -1.0}, "hunt": {5: 1.0, 7: 1.0, 13: -1.0, 44: 1.0, 6: -1.0},
    "group": {11: 3.0, 38: -1.0, 41: 1.0}, "gems": {8: -1.5}, "gold": {8: 1.5}, "mid": {40: 2.0}, "nomid": {40: -2.0},
    "search": {24: -1.0, 25: 1.0, 31: 1.0}, "ranged": {32: -1.5, 23: 1.0}, "ranged2": {32: -3.0, 23: 2.0},
    "huntranged": {5: 1.0, 7: 1.0, 13: -1.0, 44: 1.0, 6: -1.0, 32: -1.5, 23: 1.0}, "softcaut": {0: -0.5, 22: -0.5, 23: -0.5, 3: 1.0},
    "softaggr": {0: 0.5, 22: 0.5, 23: 0.5}, "teamfight": {41: 2.0}, "spread": {10: -2.0, 11: -3.0}, "wait": {9: 2.0},
    "nowait": {9: -2.0}, "shopmore": {12: 2.0}, "shopless": {12: -2.0}, "calm": {2: -1.0},
}


def profile(src, name):
    """CL_NEWMAP_PROFILE: apply one research/v71 knob profile on maps v112's LADDER_TABLES do not recognise (83 of the
    128 live-pool maps; v112 wins 49.8% there vs 56.9% on the 45 tuned maps). Recognised maps are unchanged."""
    d = PROFILES[name]
    vals = ", ".join(f"{{{k}, {v}f}}" for k, v in d.items())
    patch(src, "common.h", "#define A2_KITFIX 31\n", f"#define A2_KITFIX 31\n#define CL_NEWMAP_PROFILE {vals}\n")
    patch(src, "bot.cpp", "                break;\n            }\n        }\n#endif\n    }\n#endif\n#if A2_LAB\n",
          """                break;
            }
        }
#endif
#ifdef CL_NEWMAP_PROFILE
        if (!ladder_known) {
            static constexpr float kClProf[][2] = {CL_NEWMAP_PROFILE};
            for (const auto& p : kClProf) lab::knobs[static_cast<int>(p[0])] += p[1];
        }
#endif
    }
#endif
#if A2_LAB
""")


def newmap_table(src, table_h):
    """CL_NEWMAP_TABLE: per-map research/v71 profile (cl_newmap_table.h from train/profile_table.py) on maps v112's
    LADDER_TABLES do not recognise, matched by the same fingerprint (width, height, groups, total group gems)."""
    import shutil
    shutil.copy(table_h, os.path.join(src, "cl_newmap_table.h"))
    patch(src, "common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_NEWMAP_TABLE 1\n")
    patch(src, "bot.cpp", '#include "a2map.h"\n', '#include "a2map.h"\n#if CL_NEWMAP_TABLE\n#include "cl_newmap_table.h"\n#endif\n')
    patch(src, "bot.cpp", "                break;\n            }\n        }\n#endif\n    }\n#endif\n#if A2_LAB\n",
          """                break;
            }
        }
#endif
#if CL_NEWMAP_TABLE
        if (!ladder_known)
            for (const auto& row : cl_newmap::kRows)
                if (row.w == w.width && row.h == w.height && row.groups == n_groups && row.gems == total_gems) {
                    for (int i = 0; i < 48; ++i) lab::knobs[i] += cl_newmap::kDelta[row.profile][i];
                    break;
                }
#endif
    }
#endif
#if A2_LAB
""")


def winrecall(src):
    """CL_WINRECALL: break the win-now recall loop (JOHNDOE #171: a 414-gem Vendetta cancelled and restarted recall
    every round R1154-1168 and the game was lost with 465 gems held). The channel guard cancels a recall when the bag
    finishes the race; if banking then fails, go_home_if_needed recalled again the same turn. After a win-cancel no
    recall is started for 3 rounds (walking home / to the altar is still allowed)."""
    patch(src, "common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_WINRECALL 1\n")
    patch(src, "bot.h", "    int target_group = -1;\n", "    int target_group = -1;\n#if CL_WINRECALL\n    int cl_wincancel_round = -100;\n#endif\n")
    patch(src, "bot.cpp", """    if (state.contains(bc::champion_state::recalling) && win_now() && hp >= max_hp * tune::kDangerHp) {
        try {
            me.cancel_recall();""", """    if (state.contains(bc::champion_state::recalling) && win_now() && hp >= max_hp * tune::kDangerHp) {
#if CL_WINRECALL
        cl_wincancel_round = round;
#endif
        try {
            me.cancel_recall();""")
    patch(src, "bot.cpp", """    if (dist > tune::kShopWalkDist && !enemy_close) {
        try {
            me.recall();""", """    if (dist > tune::kShopWalkDist && !enemy_close
#if CL_WINRECALL
        && round - cl_wincancel_round > 3
#endif
    ) {
        try {
            me.recall();""")


def aoereach(src):
    """CL_AOEREACH: an area spell (radius r) can hit a camp at distance range + r by aiming at a tile within range next
    to it (ISHAN EXP-217/218: verified for Ryth, Stellar and Prism at distance 5). cast_on_camp rejected every camp
    beyond `range`; it now aims such casts at the in-range tile adjacent to the camp that hits the most live camps."""
    patch(src, "common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_AOEREACH 1\n")
    patch(src, "bot.cpp", """        if (sp.excludes_walk && walked) continue;
        if (cheb(pos, c.pos) > static_cast<int>(sp.range)) continue;
        // Stuns win champion fights""", """        if (sp.excludes_walk && walked) continue;
#if CL_AOEREACH
        if (cheb(pos, c.pos) > static_cast<int>(sp.range) +
                (sp.kind == bc::ability_kind::aoe_damage ? static_cast<int>(sp.radius) : 0)) continue;
#else
        if (cheb(pos, c.pos) > static_cast<int>(sp.range)) continue;
#endif
        // Stuns win champion fights""")
    patch(src, "bot.cpp", """    try {
        const auto ab = bc::self().abilities()[best];
        const bool ok = spells[best].kind == bc::ability_kind::aoe_damage ? ab.use(c.pos) : ab.use(c.camp);""", """    try {
        const auto ab = bc::self().abilities()[best];
#if CL_AOEREACH
        vec2 aim = c.pos;
        if (spells[best].kind == bc::ability_kind::aoe_damage && cheb(pos, c.pos) > static_cast<int>(spells[best].range)) {
            const int rr = static_cast<int>(spells[best].radius);
            int best_hits = -1;
            for (int dx = -rr; dx <= rr; ++dx)
                for (int dy = -rr; dy <= rr; ++dy) {
                    const vec2 t{c.pos.x + dx, c.pos.y + dy};
                    if (t.x < 0 || t.y < 0 || t.x >= w.width || t.y >= w.height) continue;
                    if (cheb(pos, t) > static_cast<int>(spells[best].range)) continue;
                    int hits = 0;
                    for (int other : w.groups[w.group_of_camp_tile(c.pos)].camps)
                        if (!w.camps[other].dead && cheb(w.camps[other].pos, t) <= rr) ++hits;
                    if (hits > best_hits) best_hits = hits, aim = t;
                }
        }
        const bool ok = spells[best].kind == bc::ability_kind::aoe_damage ? ab.use(aim) : ab.use(c.camp);
#else
        const bool ok = spells[best].kind == bc::ability_kind::aoe_damage ? ab.use(c.pos) : ab.use(c.camp);
#endif""")


def clfs(src, value):
    """CLFS (JOHNDOE's fuel-safe change in parts, nnrec.cpp): 1 slow-block estimates, 2 scoring margin, 4 slower need
    decay, 8 warm-up and rebuild margins. v112/v114 ship 9. Ishan EXP-179 (on v111): 11 +2.9pp [-2.5, +9.2] with
    fuel-outs 692 vs 961; 13 -1.7pp. v114 locally: ~10.4 fuel-outs a game, 19% of turns above 90k of the 100k budget."""
    patch(src, "common.h", "#ifndef CLFS\n#define CLFS 9\n", f"#ifndef CLFS\n#define CLFS {value}\n")


def goldtrip(src, until=300, k=3.75, minrate=0.6):
    """CL_GOLDTRIP: a situational gold-only shopping trip instead of CL_EARLYSHOP's fixed 90 gold. Before round
    CL_GOLDTRIP_UNTIL a trip also starts below the per-map threshold (tune::kShopGold, still the upper bound) when
      buyable >= CL_GOLDTRIP_K x income x trip
    buyable: the gold shop() would spend on the build plan right now (its own loop, so 0 when nothing is affordable);
    income: this champion's own gold per round so far (at least CL_GOLDTRIP_MINRATE);
    trip: rounds lost: a recall channel plus the walk back out, or a walk both ways within kShopWalkDist of spawn.
    K = 3.75 puts a typical 30-round recall trip at ~90 gold of buyable items with ~0.8 gold/round (ladder: 341/5 per
    champion by R100), the early-shop level; near spawn it drops to ~40, far out it rises to ~135."""
    patch(src, "common.h", "#define A2_KITFIX 31\n",
          f"#define A2_KITFIX 31\n#define CL_GOLDTRIP 1\n#define CL_GOLDTRIP_UNTIL {until}\n#define CL_GOLDTRIP_K {k}f\n"
          f"#define CL_GOLDTRIP_MINRATE {minrate}f\n")
    patch(src, "bot.h", "    bool shop_done = false;", "    int cl_earned = 0; // CL_GOLDTRIP: gold this champion has earned\n    bool shop_done = false;")
    patch(src, "bot.cpp", "    gold = static_cast<int>(me.gold_count());\n    for (int s = 0; s < 2; ++s) {",
          """    {
        const int g_before = gold;
        gold = static_cast<int>(me.gold_count());
        if (gold > g_before) cl_earned += gold - g_before; // shop() keeps `gold` current when it spends
    }
    for (int s = 0; s < 2; ++s) {""")
    patch(src, "bot.cpp", "    bool rich = gold >= tune::kShopGold && !shop_done;\n", """    bool rich = gold >= tune::kShopGold && !shop_done;
#if CL_GOLDTRIP
    if (!rich && !shop_done && gold >= 30 && round < CL_GOLDTRIP_UNTIL) {
        // what shop() would spend now (same plan loop, without can_buy, which needs the spawn)
        static const auto cl_plan = build_for(type);
        const auto counts = bc::self().item_count();
        std::array<int, static_cast<std::size_t>(bc::item_type::count)> taken{};
        int left = gold, buyable = 0;
        for (const auto& step : cl_plan) {
            const int cost = std::max(1, static_cast<int>(step.item.cost()));
            int owned = taken[static_cast<std::size_t>(step.item)] + static_cast<int>(counts[step.item]);
            if (const auto emblem = step.item.result()) owned += static_cast<int>(counts[*emblem] * step.item.combine_count());
            const int want = std::min(step.total - owned, left / cost);
            if (want <= 0) continue;
            taken[static_cast<std::size_t>(step.item)] += want;
            buyable += want * cost, left -= want * cost;
            if (left < 30) break;
        }
        const int dist = static_cast<int>(fdist(w.spawn_field, pos));
        const int trip = dist > tune::kShopWalkDist ? bc::constants::recall_time + dist : 2 * dist;
        const float rate = std::max(CL_GOLDTRIP_MINRATE, static_cast<float>(cl_earned) / static_cast<float>(std::max(1, round)));
        rich = buyable > 0 && static_cast<float>(buyable) >= CL_GOLDTRIP_K * rate * static_cast<float>(trip);
    }
#endif
""")


TABLE_G3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "research", "rl_env_1104", "candidates",
                        "profiles", "profile_table_g3.h")

PATCHES = {"contest": contest, "waitcap": waitcap, "hiderec": hiderec, "earlyshop": earlyshop,
           "winrecall": winrecall, "aoereach": aoereach,
           "clfs9": lambda s: patch(s, "common.h", "#ifndef CLFS\n#define CLFS 15\n", "#ifndef CLFS\n#define CLFS 9\n"),
           "clfs11": lambda s: clfs(s, 11), "clfs15": lambda s: clfs(s, 15),
           "table": lambda s: newmap_table(s, TABLE_G3),
           "goldtrip": goldtrip, "goldtrip_all": lambda s: goldtrip(s, until=100000)}

if __name__ == "__main__":
    src = sys.argv[1]
    for name in sys.argv[2:]:
        PATCHES[name](src)
        print("applied", name)
