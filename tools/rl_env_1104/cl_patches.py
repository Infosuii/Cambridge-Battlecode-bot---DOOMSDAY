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


PATCHES = {"contest": contest, "waitcap": waitcap, "hiderec": hiderec, "earlyshop": earlyshop}

if __name__ == "__main__":
    src = sys.argv[1]
    for name in sys.argv[2:]:
        PATCHES[name](src)
        print("applied", name)
