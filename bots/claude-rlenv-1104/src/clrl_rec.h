// CLRL_REC: teacher-trace recorder for the RL environment (task rl-env-collector-1104, research/rl_env_1104).
// Our own code: observation layout cl1 (CL1_SCHEMA.md) built from what this body legally knows (the World it keeps
// from its own vision and shared memory) plus SDK reads. Everything runs inside debug_block, so release builds drop it
// and debug builds don't charge its fuel. With CLRL_REC 0 (default) nothing here is compiled.
//
// Per alive turn: capture() right after the turn's world update (before any action), finish() after play_turn.
// One stdout row per decision:
//   CLR1 <round> <slot> <body_id> <macro> <prim> <dx> <dy> <reset> <b64 int16[448]>
// macro = v92's target group as a cl1 c-row (0..11) or 12; prim = primitive outcome bits measured by diffing the
// body's state at capture and at the end of its turn (1 moved, 2 attacked, 4 cast, 8 recall started, 16 submit
// started, 32 bought, 64 ward placed). Turns without a capture (dead, channelling) print no row; the first captured
// turn after a gap of dead rounds has reset 1.
#pragma once
#if CLRL_REC || CLRL_ACT
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

namespace clrl {
constexpr int kG = 16, kS = 32, kA = 5, kAW = 16, kE = 6, kEW = 16, kC = 12, kCW = 16, kL = 4, kLW = 8;
constexpr int kNF = kG + kS + kA * kAW + kE * kEW + kC * kCW + kL * kLW; // 448
static_assert(kNF == 448, "cl1 layout size");
constexpr int kOffS = kG, kOffA = kOffS + kS, kOffE = kOffA + kA * kAW, kOffC = kOffE + kE * kEW, kOffL = kOffC + kC * kCW;
constexpr int kAgeCap = 2000;
// Charged fuel of one recorder block outside its free window (guard entry/exit and the call), measured with
// e0_tests.py test 4 against a v92 debug build; refunded inside the block so the recorder's charged cost is zero.
#ifndef CLRL_REFUND
#define CLRL_REFUND 12
#endif

struct Seen {
    std::uint32_t id = 0;
    int type = -1, x = -1, y = -1, hp = -1, gems = -1, round = -1, range = -1;
};

struct State {
    std::int16_t f[kNF];
    int c_group[kC];   // World group index of each c-row (-1 empty)
    Seen enemies[kE];  // this body's own memory of enemy sightings, by first-seen order
    int n_enemies = 0;
    bool captured = false;
    int last_round = -1, cap_round = -1;
    int x0 = 0, y0 = 0, gold0 = 0, wards0 = 0;
    std::uint32_t state0 = 0;
    bool reset_next = true;
};
inline State st;

inline std::int16_t q(long v) { return static_cast<std::int16_t>(std::clamp<long>(v, -32000, 32000)); }
inline std::int16_t frac(float a, float b) { return q(b > 0 ? static_cast<long>(1000.0f * a / b) : -1); }
inline std::int16_t age(int now, int then) { return then < 0 ? std::int16_t{ -1 } : q(std::min(kAgeCap, now - then)); }
inline int cheb(int ax, int ay, int bx, int by) { return std::max(std::abs(ax - bx), std::abs(ay - by)); }

inline std::string b64(const std::int16_t* p, int n) {
    static const char* T = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    const auto* b = reinterpret_cast<const unsigned char*>(p);
    const int len = 2 * n;
    std::string s;
    s.reserve((len + 2) / 3 * 4);
    for (int i = 0; i < len; i += 3) {
        const unsigned v = (b[i] << 16) | ((i + 1 < len ? b[i + 1] : 0) << 8) | (i + 2 < len ? b[i + 2] : 0);
        s += T[(v >> 18) & 63];
        s += T[(v >> 12) & 63];
        s += i + 1 < len ? T[(v >> 6) & 63] : '=';
        s += i + 2 < len ? T[v & 63] : '=';
    }
    return s;
}

inline std::uint32_t state_bits(const bc::champion& me) {
    const auto s = me.state();
    using cs = bc::champion_state;
    std::uint32_t b = 0;
    const cs flags[] = { cs::alive, cs::recalling, cs::submitting_gems, cs::can_move, cs::can_attack, cs::can_cast,
                         cs::teleporting, cs::recall_started, cs::submit_gems_started };
    for (int i = 0; i < 9; ++i)
        if (s.contains(flags[i])) b |= 1u << i;
    return b;
}

} // namespace clrl

