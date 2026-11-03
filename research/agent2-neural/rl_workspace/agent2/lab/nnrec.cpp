// Neural bot recorder (A2_NNREC, agent2/lab/nn_mkrec.py): the entity features of a sampled turn, as the network will
// see them in the bot, and at the end of the turn v92's decisions and every SDK action it made (wrapped imports).
#include "bot.h"
#include "ladfit.h"
#if A2_NNREC || A2_NN
#include <algorithm>
#include <cstdio>
#include <string_view>

namespace {
constexpr int kG = 16, kS = 44, kA = 5, kAF = 12, kE = 8, kEF = 16, kC = 10, kCF = 22, kL = 4, kLF = 8;
constexpr int kNF = kG + kS + kA * kAF + kE * kEF + kC * kCF + kL * kLF; // 500
constexpr int kAF3 = 16, kC3 = 24;                                          // version 3: ally claims, 24 groups
constexpr int kNF3 = kG + kS + kA * kAF3 + kE * kEF + kC3 * kCF + kL * kLF; // 828
std::int16_t q(float v) { return static_cast<std::int16_t>(std::clamp(v, -32000.0f, 32000.0f)); }
[[maybe_unused]] std::string b64(const std::int16_t* p, int n) {
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
// Per-champion history (each champion is its own instance, so these are this champion's past), updated every turn.
struct Hist {
    static constexpr int kN = 32;
    int hp[kN] = {}, gems[kN] = {}, x[kN] = {}, y[kN] = {}, last = -1;
    int target = -9, target_since = 0, last_bank = -1000, last_contact = -1000, last_alive_gap = 0, prev_round = -1;
    int changes[8] = {}; // rounds of the last 8 target changes
    int nchg = 0;
    int banked_total = 0; // gems this champion banked (bag emptied without a death gap); RL return only, not a feature
    int gold_earned = 0, prev_gold = -1, deaths = 0; // RL return only: gold income, own deaths (respawn gaps)
} hist;
int hist_at(const int* a, int now, int ago) { return a[((now - ago) % Hist::kN + Hist::kN) % Hist::kN]; }
} // namespace

void Bot::nn_track() {
    Hist& h = hist;
    const int r = round;
    if (h.prev_round >= 0 && r - h.prev_round > 3) h.last_alive_gap = r, ++h.deaths; // came back from death
    if (h.prev_gold >= 0 && gold > h.prev_gold) h.gold_earned += gold - h.prev_gold; // income (shopping only lowers gold)
    h.prev_gold = gold;
#if A2_NN_MACRO
    count_enemy_deaths(); // team kills (all enemy handles, not only visible ones) for the RL return
#endif
    if (h.prev_round >= 0 && gems == 0 && h.gems[h.prev_round % Hist::kN] > 0) h.last_bank = r; // bag emptied: banked
    if (h.prev_round >= 0 && r - h.prev_round <= 3 && gems == 0 && h.gems[h.prev_round % Hist::kN] > 0)
        h.banked_total += h.gems[h.prev_round % Hist::kN]; // alive throughout: the bag went to an altar, not lost in a death
    for (int rr = h.prev_round + 1; rr <= r; ++rr) {
        const int i = ((rr % Hist::kN) + Hist::kN) % Hist::kN;
        h.hp[i] = static_cast<int>(hp), h.gems[i] = gems, h.x[i] = pos.x, h.y[i] = pos.y;
        if (h.prev_round < 0) break;
    }
    if (target_group != h.target) {
        h.target = target_group, h.target_since = r;
        h.changes[h.nchg++ % 8] = r;
    }
    if (nn_near() <= 6) h.last_contact = r;
    h.prev_round = r;
}

// The network features of this turn for NC camp groups and AF fields per ally: 10 / 12 = the 500-feature network,
// 24 / 16 = version 3 (more of the map, and each ally's claimed target from shared memory). `near` = Chebyshev distance
// to the nearest visible enemy.
template <int NC, int AF>
void Bot::nn_feats_t(std::int16_t* f, int near) {
    const bool fight = near <= 6;
    int k = 0;
    auto& me = bc::self();
    const auto st = me.state();
    // global (16)
    int alive_e = 0;
    for (const auto& e : w.enemies) alive_e += e.hp > 0;
    f[k + 0] = q(round);
    f[k + 1] = q(ally_score);
    f[k + 2] = q(enemy_score);
    f[k + 3] = q(static_cast<float>(bc::constants::winning_gems));
    f[k + 4] = q(team_size);
    f[k + 5] = q(slot);
    f[k + 6] = q(w.width);
    f[k + 7] = q(w.height);
    f[k + 8] = q(static_cast<float>(w.groups.size()));
    f[k + 9] = q(static_cast<float>(w.allies.size()));
    f[k + 10] = q(alive_e);
    f[k + 11] = q(static_cast<float>(w.sightings.size()));
    f[k + 12] = q(is_official_map() ? 1 : 0);
    if constexpr (NC == kC3) {
        // version 3: which official ladder map this is (v92's ladfit fingerprint: width, height, camp groups, total group
        // gems; 1-70, 0 = not a ladder map) - v92 plays a per-map tuned correction on each of them, the network can learn
        // per-map play too (the ladder only uses these maps)
        static int lad = -2;
        if (lad == -2) {
            lad = -1;
            unsigned total = 0;
            for (const auto& g : w.groups) total += g.gems;
            for (int m = 0; m < 70; ++m) {
                const auto& fp = ladfit::kFp[m];
                if (fp.w == w.width && fp.h == w.height && fp.groups == static_cast<int>(w.groups.size()) && fp.gems == total) lad = m;
            }
        }
        f[k + 13] = q(lad + 1);
    } else {
        f[k + 13] = q(target_group);
    }
    f[k + 14] = q(fight ? 1 : 0);
    f[k + 15] = q(near);
    k += kG;
    // self (32)
    f[k + 0] = q(static_cast<float>(static_cast<int>(type)));
    f[k + 1] = q(hp);
    f[k + 2] = q(max_hp);
    f[k + 3] = q(strength * 10.0f);
    f[k + 4] = q(focus * 10.0f);
    f[k + 5] = q(range);
    f[k + 6] = q(gems);
    f[k + 7] = q(gold);
    for (int s = 0; s < 2; ++s) {
        f[k + 8 + 5 * s] = q(spells[s].present ? 1 : 0);
        f[k + 9 + 5 * s] = q(static_cast<float>(static_cast<int>(spells[s].kind)));
        f[k + 10 + 5 * s] = q(spells[s].range * 10.0f);
        f[k + 11 + 5 * s] = q(cooldown[s]);
        f[k + 12 + 5 * s] = q(spell_ready(s) ? 1 : 0);
    }
    f[k + 18] = q(pos.x);
    f[k + 19] = q(pos.y);
    f[k + 20] = q(fdist(w.spawn_field, pos));
    f[k + 21] = q(w.altar_ready ? fdist(w.altar_field, pos) : -1);
    f[k + 22] = q(bit(w.bushes, pos) ? 1 : 0);
    f[k + 23] = q(bit(w.hot_zone, pos) ? 1 : 0);
    f[k + 24] = q(st.contains(bc::champion_state::recalling) ? 1 : 0);
    f[k + 25] = q(st.contains(bc::champion_state::submitting_gems) ? 1 : 0);
    f[k + 26] = q(prev_hp);
    f[k + 27] = q(me.can_attack() ? 1 : 0);
    f[k + 28] = q(bit(w.ally_spawn, pos) ? 1 : 0);
    f[k + 29] = q(heading_home ? 1 : 0);
    f[k + 30] = q(melee ? 1 : 0);
    f[k + 31] = q(static_cast<float>(my_id));
    {
        // history (32-43): commitment, health / bag / movement trends, time since bank, contact and respawn
        const Hist& h = hist;
        int chg50 = 0;
        for (int c = 0; c < 8; ++c) chg50 += h.changes[c] > 0 && round - h.changes[c] <= 50;
        f[k + 32] = q(std::min(999, round - h.target_since));
        f[k + 33] = q(chg50);
        f[k + 34] = q(hist_at(h.hp, round, 5));
        f[k + 35] = q(hist_at(h.hp, round, 20));
        f[k + 36] = q(pos.x - hist_at(h.x, round, 10));
        f[k + 37] = q(pos.y - hist_at(h.y, round, 10));
        f[k + 38] = q(hist_at(h.gems, round, 20));
        f[k + 39] = q(std::min(999, round - h.last_bank));
        f[k + 40] = q(std::min(999, round - h.last_contact));
        f[k + 41] = q(std::min(999, round - h.last_alive_gap));
        f[k + 42] = q(round < 32 ? round : 32);
        f[k + 43] = q(target_group >= 0 ? 1 : 0);
    }
    k += kS;
    // allies (5 x AF), nearest first
    std::vector<const AllyRec*> al;
    for (const auto& a : w.allies) al.push_back(&a);
    std::sort(al.begin(), al.end(), [&](auto* a, auto* b) { return cheb(a->pos, pos) < cheb(b->pos, pos); });
    for (int i = 0; i < kA; ++i, k += AF) {
        if (i >= static_cast<int>(al.size())) continue;
        const auto& a = *al[static_cast<std::size_t>(i)];
        f[k + 0] = 1;
        f[k + 1] = q(static_cast<float>(static_cast<int>(a.type)));
        f[k + 2] = q(a.pos.x - pos.x);
        f[k + 3] = q(a.pos.y - pos.y);
        f[k + 4] = q(a.hp);
        f[k + 5] = q(a.max_hp);
        f[k + 6] = q(a.strength * 10.0f);
        f[k + 7] = q(a.focus * 10.0f);
        f[k + 8] = q(a.range);
        f[k + 9] = q(cheb(a.pos, pos));
        f[k + 10] = q(static_cast<float>(static_cast<std::uint32_t>(static_cast<bc::handle_champion_t>(a.unit))));
        f[k + 11] = q(fdist(w.spawn_field, a.pos));
        if constexpr (AF >= 16) {
            // where this ally is heading: its claim slot in shared memory (v92's claims) -> claimed group's centre
            int cs = -1;
            for (int s2 = 0; s2 < std::min(team_size, kClaimSlots); ++s2)
                if (ally_handle[static_cast<std::size_t>(s2)] == a.id) cs = s2;
            const int cg = cs >= 0 ? claim_of(cs) : -1;
            if (cg >= 0 && cg < static_cast<int>(w.groups.size()) && !w.groups[static_cast<std::size_t>(cg)].camps.empty()) {
                int sx = 0, sy = 0, n = 0;
                for (int ci : w.groups[static_cast<std::size_t>(cg)].camps)
                    sx += w.camps[static_cast<std::size_t>(ci)].pos.x, sy += w.camps[static_cast<std::size_t>(ci)].pos.y, ++n;
                f[k + 12] = 1;
                f[k + 13] = q((sx + n / 2) / n - pos.x);
                f[k + 14] = q((sy + n / 2) / n - pos.y);
                f[k + 15] = q(cg == target_group ? 1 : 0);
            }
        }
    }
    // enemies (8 x 16): visible first (nearest first), then recent sightings not matching a visible enemy
    std::vector<const EnemyRec*> en;
    for (const auto& e : w.enemies)
        if (e.hp > 0) en.push_back(&e);
    std::sort(en.begin(), en.end(), [&](auto* a, auto* b) { return cheb(a->pos, pos) < cheb(b->pos, pos); });
    int ei = 0;
    for (; ei < kE && ei < static_cast<int>(en.size()); ++ei, k += kEF) {
        const auto& e = *en[static_cast<std::size_t>(ei)];
        f[k + 0] = 1;
        f[k + 1] = q(static_cast<float>(static_cast<int>(e.type)));
        f[k + 2] = q(e.pos.x - pos.x);
        f[k + 3] = q(e.pos.y - pos.y);
        f[k + 4] = q(e.hp);
        f[k + 5] = q(e.max_hp);
        f[k + 6] = q(e.strength * 10.0f);
        f[k + 7] = q(e.focus * 10.0f);
        f[k + 8] = q(e.range);
        f[k + 9] = q(e.gems);
        f[k + 10] = q(e.tributing() ? 1 : 0);
        f[k + 11] = q(e.recalling() ? 1 : 0);
        f[k + 12] = q(cheb(e.pos, pos));
        f[k + 13] = 0; // sighting age
        f[k + 14] = q(static_cast<float>(static_cast<std::uint32_t>(static_cast<bc::handle_champion_t>(e.unit))));
        f[k + 15] = q(fdist(w.spawn_field, e.pos));
    }
    std::vector<Sighting> sg(w.sightings.begin(), w.sightings.end());
    std::sort(sg.begin(), sg.end(), [](const Sighting& a, const Sighting& b) { return a.round > b.round; });
    for (const auto& s : sg) {
        if (ei >= kE || round - s.round > 30) break;
        bool seen = false;
        for (auto* e : en) seen |= cheb(e->pos, s.pos) <= 2;
        if (seen) continue;
        f[k + 0] = 2;
        f[k + 2] = q(s.pos.x - pos.x);
        f[k + 3] = q(s.pos.y - pos.y);
        f[k + 12] = q(cheb(s.pos, pos));
        f[k + 13] = q(round - s.round);
        f[k + 15] = q(fdist(w.spawn_field, s.pos));
        ++ei, k += kEF;
    }
    k += (kE - ei) * kEF;
    // camp groups (10 x 20), nearest by walking distance first. Map analysis (the user's first-turn idea): every group's
    // distance field, the enemy field (side margins) and the altar field are built on the first turns (fuel ignored).
#if A2_NN_FAST
    // real fuel: build the remaining group fields only while fuel is to spare (keeps 50k for the turn); unbuilt groups
    // fall back to straight-line distance (wd = -1)
    while (!w.fields_ready() && bc::fuel_remaining() > 110000 && w.build_next_group_field(bc::fuel_remaining() - 100000)) {
    }
#else
    if (!w.fields_ready())
        for (int it = 0; it < 64 && w.build_next_group_field(4000000); ++it) {
        }
#endif
    w.ensure_enemy_field();
    w.ensure_altar_field();
    struct GC { int gi; vec2 c; int d, wd; };
    std::vector<GC> gc;
    for (std::size_t gi = 0; gi < w.groups.size(); ++gi) {
        const auto& g = w.groups[gi];
        int sx = 0, sy = 0, n = 0;
        for (int ci : g.camps) sx += w.camps[static_cast<std::size_t>(ci)].pos.x, sy += w.camps[static_cast<std::size_t>(ci)].pos.y, ++n;
        if (!n) continue;
        const vec2 c{(sx + n / 2) / n, (sy + n / 2) / n};
        int wd = -1;
        if (w.has_field(static_cast<int>(gi))) {
            const int d = w.group_distance(static_cast<int>(gi), pos);
            wd = d >= kUnreach ? -1 : d;
        }
        gc.push_back({static_cast<int>(gi), c, cheb(c, pos), wd});
    }
    // walking distance when known (unknown / unreachable after every known one), then straight-line distance
    std::sort(gc.begin(), gc.end(), [](const GC& a, const GC& b) {
        const int ka = a.wd < 0 ? 100000 + a.d : a.wd, kb = b.wd < 0 ? 100000 + b.d : b.wd;
        return ka < kb;
    });
    for (int i = 0; i < NC; ++i, k += kCF) {
        if (i >= static_cast<int>(gc.size())) continue;
        const auto& g = w.groups[static_cast<std::size_t>(gc[static_cast<std::size_t>(i)].gi)];
        const vec2 c = gc[static_cast<std::size_t>(i)].c;
        f[k + 0] = 1;
        f[k + 1] = q(gc[static_cast<std::size_t>(i)].gi);
        f[k + 2] = q(c.x - pos.x);
        f[k + 3] = q(c.y - pos.y);
        f[k + 4] = q(gc[static_cast<std::size_t>(i)].d);
        f[k + 5] = q(g.gems);
        f[k + 6] = q(g.gold);
        f[k + 7] = q(static_cast<float>(static_cast<int>(g.state)));
        f[k + 8] = q(g.state == GroupState::respawning ? g.respawn_round - round : 0);
        f[k + 9] = q(g.hp_left(w.camps));
        f[k + 10] = q(g.max_hp);
        f[k + 11] = q(g.strength * 10.0f);
        f[k + 12] = q(g.harmless ? 1 : 0);
        f[k + 13] = q(std::min(999, round - g.enemy_round));
        f[k + 14] = q(claim_count(gc[static_cast<std::size_t>(i)].gi));
        f[k + 15] = q(allies_near_group(g));
        const int gi2 = gc[static_cast<std::size_t>(i)].gi;
        f[k + 16] = q(gc[static_cast<std::size_t>(i)].wd);
        f[k + 17] = q(w.enemy_ready && gi2 < static_cast<int>(w.group_margin.size()) ? w.group_margin[static_cast<std::size_t>(gi2)] : 0);
        // fields read at the centre's nearest walkable neighbour (camp tiles block some fields)
        auto near_d = [&](const bc::distance_field& fld) {
            int best = kUnreach;
            for (int dy = -1; dy <= 1; ++dy)
                for (int dx = -1; dx <= 1; ++dx) {
                    const vec2 qq{c.x + dx, c.y + dy};
                    if (qq.x >= 0 && qq.y >= 0 && qq.x < w.width && qq.y < w.height) best = std::min<int>(best, fdist(fld, qq) + ((dx || dy) ? 1 : 0));
                }
            return std::min(best, 999);
        };
        f[k + 18] = q(w.altar_ready ? near_d(w.altar_field) : -1);
        f[k + 19] = q(near_d(w.spawn_field));
        // allies that reach this group before us (walking), the team's coverage of it
        int closer = 0;
        if (w.has_field(gi2)) {
            const int mine = w.group_distance(gi2, pos);
            for (const auto& a : w.allies) closer += a.hp > 0 && w.group_distance(gi2, a.pos) < mine;
        }
        f[k + 20] = q(closer);
        f[k + 21] = q(gi2 == target_group ? 1 : 0); // our current (committed) target
    }
    // altars (4 x 8), nearest first
    std::vector<vec2> alt(w.altars.begin(), w.altars.end());
    std::sort(alt.begin(), alt.end(), [&](vec2 a, vec2 b) { return cheb(a, pos) < cheb(b, pos); });
    for (int i = 0; i < kL; ++i, k += kLF) {
        if (i >= static_cast<int>(alt.size())) continue;
        const vec2 a = alt[static_cast<std::size_t>(i)];
        int en4 = 0, al4 = 0;
        for (auto* e : en) en4 += cheb(e->pos, a) <= 4;
        for (auto* x : al) al4 += cheb(x->pos, a) <= 4;
        f[k + 0] = 1;
        f[k + 1] = q(a.x - pos.x);
        f[k + 2] = q(a.y - pos.y);
        f[k + 3] = q(cheb(a, pos));
        f[k + 4] = q(en4);
        f[k + 5] = q(al4);
        f[k + 6] = q(fdist(w.spawn_field, a));
        f[k + 7] = q(a.x * 128 + a.y);
    }
}

void Bot::nn_feats(std::int16_t* f, int near) { nn_feats_t<kC, kAF>(f, near); }
void Bot::nn_feats3(std::int16_t* f, int near) { nn_feats_t<kC3, kAF3>(f, near); }

int Bot::nn_near() const {
    int near = 99;
    for (const auto& e : w.enemies)
        if (e.hp > 0) near = std::min(near, cheb(e.pos, pos));
    return near;
}

#if A2_NNREC
void Bot::nnrec_begin() {
    if (!inited) return;
    nn_track();
    const int near = nn_near();
    const bool fight = near <= 6;
    if ((round + slot) % A2_NNREC != 0 && !(fight && round % 2 == 0)) return;
    if (!nnrec_camps_done) {
        // camp handle -> group index, once per champion (attack targets on camps map to groups offline)
        nnrec_camps_done = true;
        std::string s = "NRC " + std::to_string(slot);
        for (std::size_t ci = 0; ci < w.camps.size() && ci < w.camp_group.size(); ++ci)
            s += " " + std::to_string(static_cast<std::uint32_t>(static_cast<bc::handle_camp_t>(w.camps[ci].camp))) + ":" + std::to_string(w.camp_group[ci]);
        std::printf("%s\n", s.c_str());
    }
#if A2_NNREC_LAYOUT == 3
    constexpr int kNFr = kNF3; // version-3 features logged (the acting network may still use the 500-feature layout)
    std::int16_t f[kNFr] = {};
    nn_feats3(f, near);
#else
    constexpr int kNFr = kNF;
    std::int16_t f[kNFr] = {};
    nn_feats(f, near);
#endif
    char head[48];
    std::snprintf(head, sizeof head, "NR %d %d %d ", round, slot, fight ? 1 : 0);
    nnrec_line = head + b64(f, kNFr);
}

void Bot::nnrec_end() {
    if (nnrec_line.empty()) return;
#if (A2_NN & 1) && A2_NNREC_LAYOUT != 3 // version-3 recording imitates the executed (network) choice, not v92's
    const int label_group = nn_v92best; // DAgger: v92's choice in the state the network led us to
#else
    const int label_group = target_group;
#endif
    std::printf("%s %s %d %d | %s\n", nnrec_line.c_str(), (mode && *mode) ? mode : "-", label_group, heading_home ? 1 : 0,
                nnrec::acts.c_str());
}
#endif

#if A2_NN
#include "nn_infer.h"
// Neural bot (A2_NN bits: 1 the student picks the farming target group, 2 it decides when to bank).
void Bot::nn_decide() {
    nn_group = -1, nn_beh = -1;
    nn_v92best = target_group; // v92 keeps its target unless farm() chooses again
    if (!inited) return;
    nn_track();
#if A2_NN_FAST && !defined(A2_NN_RL)
    // deployment: in contact v92's fight code decides and needs the fuel - no network this turn
    if (nn_near() <= 6) return;
#endif
#if A2_NN_LAYOUT == 3
    constexpr int kNFa = kNF3, NCt = kC3, kCOff = kG + kS + kA * kAF3 + kE * kEF; // the acting network's layout
#else
    constexpr int kNFa = kNF, NCt = kC, kCOff = kG + kS + kA * kAF + kE * kEF;
#endif
    std::int16_t f[kNFa] = {};
#ifdef A2_NN_FUEL
    const std::uint64_t f0 = bc::fuel_remaining();
#endif
#if A2_NN_LAYOUT == 3
    nn_feats3(f, nn_near());
#else
    nn_feats(f, nn_near());
#endif
#ifdef A2_NN_FUEL
    const std::uint64_t f1 = bc::fuel_remaining();
#endif
    nn::Out o;
#if A2_NN_FAST
    nn::forward(f, o, nn::kHBeh | nn::kHTarget | nn::kHOption); // only the heads the bot reads
#else
    nn::forward(f, o);
#endif
#ifdef A2_NN_FUEL
    {
        static std::uint64_t sf = 0, sn = 0, cnt = 0;
        sf += f0 - f1, sn += f1 - bc::fuel_remaining(), ++cnt;
        if (cnt % 200 == 0) std::printf("NNFUEL feats %llu net %llu per turn (budget %llu)\n", static_cast<unsigned long long>(sf / cnt),
                                        static_cast<unsigned long long>(sn / cnt), static_cast<unsigned long long>(f0));
    }
#endif
    nn_beh = nn::argmax(o.behaviour);
    int t = nn::argmax(o.target);
#if A2_NN_MACRO
    {
        // Macro policy (A2_NN_MACRO): the behaviour head picks an option, held until it completes; the target head
        // picks the farming group. Sampled at temperature A2_NN_RL_T in RL rollouts (A2_NN_RL), argmax otherwise.
        // Options in contact (enemy within 6): 2 fight, 3 flee (held 3 rounds), anything else = v92's own verdict.
        // Out of contact: 0 farm, 1 bank (until the bag is empty, <= 25), 2 hunt (10), 3 / 4 home (until at spawn,
        // <= 20), 6 regroup (until within 2 of an ally, <= 8), 5 / 7 v92's own choice (nn_option_out in nnrec.cpp).
        const bool contact = nn_near() <= 6;
        static std::uint64_t rs = 0x9E3779B97F4A7C15ull;
        if (rs == 0x9E3779B97F4A7C15ull) rs ^= (static_cast<std::uint64_t>(my_id) << 32) ^ static_cast<std::uint64_t>(round * 7919 + slot);
        auto pick = [&](const float* lg, int n, float& lp) {
#ifdef A2_NN_RL
            const float temp = static_cast<float>(A2_NN_RL_T);
            float mx = -1e30f, z = 0.0f, p[32];
            for (int i = 0; i < n; ++i) mx = std::max(mx, lg[i] / temp);
            for (int i = 0; i < n; ++i) z += (p[i] = std::exp(lg[i] / temp - mx));
            rs ^= rs << 13, rs ^= rs >> 7, rs ^= rs << 17;
            float u = static_cast<float>(rs >> 40) / static_cast<float>(1ull << 24) * z;
            int a = n - 1;
            for (int i = 0; i < n; ++i)
                if ((u -= p[i]) <= 0.0f) { a = i; break; }
            lp = std::log(std::max(p[a] / z, 1e-12f));
            return a;
#else
            lp = 0.0f;
            return static_cast<int>(std::max_element(lg, lg + n) - lg);
#endif
        };
        // Option head (RL-only residual, out of contact): 1 hunt (held 10), 2 home (until at spawn, <= 20), 3 regroup
        // (until within 2 of an ally, <= 8), 4 bank now (until the bag is empty, <= 25); 0 none = v92's chain with the
        // imitation heads (banking = the behaviour head's argmax at v92's tribute step), so a fresh head is the best bot.
        bool release = round >= nn_hold_until || contact;
        if (!release) {
            if (nn_hold_beh == 2) release = bit(w.ally_spawn, pos);
            else if (nn_hold_beh == 4) release = gems == 0;
            else if (nn_hold_beh == 3) {
                int d = 99;
                for (const auto& a : w.allies) if (a.hp > 0) d = std::min(d, cheb(a.pos, pos));
                release = d <= 2;
            }
        }
        nn_rl_beh_a = -1;
        if (contact) {
            nn_hold_beh = 0, nn_hold_until = -1;
        } else if (release) {
#if defined(A2_NN_RL) && defined(A2_NN_OPT_T)
            const float otemp = static_cast<float>(A2_NN_OPT_T);
#else
            const float otemp = 1.0f;
#endif
            float pr[5], omx = -1e30f, oz = 0.0f;
            for (int i = 0; i < 5; ++i) omx = std::max(omx, o.option[i] / otemp);
            for (int i = 0; i < 5; ++i) oz += (pr[i] = std::exp(o.option[i] / otemp - omx));
#ifdef A2_NN_RL
            rs ^= rs << 13, rs ^= rs >> 7, rs ^= rs << 17;
            float u = static_cast<float>(rs >> 40) / static_cast<float>(1ull << 24) * oz;
            int b = 4;
            for (int i = 0; i < 5; ++i)
                if ((u -= pr[i]) <= 0.0f) { b = i; break; }
#else
            const int b = static_cast<int>(std::max_element(pr, pr + 5) - pr);
#endif
            nn_rl_beh_a = b, nn_rl_beh_lp = std::log(std::max(pr[b] / oz, 1e-12f));
            const int hold = b == 1 ? 10 : b == 2 ? 20 : b == 3 ? 8 : b == 4 ? 25 : 0;
            nn_hold_beh = b, nn_hold_until = round + hold, nn_hold_contact = false;
        }
        nn_beh = nn::argmax(o.behaviour); // the banking gate, exactly as in the best target + bank bot
        float lpt = 0.0f;
        t = pick(o.target, NCt + 1, lpt);
        nn_rl_a = t, nn_rl_lp = lpt;
        nn_rl_contact = contact;
        nn_rl_val = hist.banked_total + gems;
        nn_rl_gold = hist.gold_earned, nn_rl_kills = enemy_deaths, nn_rl_deaths = hist.deaths;
        nn_rl_tgt_applied = false, nn_rl_chg = false;
#ifdef A2_NN_RL
        nn_rl_feat = b64(f, kNFa);
#endif
    }
#elif defined(A2_NN_HYST)
    // commitment: keep the current target group unless another scores A2_NN_HYST logits higher
    for (int c = 0; c < NCt; ++c)
        if (f[kCOff + c * kCF] == 1 && f[kCOff + c * kCF + 1] == target_group && o.target[t] < o.target[c] + A2_NN_HYST) t = c;
#endif
#if defined(A2_NN_RL) && !A2_NN_MACRO
    {
        // RL rollouts: sample the target from softmax(logits / A2_NN_RL_T) and log the state, action and its
        // log-probability (every A2_NN_RL-th turn of each champion, plus every turn the target changes)
        static std::uint64_t rs = 0x9E3779B97F4A7C15ull;
        if (rs == 0x9E3779B97F4A7C15ull) rs ^= (static_cast<std::uint64_t>(my_id) << 32) ^ static_cast<std::uint64_t>(round * 7919 + slot);
        rs ^= rs << 13, rs ^= rs >> 7, rs ^= rs << 17;
        const float temp = static_cast<float>(A2_NN_RL_T);
        float mx = -1e30f, z = 0.0f, p[NCt + 1];
        for (int i = 0; i < NCt + 1; ++i) mx = std::max(mx, o.target[i] / temp);
        for (int i = 0; i < NCt + 1; ++i) z += (p[i] = std::exp(o.target[i] / temp - mx));
        float u = static_cast<float>(rs >> 40) / static_cast<float>(1ull << 24) * z;
        int a = NCt;
        for (int i = 0; i < NCt + 1; ++i) {
            if ((u -= p[i]) <= 0.0f) { a = i; break; }
        }
        t = a;
        // logged by farm() only when the choice is applied (nn_mkbot.py): turns spent fighting / banking are not decisions
        nn_rl_a = a;
        nn_rl_lp = std::log(std::max(p[a] / z, 1e-12f));
        nn_rl_val = hist.banked_total + gems; // this champion's own value: banked by it so far + carried
        nn_rl_feat = b64(f, kNFa);
    }
#endif
    if (t < NCt && f[kCOff + t * kCF] == 1) nn_group = f[kCOff + t * kCF + 1];
#ifdef A2_NN_DBG
    if (round % 25 == 0)
        std::printf("NND %s %.5f %.5f %.5f %.5f %.5f\n", b64(f, kNFa).c_str(), o.behaviour[0], o.behaviour[1], o.target[0],
                    o.attack[18], o.cast_tgt[24]);
#endif
}

#if A2_NN_MACRO
// Out-of-contact options of the option head (called in play_turn's dispatch after the win-now bank; false = v92's own
// chain decides this turn).
bool Bot::nn_option_out() {
    switch (nn_hold_beh) {
    case 1: // hunt
        return hunt();
    case 2: // home
        if (go_home_if_needed()) return true;
        if (!bit(w.ally_spawn, pos)) {
            heading_home = true;
            mode = "nn-home";
            walk_toward(w.ally_spawn);
            return true;
        }
        return false;
    case 3: { // regroup with the nearest living ally
        int best = 99;
        vec2 at{};
        for (const auto& a : w.allies)
            if (a.hp > 0 && cheb(a.pos, pos) < best) best = cheb(a.pos, pos), at = a.pos;
        if (best < 99 && best > 2) {
            bc::bitboard goal;
            goal.clear();
            set_bit(goal, at);
            mode = "nn-regroup";
            walk_toward(goal);
            return true;
        }
        return false;
    }
    case 4: // bank now
        if (gems > 0) {
            force_tribute = true;
            if (tribute_if_needed()) {
                mode = "nn-bank";
                return true;
            }
            force_tribute = false;
        }
        return false;
    default: // 0 none: v92's chain decides
        return false;
    }
}

#ifdef A2_NN_RL
// End of turn (main.cpp): one row per turn with a decision - a new option and / or an applied target choice:
// NRB round slot contact beh_a beh_lp tgt_a tgt_lp target_changed own_value gold_earned team_kills own_deaths features
void Bot::nn_rl_end() {
    if (nn_rl_feat.empty()) return;
    if (nn_rl_beh_a >= 0 || nn_rl_tgt_applied)
        std::printf("NRB %d %d %d %d %.5f %d %.5f %d %d %d %d %d %s\n", round, slot, nn_rl_contact ? 1 : 0, nn_rl_beh_a, nn_rl_beh_lp,
                    nn_rl_tgt_applied ? nn_rl_a : -1, nn_rl_lp, nn_rl_chg ? 1 : 0, nn_rl_val, nn_rl_gold, nn_rl_kills, nn_rl_deaths,
                    nn_rl_feat.c_str());
    nn_rl_feat.clear();
}
#endif
#endif
#endif
#endif
