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


PATCHES = {"contest": contest}

if __name__ == "__main__":
    src = sys.argv[1]
    for name in sys.argv[2:]:
        PATCHES[name](src)
        print("applied", name)