// The recorder's entry points; Bot declares this struct a friend (bot.h, CLRL_REC only).
struct ClrlFriend {
// Encode the observation of `bot` (a Bot) this turn into st.f. Called inside debug_block.
template <class BotT>
static void encode(const BotT& b) {
    using namespace clrl;
    auto& f = st.f;
    std::fill(f, f + kNF, static_cast<std::int16_t>(0)); // every row cleared each decision
    const auto& w = b.w;
    const int now = b.round, px = b.pos.x, py = b.pos.y;
    const auto& me = bc::self();

    // g: globals
    const int ours = static_cast<int>(bc::global_submitted_gems(bc::team::ally));
    const int theirs = static_cast<int>(bc::global_submitted_gems(bc::team::enemy));
    int near_spawn = 9999, near_altar = 9999;
    for (const auto& t : w.spawn_tiles) near_spawn = std::min(near_spawn, cheb(px, py, t.x, t.y));
    for (const auto& a : w.altars) near_altar = std::min(near_altar, cheb(px, py, a.x, a.y));
    f[0] = q(now);
    f[1] = q(ours);
    f[2] = q(theirs);
    f[3] = q(static_cast<long>(bc::constants::winning_gems));
    f[4] = q(b.team_size);
    f[5] = q(w.width);
    f[6] = q(w.height);
    f[7] = q(static_cast<long>(bc::symmetry()));
    f[8] = q(b.slot);
    f[9] = q(static_cast<long>(w.allies.size()) + 1);
    f[10] = q(static_cast<long>(w.enemies.size()));
    int recent = 0;
    for (int i = 0; i < st.n_enemies; ++i) recent += st.enemies[i].round >= 0 && now - st.enemies[i].round <= 50;
    f[11] = q(recent);
    f[12] = q(near_spawn == 9999 ? -1 : near_spawn);
    f[13] = q(near_altar == 9999 ? -1 : near_altar);
    f[14] = q(bc::draft_memory.size() > 0 ? 1 : 0);
    f[15] = q(static_cast<long>(bc::fuel_remaining() / 100));

    // s: self (engine id in the last field; the learner strips it)
    std::int16_t* s = f + kOffS;
    s[0] = q(static_cast<long>(b.type));
    s[1] = q(px);
    s[2] = q(py);
    s[3] = q(static_cast<long>(b.hp));
    s[4] = q(static_cast<long>(b.max_hp));
    s[5] = q(static_cast<long>(b.strength));
    s[6] = q(static_cast<long>(b.focus));
    s[7] = q(b.gems);
    s[8] = q(b.gold);
    s[9] = q(static_cast<long>(state_bits(me)));
    s[10] = q(b.cooldown[0]);
    s[11] = q(b.cooldown[1]);
    s[12] = q(b.range);
    s[13] = q(b.melee ? 1 : 0);
    s[14] = q(static_cast<long>(me.ward_positions().size()));
    s[31] = q(static_cast<long>(b.my_id));

    // a: allies by slot, excluding self (visible now from World; else present only)
    int ar = 0;
    for (int sl = 0; sl < b.team_size && ar < kA; ++sl) {
        if (sl == b.slot) continue;
        std::int16_t* a = f + kOffA + ar++ * kAW;
        a[0] = 1;
        a[1] = q(static_cast<long>(b.slot_type[sl]));
        a[2] = 0; // visible now
        for (const auto& al : w.allies) {
            if (al.id != b.ally_handle[sl]) continue;
            a[2] = 1;
            a[3] = q(al.pos.x - px);
            a[4] = q(al.pos.y - py);
            a[5] = frac(al.hp, al.max_hp);
            a[6] = q(cheb(px, py, al.pos.x, al.pos.y));
            a[7] = q(static_cast<long>(al.strength));
            a[8] = q(al.range);
        }
    }

    // e: enemies from this body's own sighting memory (updated from World's visible list first)
    for (const auto& e : w.enemies) {
        int k = 0;
        while (k < st.n_enemies && st.enemies[k].id != e.id) ++k;
        if (k == st.n_enemies) {
            if (st.n_enemies == kE) continue;
            st.enemies[st.n_enemies++].id = e.id;
        }
        auto& r = st.enemies[k];
        r.type = static_cast<int>(e.type);
        r.x = e.pos.x;
        r.y = e.pos.y;
        r.hp = e.max_hp > 0 ? static_cast<int>(1000.0f * e.hp / e.max_hp) : -1;
        r.gems = e.gems;
        r.round = now;
        r.range = e.range;
    }
    for (int k = 0; k < st.n_enemies; ++k) {
        const auto& r = st.enemies[k];
        std::int16_t* e = f + kOffE + k * kEW;
        const bool vis = r.round == now;
        e[0] = 1;
        e[1] = q(r.type);
        e[2] = vis ? 1 : 0;
        e[3] = age(now, r.round);
        e[4] = q(r.x - px);
        e[5] = q(r.y - py);
        e[6] = q(r.hp);
        e[7] = q(r.gems);
        e[8] = q(cheb(px, py, r.x, r.y));
        e[9] = q(r.range);
        e[10] = vis && cheb(px, py, r.x, r.y) <= b.range ? 1 : 0;
    }

    // c: the 12 nearest camp groups by Chebyshev distance to their member centroid
    std::fill(st.c_group, st.c_group + kC, -1);
    struct GD { int g, d, cx, cy; };
    // Group centroids are static: computed once per body, not every decision (this loop was ~80% of encode fuel).
    static std::vector<int> gcx, gcy;
    if (gcx.size() != w.groups.size()) {
        gcx.assign(w.groups.size(), -1);
        gcy.assign(w.groups.size(), -1);
        for (std::size_t g = 0; g < w.groups.size(); ++g) {
            const auto& gr = w.groups[g];
            if (gr.camps.empty()) continue;
            long sx = 0, sy = 0;
            for (int ci : gr.camps) { sx += w.camps[ci].pos.x; sy += w.camps[ci].pos.y; }
            gcx[g] = static_cast<int>(sx / static_cast<long>(gr.camps.size()));
            gcy[g] = static_cast<int>(sy / static_cast<long>(gr.camps.size()));
        }
    }
    // Keep the 12 nearest in a sorted array (insertion), ties by group index: same order as a full sort.
    GD best[kC];
    int nb = 0;
    for (int g = 0; g < static_cast<int>(w.groups.size()); ++g) {
        if (gcx[g] < 0) continue;
        const GD cand{ g, cheb(px, py, gcx[g], gcy[g]), gcx[g], gcy[g] };
        if (nb == kC && cand.d >= best[kC - 1].d) continue;  // g increases, so a tie never beats an earlier group
        int k = nb < kC ? nb++ : kC - 1;
        while (k > 0 && best[k - 1].d > cand.d) {
            best[k] = best[k - 1];
            --k;
        }
        best[k] = cand;
    }
    for (int i = 0; i < nb; ++i) {
        const auto& gr = w.groups[best[i].g];
        std::int16_t* c = f + kOffC + i * kCW;
        st.c_group[i] = best[i].g;
        c[0] = 1;
        c[1] = q(best[i].cx - px);
        c[2] = q(best[i].cy - py);
        c[3] = q(static_cast<long>(gr.camps.size()));
        int types[6] = {}, dead = 0;
        float hp = 0, mx = 0;
        for (int ci : gr.camps) {
            const auto& cr = w.camps[ci];
            const int t = static_cast<int>(cr.type);
            if (t >= 0 && t < 6) ++types[t];
            dead += cr.dead ? 1 : 0;
            hp += cr.dead ? 0.0f : cr.hp;
            mx += cr.max_hp;
        }
        for (int t = 0; t < 6; ++t) c[4 + t] = q(types[t]);
        c[10] = q(static_cast<long>(gr.state)); // 0 alive, 1 reward waiting, 2 respawning (World's knowledge)
        c[11] = q(dead);
        c[12] = frac(hp, mx);
        c[13] = q(best[i].d);
        c[14] = age(now, gr.seen_round);
        c[15] = q(static_cast<long>(gr.gems));
    }

    // l: altars (lock state is not read yet: -1 = unknown)
    for (int i = 0; i < kL && i < static_cast<int>(w.altars.size()); ++i) {
        std::int16_t* l = f + kOffL + i * kLW;
        const auto& a = w.altars[i];
        l[0] = 1;
        l[1] = q(a.x - px);
        l[2] = q(a.y - py);
        l[3] = q(cheb(px, py, a.x, a.y));
        l[4] = -1;
        l[5] = -1;
        l[6] = -1;
        l[7] = q(cheb(px, py, a.x, a.y) <= static_cast<int>(bc::constants::submit_gems_range) ? 1 : 0);
    }
}

#if CLRL_REC  // recorder entry points (debug-only fuel refund API)
template <class BotT>
static void capture(const BotT& b) {
    using namespace clrl;
    debug_block({
        ::cambc::detail::sdk_fuel_adjust(CLRL_REFUND);
        try {
            encode(b);
            const auto& me = bc::self();
            st.x0 = b.pos.x;
            st.y0 = b.pos.y;
            st.gold0 = b.gold;
            st.wards0 = static_cast<int>(me.ward_positions().size());
            st.state0 = state_bits(me);
            st.cap_round = b.round;
            st.captured = true;
        } catch (...) {
            st.captured = false;
        }
    });
}

template <class BotT>
static void finish(const BotT& b) {
    using namespace clrl;
    debug_block({
        ::cambc::detail::sdk_fuel_adjust(CLRL_REFUND);
        try {
            const int now = static_cast<int>(bc::round_number());
            if (st.captured) {
                const auto& me = bc::self();
                const auto p = me.position();
                const std::uint32_t s1 = state_bits(me);
                int prim = 0;
                if (p.x != st.x0 || p.y != st.y0) prim |= 1;
                if ((st.state0 & (1u << 4)) && !(s1 & (1u << 4))) prim |= 2;
                if ((st.state0 & (1u << 5)) && !(s1 & (1u << 5))) prim |= 4;
                if (s1 & (1u << 7)) prim |= 8;
                if (s1 & (1u << 8)) prim |= 16;
                if (static_cast<int>(me.gold_count()) < st.gold0) prim |= 32;
                if (static_cast<int>(me.ward_positions().size()) > st.wards0) prim |= 64;
                int macro = kC;
                for (int i = 0; i < kC; ++i)
                    if (st.c_group[i] >= 0 && st.c_group[i] == b.target_group) macro = i;
                std::printf("CLR1 %d %d %u %d %d %d %d %d %s\n", st.cap_round, b.slot, b.my_id, macro, prim, p.x - st.x0,
                            p.y - st.y0, st.reset_next ? 1 : 0, b64(st.f, kNF).c_str());
                st.reset_next = false;
                st.last_round = st.cap_round;
            } else if (!bc::self().is_alive()) {
                st.reset_next = true; // dead: the next captured turn starts a new recurrent segment
            }
            st.captured = false;
            (void)now;
        } catch (...) {
            st.captured = false;
        }
    });
}
#endif
};
#endif
