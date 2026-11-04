// Neural bot recorder (A2_NNREC, agent2/lab/nn_mkrec.py): the entity features of a sampled turn, as the network will
// see them in the bot, and at the end of the turn v92's decisions and every SDK action it made (wrapped imports).
#include "bot.h"
#include "ladfit.h"
#if A2_NNREC || A2_NN
#include <algorithm>
#include <cstdio>
#include <string_view>
#include <type_traits>

namespace {
#ifndef A2_NN_XF
#define A2_NN_XF 0 // E123: 6 more global fields (exact deaths, respawn countdown) and 5 more camp fields (draft-turn analysis)
#endif
constexpr int kG = A2_NN_XF ? 22 : 16, kS = 44, kA = 5, kAF = 12, kE = 8, kEF = 16, kC = 10, kCF = A2_NN_XF ? 27 : 22, kL = 4, kLF = 8;
constexpr int kNF = kG + kS + kA * kAF + kE * kEF + kC * kCF + kL * kLF; // 500 (A2_NN_XF: 556)
constexpr int kAF3 = 16, kC3 = 24;                                          // version 3: ally claims, 24 groups
constexpr int kNF3 = kG + kS + kA * kAF3 + kE * kEF + kC3 * kCF + kL * kLF; // 828
std::int16_t q(float v) { return static_cast<std::int16_t>(std::clamp(v, -32000.0f, 32000.0f)); }
template <class T, std::enable_if_t<std::is_integral_v<T>, int> = 0>
std::int16_t q(T v) {
    const int i = static_cast<int>(v);
    return static_cast<std::int16_t>(i < -32000 ? -32000 : i > 32000 ? 32000 : i);
}
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
#if A2_NN_XF
// E123: inputs the student's weights start at zero on, for RL to learn. The draft turn's analysis (nn_mkbot.py writes it to draft memory
// on the first draft turn's 10M fuel): per group the team plan's steps, value per round of a round trip from our spawn, and the gems around the group.
constexpr int kXOff = 200, kXMax = 96;
struct XFDraft {
    bool loaded = false;
    std::uint8_t vpt[kXMax] = {}, nbr[kXMax] = {}, team[kXMax] = {}, order[kXMax] = {};
    std::int16_t start[kXMax] = {};
} xfd;
void xf_load(int my_slot) {
    xfd.loaded = true;
    try {
        const auto& mem = bc::draft_memory;
        const auto u8 = [&](std::size_t i) { return static_cast<int>(static_cast<std::uint8_t>(mem[i])); };
        if (mem.size() > 10 && u8(8) == 'P') {
            const int slots = u8(9);
            std::size_t at = 10;
            for (int k = 0; k < slots && at < mem.size(); ++k) {
                const int n = u8(at++);
                for (int s = 0; s < n && at + 1 < mem.size(); ++s, at += 2) {
                    const int g = u8(at);
                    if (g >= kXMax) continue;
                    if (xfd.team[g] < 255) ++xfd.team[g];
                    if (k == my_slot && !xfd.order[g]) xfd.order[g] = static_cast<std::uint8_t>(s + 1), xfd.start[g] = static_cast<std::int16_t>(2 * u8(at + 1));
                }
            }
        }
        if (mem.size() > static_cast<std::size_t>(kXOff + 2 + 2 * kXMax) && u8(kXOff) == 'X') {
            const int n = std::min(u8(kXOff + 1), kXMax);
            for (int i = 0; i < n; ++i) {
                xfd.vpt[i] = static_cast<std::uint8_t>(u8(static_cast<std::size_t>(kXOff + 2 + i)));
                xfd.nbr[i] = static_cast<std::uint8_t>(u8(static_cast<std::size_t>(kXOff + 2 + kXMax + i)));
            }
        }
    } catch (...) {
    }
}
// Exact deaths: the API's is-alive query works for any champion, without vision. Rounds until each returns, counted from when we saw it dead.
struct XFDeaths {
    std::vector<std::uint32_t> h;
    std::vector<int> died;
    int dead = 0, next = 0, sum = 0;
    void update(team side, int r) {
        if (h.empty()) {
            for (const auto& c : bc::champions(side)) h.push_back(static_cast<std::uint32_t>(static_cast<bc::handle_champion_t>(c)));
            died.assign(h.size(), -1);
        }
        dead = next = sum = 0;
        for (std::size_t i = 0; i < h.size(); ++i) {
            std::int32_t alive = 1;
            if (cambc::detail::sdk_champion_is_alive(h[i], &alive) != 0) continue;
            if (alive) {
                died[i] = -1;
                continue;
            }
            if (died[i] < 0) died[i] = r;
            const int left = std::max(0, died[i] + static_cast<int>(bc::constants::respawn_time) - r);
            ++dead, sum += left, next = dead == 1 ? left : std::min(next, left);
        }
    }
} xfe, xfa;
#endif
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

#ifdef A2_NN_PROF
// feature fuel profile (A2_NN_PROF, E120): mean fuel per feature build of each section, printed every 200 builds
static void nn_fprof(int stage) {
    static std::uint64_t last = 0, sum[8] = {}, calls = 0;
    const std::uint64_t now = bc::fuel_remaining();
    if (stage > 0) sum[stage] += last - now;
    else ++calls;
    last = bc::fuel_remaining();
    if (stage == 7 && calls % 200 == 0) {
        auto m = [&](int s) { return static_cast<unsigned long long>(sum[s] / calls); };
        std::printf("NNFPROF glob %llu self %llu ally %llu enemy %llu fields %llu camp %llu altar %llu\n", m(1), m(2), m(3), m(4),
                    m(5), m(6), m(7));
    }
}
#define NN_FPROF(s) nn_fprof(s)
#else
#define NN_FPROF(s)
#endif

// The network features of this turn for NC camp groups and AF fields per ally: 10 / 12 = the 500-feature network,
// 24 / 16 = version 3 (more of the map, and each ally's claimed target from shared memory). `near` = Chebyshev distance
// to the nearest visible enemy.
template <int NC, int AF>
void Bot::nn_feats_t(std::int16_t* f, int near, int parts) {
    const bool fight = near <= 6;
    int k = 0;
    auto& me = bc::self();
    const auto st = me.state();
    NN_FPROF(0);
    std::vector<const AllyRec*> al;
    std::vector<const EnemyRec*> en;
    if (parts & 9) {
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
#if A2_NN_XF
    xfe.update(team::enemy, round), xfa.update(team::ally, round);
    f[k + 16] = q(static_cast<float>(xfe.h.size()) - static_cast<float>(xfe.dead)); // enemies alive, wherever they are
    f[k + 17] = q(xfe.dead);
    f[k + 18] = q(xfe.next); // rounds until the next dead enemy returns
    f[k + 19] = q(xfe.sum);  // enemy champion-rounds still to sit out
    f[k + 20] = q(xfa.dead);
    f[k + 21] = q(xfa.next);
#endif
    }
    k = kG;
    NN_FPROF(1);
    if (parts & 5) {
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
    }
    k = kG + kS;
    NN_FPROF(2);
    // allies (5 x AF), nearest first
    if (parts & 81) {
    for (const auto& a : w.allies) al.push_back(&a);
    std::sort(al.begin(), al.end(), [&](auto* a, auto* b) { return cheb(a->pos, pos) < cheb(b->pos, pos); });
    }
    if (parts & 17)
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
    k = kG + kS + kA * AF;
    NN_FPROF(3);
    // enemies (8 x 16): visible first (nearest first), then recent sightings not matching a visible enemy
    if (parts & 97) {
    for (const auto& e : w.enemies)
        if (e.hp > 0) en.push_back(&e);
    std::sort(en.begin(), en.end(), [&](auto* a, auto* b) { return cheb(a->pos, pos) < cheb(b->pos, pos); });
    }
    if (parts & 33) {
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
    }
    k = kG + kS + kA * AF + kE * kEF;
    NN_FPROF(4);
    if (parts & 2) {
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
#if !A2_NN_FAST
    w.ensure_enemy_field();
    w.ensure_altar_field();
#endif
    // (A2_NN_FAST: v92 builds these one-time fields on its own fuel schedule; until then the features read "not ready")
    NN_FPROF(5);
    // fields read at a group centre's nearest walkable neighbour (camp tiles block some fields)
    auto near_d = [&](const bc::distance_field& fld, vec2 c) {
        int best = kUnreach;
        for (int dy = -1; dy <= 1; ++dy)
            for (int dx = -1; dx <= 1; ++dx) {
                const vec2 qq{c.x + dx, c.y + dy};
                if (qq.x >= 0 && qq.y >= 0 && qq.x < w.width && qq.y < w.height) best = std::min<int>(best, fdist(fld, qq) + ((dx || dy) ? 1 : 0));
            }
        return std::min(best, 999);
    };
    // per-group constants (E120 fuel fit, the first-turn map analysis): centre, camp count, spawn-field and altar-field
    // value at the centre; computed once per group (the altar value once the altar field exists), same values as before
    struct GStat { vec2 c; int n, spn, alt, rad; };
    static std::vector<GStat> gst;
    static bool gst_bridges = false; // the spawn / altar fields are rebuilt once when bridges turn on: recompute then
    if (gst.size() != w.groups.size() || gst_bridges != w.bridges_on) {
        gst_bridges = w.bridges_on;
        gst.assign(w.groups.size(), GStat{{0, 0}, 0, 0, -2, 0});
        for (std::size_t gi = 0; gi < w.groups.size(); ++gi) {
            int sx = 0, sy = 0, n = 0;
            for (int ci : w.groups[gi].camps) sx += w.camps[static_cast<std::size_t>(ci)].pos.x, sy += w.camps[static_cast<std::size_t>(ci)].pos.y, ++n;
            gst[gi].n = n;
            if (n) gst[gi].c = vec2{(sx + n / 2) / n, (sy + n / 2) / n}, gst[gi].spn = near_d(w.spawn_field, gst[gi].c);
            for (int ci : w.groups[gi].camps) gst[gi].rad = std::max(gst[gi].rad, cheb(w.camps[static_cast<std::size_t>(ci)].pos, gst[gi].c));
        }
    }
    struct GC { int gi; vec2 c; int d, wd, key; };
#if A2_NN_FAST
    // (fuel) kept between decisions: nearly sorted already, so an insertion sort is about n compares, with no allocation
    static std::vector<GC> gc;
    if (gc.empty())
        for (std::size_t gi = 0; gi < w.groups.size(); ++gi)
            if (gst[gi].n) gc.push_back({static_cast<int>(gi), gst[gi].c, 0, 0, 0});
    const std::size_t here_idx = field_index(pos);
    const std::uint16_t* const* fptr = w.field_ptr.size() == w.groups.size() ? w.field_ptr.data() : nullptr;
    for (auto& e : gc) {
        int wd = -1;
        if (fptr && fptr[e.gi]) {
            const int d = fptr[e.gi][here_idx];
            wd = d >= kUnreach ? -1 : d;
        }
        e.d = cheb(e.c, pos), e.wd = wd, e.key = wd < 0 ? 100000 + e.d : wd;
    }
    // (fuel) the same once per call instead of per camp
    std::size_t ally_idx[8];
    int n_ally = 0;
    for (const auto& a : w.allies) {
        if (n_ally < 8 && a.hp > 0) ally_idx[n_ally++] = field_index(a.pos);
    }
    int claim_n[kClaimSlots], claim_g[kClaimSlots];
    int n_claim = 0;
    for (int s2 = 0; s2 < kClaimSlots; ++s2)
        if (s2 != slot) claim_g[n_claim] = claim_of(s2), claim_n[n_claim] = 1, ++n_claim;
    for (std::size_t i = 1; i < gc.size(); ++i) {
        const GC e = gc[i];
        std::size_t j = i;
        for (; j > 0 && gc[j - 1].key > e.key; --j) gc[j] = gc[j - 1];
        gc[j] = e;
    }
#else
    std::vector<GC> gc;
    for (std::size_t gi = 0; gi < w.groups.size(); ++gi) {
        if (!gst[gi].n) continue;
        const vec2 c = gst[gi].c;
        int wd = -1;
        if (w.has_field(static_cast<int>(gi))) {
            const int d = w.group_distance(static_cast<int>(gi), pos);
            wd = d >= kUnreach ? -1 : d;
        }
        gc.push_back({static_cast<int>(gi), c, cheb(c, pos), wd, 0});
    }
    // walking distance when known (unknown / unreachable after every known one), then straight-line distance
    std::sort(gc.begin(), gc.end(), [](const GC& a, const GC& b) {
        const int ka = a.wd < 0 ? 100000 + a.d : a.wd, kb = b.wd < 0 ? 100000 + b.d : b.wd;
        return ka < kb;
    });
#endif
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
#if A2_NN_FAST
        {
            int cc = 0;
            const int gi_c = gc[static_cast<std::size_t>(i)].gi;
            for (int s2 = 0; s2 < n_claim; ++s2) cc += claim_g[s2] == gi_c;
            f[k + 14] = q(cc);
        }
#else
        f[k + 14] = q(claim_count(gc[static_cast<std::size_t>(i)].gi));
#endif
#if A2_NN_FAST
        {
            // allies_near_group(g), most allies settled from the group's centre and radius
            int an = 0;
            const int rad = gst[static_cast<std::size_t>(gc[static_cast<std::size_t>(i)].gi)].rad;
            for (const auto& a : w.allies) {
                if (a.hp < a.max_hp * 0.35f) continue;
                const int dc = cheb(a.pos, c);
                if (dc > 5 + rad) continue;
                if (dc <= 5 - rad) {
                    ++an;
                    continue;
                }
                for (int ci : g.camps)
                    if (cheb(a.pos, w.camps[static_cast<std::size_t>(ci)].pos) <= 5) {
                        ++an;
                        break;
                    }
            }
            f[k + 15] = q(an);
        }
#else
        f[k + 15] = q(allies_near_group(g));
#endif
        const int gi2 = gc[static_cast<std::size_t>(i)].gi;
        f[k + 16] = q(gc[static_cast<std::size_t>(i)].wd);
        f[k + 17] = q(w.enemy_ready && gi2 < static_cast<int>(w.group_margin.size()) ? w.group_margin[static_cast<std::size_t>(gi2)] : 0);
        auto& gs = gst[static_cast<std::size_t>(gi2)];
        if (gs.alt == -2 && w.altar_ready) gs.alt = near_d(w.altar_field, c);
        f[k + 18] = q(w.altar_ready ? gs.alt : -1);
        f[k + 19] = q(gs.spn);
        // allies that reach this group before us (walking), the team's coverage of it
        int closer = 0;
#if A2_NN_FAST
        if (fptr && fptr[gi2]) {
            const std::uint16_t* fg = fptr[gi2];
            const int mine = fg[here_idx];
            for (int a2 = 0; a2 < n_ally; ++a2) closer += fg[ally_idx[a2]] < mine;
        }
#else
        if (w.has_field(gi2)) {
            const int mine = w.group_distance(gi2, pos);
            for (const auto& a : w.allies) closer += a.hp > 0 && w.group_distance(gi2, a.pos) < mine;
        }
#endif
        f[k + 20] = q(closer);
        f[k + 21] = q(gi2 == target_group ? 1 : 0); // our current (committed) target
#if A2_NN_XF
        if (!xfd.loaded) xf_load(slot);
        if (gi2 < kXMax) {
            f[k + 22] = q(xfd.vpt[gi2]);
            f[k + 23] = q(xfd.nbr[gi2]);
            f[k + 24] = q(xfd.team[gi2]);  // steps of the team plan at this group
            f[k + 25] = q(xfd.order[gi2]); // its place in my plan (1 = first; 0 = not in it)
            f[k + 26] = q(xfd.order[gi2] ? std::clamp(xfd.start[gi2] - round, -255, 255) : 0); // rounds until the plan starts here
        }
#endif
    }
    NN_FPROF(6);
    } else {
        k += NC * kCF;
    }
    if (parts & 65) {
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
    NN_FPROF(7);
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
#ifndef A2_NN_RESERVE
#define A2_NN_RESERVE 1000 // fuel every turn leaves unspent: up to 99k a turn is fine (going over the 100k cap costs the next turn)
#endif
#if A2_NN_FAST && !defined(A2_NN_RL)
#ifndef A2_NN_TTL
#define A2_NN_TTL 1000000 // a decision older than this many rounds is dropped (v92 decides until the next one)
#endif
#ifndef A2_NN_BEH
#define A2_NN_BEH 2 // bank gate: 2 the network's as published, 1 it may only force a bank (0 = v92 decides), 0 v92 banks
#endif
#ifndef A2_NN_VALID
#define A2_NN_VALID 0 // 1: a held target that went to respawning since its features were taken is skipped (next choice)
#endif
// The decision in force (E120, decisions held over several turns): the network's best target groups, each with its
// group's state when the features were taken, and its bank gate. A rank < 0 is the network's "none" slot: v92 chooses.
struct NNPub {
    int rank[4] = {-1, -1, -1, -1}, st[4] = {0, 0, 0, 0};
    int beh = -1, at = -1000000;
#ifdef A2_NN_ENS
    int n = 0, eg[12] = {}; // the groups scored and their scores, for the blend with v92's own choice (nn_ens_keep)
    float es[12] = {}, far = -1e30f;
#endif
};
static NNPub nn_pub;
#if defined(A2_NN_LIVE) && A2_NN_LIVE
#ifndef A2_NN_ZSTART
#define A2_NN_ZSTART 0 // 1: the slow part also runs at the start of the turn when it fits (E122: no gain on fresh or ladder maps, overruns 0.7% against 0.01%)
#endif
#ifndef A2_NN_ZFRESH
#define A2_NN_ZFRESH 0 // the bank gate applies only if its summary is from this many rounds ago or fewer; otherwise v92 banks
#endif
// Real-fuel state and fuel book-keeping: what v92 spent after the camp scoring (per turn kind: 0 no enemy in view, 1 nearest
// beyond 10, 2 nearest within 10, where v92's fight search may spend up to its 70k budget; each a slowly decaying maximum),
// the cost of the camp scoring and of each stage of the slow part, and how the turns went.
static nn::Live nn_lv;
static nn::Out nn_lo;
static std::int16_t nn_lf[kNF] = {};
#ifdef CLNA_HEAD
// Target-head inputs (clna-head-abi-v1, tools/rl_env_1104/native/head_export.py), taken where nn_pub is built:
//  - camp part (clna_snap): the frozen runtime's camp embeddings (Q10) and four camp fields of nn_pub's slots, refreshed
//    with every nn_pub, so the per-slot inputs belong to the slots and logits they adjust;
//  - context part (ClnaCtx): the trunk input x (Q10) and the head's projection h = relu(context(x)), which costs ~29k and
//    is accumulated in stages from spare end-of-turn fuel (clna_turn_end, JOHNDOE #83 option a) in jd_head::dense's own
//    operation order, so h is bit-identical to the one-shot head. Double-buffered: a pending context is staged while
//    the last completed one is in use; its round (the context age) is logged with every decision.
static_assert(A2_NN_Q16 && nnw::kTrunkIn == 160 && nnw::kEnc == 16, "clna-head-abi-v1: Q16 runtime, context 160, camp 16");
struct ClnaSnap {
    int at = -1, n = 0;
    std::int16_t ec[10][16], ft[10][4];
};
struct ClnaCtx {
    int at = -1;        // round x was taken (-1: none)
    std::int16_t x[160];
    alignas(16) float acc[64];
    int done = 0;        // inputs of x accumulated so far (0..160)
    bool ready = false;  // h (in acc) complete, and the h-only terms below
    float ek[16], ef[4], bias = 0, far = 0;
    double alpha = 0;
};
static ClnaSnap clna_snap;
static ClnaCtx clna_pend, clna_act;  // being staged / completed and in use
static int clna_skips[4] = {};       // this turn's skipped decisions by reason (CNK row at the end of the turn)
struct ClnaRow {                     // this turn's head decision, formatted as CNR3 by clna_emit_row
    bool pending = false;
    int round = 0, slot = 0, index = 0, ref = 0, chosen = 0, v92 = 0, nn = 0, n = 0, pub = 0, ctx = 0, nu = 0;
    long id = 0;
    double alpha = 0, p = 0;
    int ug[14] = {}, map[11] = {};
    float nat[11] = {};
    std::int16_t ec[10][16] = {}, ft[10][4] = {};  // (x is clna_act.x, the context in use)
    long f_before = 0, f_head = 0, f_left = 0, f_stash = 0;  // CLNA_FPROF
};
static ClnaRow clna_row;
static int clna_memo_hits = 0, clna_memo_misses = 0;  // (CLNA_FPROF reports them)
static void clna_take_snap(const std::int16_t* f, int coff, int at) {
    // Exact memoisation (JOHNDOE #90): a new context whose 320 raw bytes equal the completed one in use needs no staging;
    // its h and h-only terms are reused (the weights are compiled in), and its round stays the round those bytes were
    // first taken. Never keyed on rounds or slots; a pending context is never marked ready early.
    if (clna_pend.at < 0) {
        if (clna_act.ready && __builtin_memcmp(nn_lv.x, clna_act.x, sizeof clna_act.x) == 0) ++clna_memo_hits;
        else std::copy(nn_lv.x, nn_lv.x + 160, clna_pend.x), clna_pend.at = at, clna_pend.done = 0, clna_pend.ready = false, ++clna_memo_misses;
    }
    int n = 0;
    for (int i = 0; i < kC && n < 10; ++i) {
        const std::int16_t* r = f + coff + i * kCF;
        if (r[0] != 1) continue;
        std::copy(nn_lv.ec[i], nn_lv.ec[i] + 16, clna_snap.ec[n]);
        clna_snap.ft[n][0] = r[16], clna_snap.ft[n][1] = r[14], clna_snap.ft[n][2] = r[20], clna_snap.ft[n][3] = r[21];
        ++n;
    }
    clna_snap.n = n, clna_snap.at = at;
}
#endif
#ifdef A2_NN_LAZY
static std::uint64_t nn_need[3] = {16000, 18000, 20000}, nn_mark = 0, nn_est_camps = 30000, nn_sum_camps = 0; // (nn_need: what v92 spends after its target choice)
#else
static std::uint64_t nn_need[3] = {25000, 30000, 45000}, nn_mark = 0, nn_est_camps = 30000, nn_sum_camps = 0;
#endif
// starting estimates: the 16 x 64 student's measured stage costs (E121), scaled with the matrix sizes of a larger student (E123)
static constexpr std::uint64_t kSE = nnw::kEnc * 1000 / 16, kST0 = nnw::kEnc * nnw::kTrunk * 1000 / (16 * 64), kST1 = nnw::kTrunk * nnw::kTrunk * 1000 / (64 * 64);
static std::uint64_t nn_est_stage[nn::kLiveStages] = {13 * kSE, 14 * kSE, 6 * kSE + 8 * kST0, 8 * kST0, 8 * kST0, 10 * kST1, 6 * kST0};
static std::uint32_t nn_round0 = 0;
static int nn_kind = 0, nn_path = 3, nn_live_turns = 0, nn_c_refresh = 0, nn_c_camps = 0, nn_c_hold = 0, nn_c_contact = 0;
static int nn_zstage = 0, nn_zstart = 0, nn_zround = -1000; // next stage + 1 (0: no refresh under way), its start, the last refresh
static int nn_warm = 0;                                     // one-time setup at the end of the first turns: 0 features next, 1 camps next, 2 done
#ifdef A2_NN_NNUE
static int nn_xdone = 0, nn_xnext = 0;                      // slow blocks encoded once (bits, by place in kXOrder); the next to refresh
static constexpr int kXOrder[4] = {3, 2, 0, 5}, kXPart[4] = {32, 16, 8, 64}; // nn::live_block's number and nn_feats_t's part: enemies, allies, global, altars
static std::uint64_t nn_xest[4] = {12000, 12000, 4000, 9000}, nn_est_c2 = 26000;
static int nn_c_camps2 = 0;
static int nn_xround[4] = {-1, -1, -1, -1};                 // when each was last refreshed
#endif
static constexpr std::uint64_t kStageCeil[nn::kLiveStages] = {20 * kSE, 25 * kSE, 10 * kSE + 14 * kST0, 14 * kST0, 14 * kST0, 18 * kST1, 12 * kST0}; // an overrun raises an estimate at most to this
#if defined(A2_NN_RLIVE) && A2_NN_RLIVE
// RL rollouts of the deployed bot (nn_rl4.py, debug builds): the target is sampled and the rows logged inside debug_block, which
// spends no fuel, so a rollout has exactly the deployed bot's fuel. nn_zf: the features the summary in force was computed from
// (the whole vector at its start, the camp block as of its pooling stage), so the trainer can reproduce each decision exactly.
#ifndef A2_NN_RL_T
#define A2_NN_RL_T 0.4
#endif
#ifndef A2_NN_RL_KEEP
#define A2_NN_RL_KEEP 10 // one in this many rows that keep the current target is logged; every change is
#endif
static std::int16_t nn_zf[kNF] = {}, nn_zfp[kNF] = {};
static int nn_zid = 0, nn_zid_printed = -1;
static std::uint64_t nn_rs = 0;
static std::uint64_t nn_rand(std::uint64_t seed) {
    if (!nn_rs) nn_rs = 0x9E3779B97F4A7C15ull ^ (seed << 32) ^ (seed * 0x1000193ull);
    nn_rs ^= nn_rs << 13, nn_rs ^= nn_rs >> 7, nn_rs ^= nn_rs << 17;
    return nn_rs;
}
// sample from softmax(logits / A2_NN_RL_T); lp: log-probability of the choice
static int nn_sample(const float* lg, int n, float& lp, std::uint64_t seed) {
    const float temp = static_cast<float>(A2_NN_RL_T);
    float mx = -1e30f, z = 0.0f, p[32];
    for (int i = 0; i < n; ++i) mx = std::max(mx, lg[i] / temp);
    for (int i = 0; i < n; ++i) z += (p[i] = lg[i] < -1e8f ? 0.0f : std::exp(lg[i] / temp - mx));
    float u = static_cast<float>(nn_rand(seed) >> 40) / static_cast<float>(1ull << 24) * z;
    int a = n - 1;
    for (int i = 0; i < n; ++i)
        if (p[i] > 0.0f && (u -= p[i]) <= 0.0f) {
            a = i;
            break;
        }
    lp = std::log(std::max(p[a] / z, 1e-12f));
    return a;
}
#endif
// Run the slow part's next stages while the fuel left covers the most each has cost lately (+1/8) above `floor`.
static void nn_run_stages(std::uint64_t floor, int rnd) {
    if (nn_zstage > 0 && rnd - nn_zstart > 12) nn_zstage = 0; // its features are too old: start again
    while (nn_zstage > 0) {
        const int s = nn_zstage - 1;
        const std::uint64_t left = bc::fuel_remaining();
        if (left < nn_est_stage[s] + floor) return;
        const auto r0 = bc::round_number();
#if defined(A2_NN_RLIVE) && A2_NN_RLIVE
        if (s == 2) debug_block({ std::copy(nn_lf, nn_lf + kNF, nn_zfp); });
#endif
        nn::live_stage(nn_lf, nn_lv, s);
#if defined(A2_NN_RLIVE) && A2_NN_RLIVE
        if (s == nn::kLiveStages - 1) debug_block({
            std::copy(nn_zfp, nn_zfp + kNF, nn_zf);
            ++nn_zid;
        });
#endif
        const std::uint64_t now = bc::fuel_remaining();
        if (bc::round_number() != r0 || now > left) {
            nn_est_stage[s] = std::max(nn_est_stage[s], std::min(left + static_cast<std::uint64_t>(A2_NN_RESERVE), kStageCeil[s])); // (never out of reach)
        } else {
            const std::uint64_t used = left - now;
            nn_est_stage[s] = std::max(used + used / 8, nn_est_stage[s] - nn_est_stage[s] / 32);
        }
        if (++nn_zstage > nn::kLiveStages) nn_zstage = 0, nn_zround = nn_zstart, ++nn_c_refresh; // nn_zround: the round its features are from
    }
}
#endif
static NNPub nn_make_pub(const std::int16_t* f, const float* target, int n, int nc, int coff, int beh, int at) {
    NNPub p;
    p.beh = beh, p.at = at;
    float v[32];
    std::copy(target, target + n, v);
    for (int r = 0; r < 4; ++r) {
        const int t = static_cast<int>(std::max_element(v, v + n) - v);
        if (t >= nc || f[coff + t * kCF] != 1) break;
        p.rank[r] = f[coff + t * kCF + 1], p.st[r] = f[coff + t * kCF + 7];
        v[t] = -2e9f;
    }
#ifdef A2_NN_ENS
    p.far = target[nc];
    for (int i = 0; i < nc && i < 12; ++i)
        if (f[coff + i * kCF] == 1) p.eg[p.n] = f[coff + i * kCF + 1], p.es[p.n] = target[i], ++p.n;
#endif
    return p;
}
#ifdef A2_NN_NNUE
// refresh slow block x of kXOrder from this turn's world
void Bot::nn_x_refresh(int x) {
    constexpr int kOff[4] = {kG + kS + kA * kAF, kG + kS, 0, kG + kS + kA * kAF + kE * kEF + kC * kCF}, kLen[4] = {kE * kEF, kA * kAF, kG, kL * kLF};
    const std::uint64_t f0 = bc::fuel_remaining();
    const auto r0 = bc::round_number();
    std::fill(nn_lf + kOff[x], nn_lf + kOff[x] + kLen[x], static_cast<std::int16_t>(0));
    nn_feats_t<kC, kAF>(nn_lf, nn_near(), kXPart[x]);
    nn::live_block(nn_lf, nn_lv, kXOrder[x]);
    nn_xdone |= 1 << x, nn_xround[x] = round;
    const std::uint64_t f1 = bc::fuel_remaining();
    if (bc::round_number() != r0 || f1 > f0) return;
    const std::uint64_t used = f0 - f1;
    nn_xest[x] = std::max(used + used / 8, nn_xest[x] - nn_xest[x] / 32);
}
#endif
#ifdef A2_NN_LAZY
#ifndef A2_NN_LAZY_FLOOR
#define A2_NN_LAZY_FLOOR 8000 // at least this fuel is left after the scoring, for what farm() still does (the move); more if v92 has spent more there lately
#endif
#ifndef A2_NN_LAZY_TTL
#define A2_NN_LAZY_TTL 2 // scores older than this many rounds have no say: v92's choice stands
#endif
#ifdef A2_NN_NNUE
#define A2_NN_NNUE_CEIL 70000
#else
#define A2_NN_NNUE_CEIL 45000
#endif
// E123: in farm(), right after v92's own target choice. Whatever v92 needs before this point (world, fights, its target search) is spent, at v92's own fuel: nothing to predict
// and no effect on v92's fuel gates. If the fuel left covers it, the camps are scored on this turn's features with the last summary; the decision in force is then applied.
void Bot::nn_lazy_score() {
    constexpr int kCOffL = kG + kS + kA * kAF + kE * kEF;
    static bool first_camps = true;
    nn_group = -1;
    if (nn_live_turns <= 1) return;
#ifdef A2_NN_FIELDS_FIRST
    // E125: on big maps a distance field costs about 43k and is built at the end of the turn: until they are all built the network does not score (v92's choice stands), or v92 and the network would both play
    // the opening without walking distances (official maps over 60 wide: 35-40% at real fuel, 58% at 20M)
    if (!w.fields_ready()) {
        nn_mark = bc::fuel_remaining(), nn_round0 = bc::round_number(), nn_field_fuel = 0;
        return;
    }
#endif
#ifdef A2_NN_ENSEVERY
    // E123: the network has a say only when v92 wants to change target, or every A2_NN_ENSEVERY rounds (v92 and the current target agree on most turns); the fuel of the other turns goes to the slow blocks
    if (nn_v92best == target_group && (round + slot) % A2_NN_ENSEVERY != 0) {
        nn_mark = bc::fuel_remaining(), nn_round0 = bc::round_number(), nn_field_fuel = 0;
        return;
    }
#endif
    const int near_e = nn_near();
    nn_kind = w.enemies.empty() ? 0 : near_e > 10 ? 1 : 2;
    const std::uint64_t f0 = bc::fuel_remaining(), floor_f = std::max<std::uint64_t>(nn_need[nn_kind], A2_NN_LAZY_FLOOR) + 2000;
    std::uint64_t enemy_used = 0;
#if A2_FUELLOG
    {
        // fuel left at v92's target choice, and what the gate asks for, by 10k steps
        static int hist[11] = {}, hg[11] = {}, nh = 0;
        ++hist[std::min<int>(10, static_cast<int>(f0 / 10000))], ++hg[std::min<int>(10, static_cast<int>((nn_est_camps + floor_f) / 10000))];
        if (++nh % 400 == 0) {
            std::printf("nnfarm n %d left", nh);
            for (int i = 0; i < 11; ++i) std::printf(" %d", hist[i]);
            std::printf(" gate");
            for (int i = 0; i < 11; ++i) std::printf(" %d", hg[i]);
            std::printf(" est %llu floor %llu full %d hold %d\n", static_cast<unsigned long long>(nn_est_camps), static_cast<unsigned long long>(floor_f), nn_c_camps, nn_c_hold);
        }
    }
#endif
#ifdef A2_NN_LAZY_CHOLD
    // in contact: the last decision holds, whatever its age, as in the every-turn network at 20M
    if (near_e <= 6) {
        ++nn_c_contact, nn_path = 3;
        nn_mark = bc::fuel_remaining(), nn_round0 = bc::round_number(), nn_field_fuel = 0;
        for (int r = 0; r < 4 && nn_pub.rank[r] >= 0; ++r) {
#if A2_NN_VALID
            if (w.groups[static_cast<std::size_t>(nn_pub.rank[r])].state == GroupState::respawning && nn_pub.st[r] != static_cast<int>(GroupState::respawning)) continue;
#endif
            nn_group = nn_pub.rank[r];
            break;
        }
        return;
    }
#endif
#ifdef A2_NN_LAZYFULL
    // E124 diagnosis at 20M: all features and the plain network, at farm() instead of the start of the turn
    if (nn_warm == 2) {
        std::fill(nn_lf, nn_lf + kNF, static_cast<std::int16_t>(0));
        nn_feats_t<kC, kAF>(nn_lf, near_e, 3);
        nn::forward(nn_lf, nn_lo, nn::kHBeh | nn::kHTarget);
#ifdef A2_NN_LJIT
        for (int i = 0; i < kC + 1; ++i) {
            std::uint32_t h = (static_cast<std::uint32_t>(A2_NN_LJIT) * 2654435761u) ^ (static_cast<std::uint32_t>(i) * 40503u) ^
                              (static_cast<std::uint32_t>(round / 8) * 2246822519u) ^ (static_cast<std::uint32_t>(slot) * 97u);
            h = h * 1664525u + 1013904223u, h = h * 1664525u + 1013904223u;
            nn_lo.target[i] += static_cast<float>(A2_NN_LJIT_A) * (static_cast<float>(h >> 8) / 16777216.0f - 0.5f);
        }
#endif
        nn_pub = nn_make_pub(nn_lf, nn_lo.target, kC + 1, kC, kCOffL, -1, round);
#ifdef A2_NN_DBG
        if (round <= A2_NN_DBG) {
            std::printf("NND %d %d %d %d %s", round, slot, nn_pub.rank[0], -1, b64(nn_lf, kNF).c_str());
            for (int i = 0; i < 8; ++i) std::printf(" %.4f", nn_lo.behaviour[i]);
            for (int i = 0; i < kC + 1; ++i) std::printf(" %.4f", nn_lo.target[i]);
            std::printf("\n");
        }
#endif
        nn_mark = bc::fuel_remaining(), nn_round0 = bc::round_number(), nn_field_fuel = 0;
        for (int r = 0; r < 4 && nn_pub.rank[r] >= 0; ++r) {
#if A2_NN_VALID
            if (w.groups[static_cast<std::size_t>(nn_pub.rank[r])].state == GroupState::respawning && nn_pub.st[r] != static_cast<int>(GroupState::respawning)) continue;
#endif
            nn_group = nn_pub.rank[r];
            break;
        }
        return;
    }
#endif
    if (nn_warm == 2 && f0 >= nn_est_camps + floor_f) {
        const auto r0 = bc::round_number();
        std::fill(nn_lf + kCOffL, nn_lf + kCOffL + kC * kCF, static_cast<std::int16_t>(0));
#ifdef A2_NN_NNUE
        // E123: self + camps fresh every turn; trunk layer 0 is updated by the inputs that changed, the rest of the network runs in full (nn_infer.h)
        std::fill(nn_lf + kG, nn_lf + kG + kS, static_cast<std::int16_t>(0));
#if A2_FUELLOG
        static std::uint64_t cost[6] = {}, cost_n = 0;
        std::uint64_t cf = bc::fuel_remaining();
        const auto cmark = [&](int i) {
            const std::uint64_t now = bc::fuel_remaining();
            cost[i] += cf - now, cf = now;
        };
#else
#define cmark(i)
#endif
        nn_feats_t<kC, kAF>(nn_lf, near_e, 2 | 4);
        cmark(0);
        nn::live_camps(nn_lf, nn_lv, w.groups.size());
        cmark(1);
        nn::live_block(nn_lf, nn_lv, 1);
        cmark(2);
        nn::live_block(nn_lf, nn_lv, 4);
        cmark(3);
        // enemies in view: this turn's too, if the fuel allows (simulated at 20M, official maps: 63.8% with enemies fresh, 58.1% without, 47.6% with only the camps fresh)
        {
            const std::uint64_t fe0 = bc::fuel_remaining();
            if (!w.enemies.empty() && fe0 >= nn_xest[0] + 12000 + floor_f) {
                nn_x_refresh(0);
                const std::uint64_t fe1 = bc::fuel_remaining();
                enemy_used = fe0 > fe1 ? fe0 - fe1 : 0;
            }
        }
        cmark(4);
        if (nn_xdone == 15) {
            nn::live_top(nn_lv);
#if defined(A2_NN_RLIVE) && A2_NN_RLIVE
            debug_block({
                std::copy(nn_lf, nn_lf + kNF, nn_zf);
                ++nn_zid;
            });
#endif
        }
        cmark(5);
#if A2_FUELLOG
        if (++cost_n % 200 == 0)
            std::printf("nncost n %llu feats %llu camps %llu self %llu pool %llu enemy %llu top %llu est %llu xest %llu %llu %llu %llu\n", static_cast<unsigned long long>(cost_n),
                        static_cast<unsigned long long>(cost[0] / cost_n), static_cast<unsigned long long>(cost[1] / cost_n), static_cast<unsigned long long>(cost[2] / cost_n),
                        static_cast<unsigned long long>(cost[3] / cost_n), static_cast<unsigned long long>(cost[4] / cost_n), static_cast<unsigned long long>(cost[5] / cost_n),
                        static_cast<unsigned long long>(nn_est_camps), static_cast<unsigned long long>(nn_xest[0]), static_cast<unsigned long long>(nn_xest[1]),
                        static_cast<unsigned long long>(nn_xest[2]), static_cast<unsigned long long>(nn_xest[3]));
#else
#undef cmark
#endif
#else
        nn_feats_t<kC, kAF>(nn_lf, nn_near(), 2);
        nn::live_camps(nn_lf, nn_lv, w.groups.size());
#endif
        if (nn_lv.z_ok) {
            nn::live_target(nn_lv, nn_lo);
#ifdef A2_NN_LJIT
            // tiny noise on the bot's own scores: another line of play from the same bot, for testing (deterministic games: a build is one draw)
            for (int i = 0; i < kC + 1; ++i) {
                std::uint32_t h = (static_cast<std::uint32_t>(A2_NN_LJIT) * 2654435761u) ^ (static_cast<std::uint32_t>(i) * 40503u) ^
                                  (static_cast<std::uint32_t>(round / 8) * 2246822519u) ^ (static_cast<std::uint32_t>(slot) * 97u);
                h = h * 1664525u + 1013904223u, h = h * 1664525u + 1013904223u;
                nn_lo.target[i] += static_cast<float>(A2_NN_LJIT_A) * (static_cast<float>(h >> 8) / 16777216.0f - 0.5f);
            }
#endif
            nn_pub = nn_make_pub(nn_lf, nn_lo.target, kC + 1, kC, kCOffL, -1, round);
#ifdef CLNA_HEAD
            clna_take_snap(nn_lf, kCOffL, round);
#endif
        }
        const std::uint64_t f1 = bc::fuel_remaining();
        if (bc::round_number() != r0 || f1 > f0) {
            nn_est_camps = std::max(nn_est_camps, std::min<std::uint64_t>(f0, A2_NN_NNUE_CEIL)); // (never out of reach)
        } else {
            const std::uint64_t used = f0 - f1 - std::min(enemy_used, f0 - f1);
            nn_sum_camps += used;
            if (!first_camps) nn_est_camps = std::max(used + used / 8, nn_est_camps - nn_est_camps / 32); // (the first carries one-time setup)
        }
        first_camps = false;
        ++nn_c_camps, nn_path = 1;
#if defined(A2_NN_NNUE) && defined(A2_NN_TIER2)
    } else if (nn_warm == 2 && nn_lv.z_ok && f0 >= nn_est_c2 + floor_f) {
        // not enough for the rest of the network: the camps alone, with the last pointer vector (E121's cheaper tier)
        nn_est_camps -= nn_est_camps / 16;
        const auto r0 = bc::round_number();
        std::fill(nn_lf + kCOffL, nn_lf + kCOffL + kC * kCF, static_cast<std::int16_t>(0));
        nn_feats_t<kC, kAF>(nn_lf, near_e, 2);
        nn::live_camps(nn_lf, nn_lv, w.groups.size());
        nn::live_target(nn_lv, nn_lo);
        nn_pub = nn_make_pub(nn_lf, nn_lo.target, kC + 1, kC, kCOffL, -1, round);
        const std::uint64_t f1 = bc::fuel_remaining();
        if (bc::round_number() != r0 || f1 > f0) {
            nn_est_c2 = std::max(nn_est_c2, std::min<std::uint64_t>(f0, 45000));
        } else {
            const std::uint64_t used = f0 - f1;
            nn_est_c2 = std::max(used + used / 8, nn_est_c2 - nn_est_c2 / 32);
        }
        ++nn_c_camps2, nn_path = 1;
#endif
    } else {
        // (an estimate pushed up by one costly turn must not lock the scoring out: it comes down while unused too)
        nn_est_camps -= nn_est_camps / 16;
#ifdef A2_NN_NNUE
        nn_est_c2 -= nn_est_c2 / 16;
#endif
        ++nn_c_hold, nn_path = 0;
    }
    nn_mark = bc::fuel_remaining(), nn_round0 = bc::round_number(), nn_field_fuel = 0;
#if defined(A2_NN_XFDBG) && A2_NN_XF
    if (round % A2_NN_XFDBG == 0) {
        std::printf("NNXF round %d slot %d enemy alive %d dead %d next %d sum %d ally dead %d next %d |", round, slot, nn_lf[16], nn_lf[17], nn_lf[18], nn_lf[19], nn_lf[20], nn_lf[21]);
        for (int i = 0; i < 5; ++i) {
            const std::int16_t* c = nn_lf + kCOffL + i * kCF;
            std::printf(" g%d vpt %d nbr %d team %d order %d start %d;", c[1], c[22], c[23], c[24], c[25], c[26]);
        }
        std::printf("\n");
    }
#endif
#ifdef A2_NN_HOLDKEEP
    // no new information from the network this turn: no change of target (going back to v92's pick and then to the network's again next turn walks in circles)
    nn_stay = nn_path == 0 && nn_lv.z_ok && target_group >= 0 && target_group < static_cast<int>(w.groups.size()) &&
              w.groups[static_cast<std::size_t>(target_group)].state != GroupState::respawning && avoid_until[static_cast<std::size_t>(target_group)] <= round;
    if (nn_stay) {
        nn_group = target_group;
        return;
    }
#endif
    if (round - nn_pub.at > A2_NN_LAZY_TTL) return;
    for (int r = 0; r < 4 && nn_pub.rank[r] >= 0; ++r) {
#if A2_NN_VALID
        if (w.groups[static_cast<std::size_t>(nn_pub.rank[r])].state == GroupState::respawning && nn_pub.st[r] != static_cast<int>(GroupState::respawning)) continue;
#endif
        nn_group = nn_pub.rank[r];
        break;
    }
}
#endif
#ifdef A2_NN_FCMP
// E124 diagnosis at 20M: why does scoring in farm() lose against the start of the turn? Same turn, same bot: this turn's features at the start of the turn (nn_lf) against the same features taken at v92's target choice.
void Bot::nn_fcmp(int v92g) {
    static int calls = 0, diff_top = 0, diff_blend = 0, any = 0;
    static int cnt[kNF] = {};
    static std::int16_t tmp[kNF];
    static nn::Out o2;
    std::fill(tmp, tmp + kNF, static_cast<std::int16_t>(0));
    nn_feats_t<kC, kAF>(tmp, nn_near(), 3);
    bool d = false;
    for (int i = 0; i < kNF; ++i)
        if (tmp[i] != nn_lf[i]) ++cnt[i], d = true;
    any += d;
    nn::forward(tmp, o2, nn::kHBeh | nn::kHTarget);
    const NNPub p2 = nn_make_pub(tmp, o2.target, kC + 1, kC, kG + kS + kA * kAF + kE * kEF, -1, round);
    diff_top += p2.rank[0] != nn_pub.rank[0];
    const bool k1 = nn_pub.rank[0] < 0 || nn_ens_keep(v92g, nn_pub.rank[0]);
    float sv = p2.far, sn = -1e30f;
    for (int i = 0; i < p2.n; ++i) {
        if (p2.eg[i] == v92g) sv = p2.es[i];
        if (p2.eg[i] == p2.rank[0]) sn = p2.es[i];
    }
    const bool k2 = p2.rank[0] < 0 || sv + static_cast<float>(A2_NN_ENS) >= sn;
    diff_blend += k1 != k2 || (!k1 && p2.rank[0] != nn_pub.rank[0]);
    if (++calls % 1000 == 0) {
        std::printf("NNFC calls %d rows with any difference %d, top camp differs %d, blend decision differs %d |", calls, any, diff_top, diff_blend);
        for (int i = 0; i < kNF; ++i)
            if (cnt[i] * 50 > calls) std::printf(" %d:%d", i, cnt[i]);
        std::printf("\n");
    }
}
#endif
#ifdef A2_NN_ENSLOG
// E124: the blend's states for training a smaller model (nn_ens_rec.py, 20M fuel): every disagreement between the network's top group and v92's choice, 1 in 8 of the rest
static std::int16_t nn_ef[kNF] = {};
void Bot::nn_ens_log(int v92g, int ng) {
    static int cnt = 0;
    const bool dis = v92g != ng;
    if (dis || ++cnt % 8 == 0) std::printf("NRE %d %d %d %d %d %s\n", round, slot, v92g, ng, dis ? 1 : 0, b64(nn_ef, kNF).c_str());
}
#endif
#ifdef A2_NN_ENS
// E123: blend of the network and v92 (farm(), nn_mkbot.py): v92's own choice stays unless the network's scores the other group more than A2_NN_ENS logits higher.
// A group outside the network's 10 nearest counts at the network's "far" score.
bool Bot::nn_ens_keep(int v92g, int ng) const {
    float sv = nn_pub.far, sn = -1e30f;
    for (int i = 0; i < nn_pub.n; ++i) {
        if (nn_pub.eg[i] == v92g) sv = nn_pub.es[i];
        if (nn_pub.eg[i] == ng) sn = nn_pub.es[i];
    }
    return sv + static_cast<float>(A2_NN_ENS) >= sn;
}
#if defined(A2_NN_RLIVE) && A2_NN_RLIVE
// RL rollouts of the blend (nn_rl4.py, NN_ENS): the group is sampled here, where v92's choice is known, from the deployed scores with the bonus on v92's choice ("far" stands
// for a choice outside the 10 nearest), and the row is logged with v92's slot. Inside debug_block: no fuel.
int Bot::nn_ens_sample(int v92g) {
    int out = v92g;
    debug_block({
        constexpr int kCOffL = kG + kS + kA * kAF + kE * kEF;
        float v[kC + 1];
        std::copy(nn_lo.target, nn_lo.target + kC + 1, v);
        int bs = kC;
        for (int i = 0; i < kC; ++i)
            if (nn_lf[kCOffL + i * kCF] == 1 && nn_lf[kCOffL + i * kCF + 1] == v92g) bs = i;
        v[bs] += static_cast<float>(A2_NN_ENS);
        float lp = 0.0f;
        const int a = nn_sample(v, kC + 1, lp, static_cast<std::uint64_t>(my_id) + 1);
        if (a < kC && nn_lf[kCOffL + a * kCF] == 1) out = nn_lf[kCOffL + a * kCF + 1];
        const bool chg = out != target_group;
        if (chg || nn_rand(0) % A2_NN_RL_KEEP == 0) {
            if (nn_zid_printed != nn_zid) {
                std::printf("NRZ %d %s\n", nn_zid, b64(nn_zf, kNF).c_str());
                nn_zid_printed = nn_zid;
            }
            static std::int16_t xn[kNF];
#ifdef A2_NN_NNUE
            std::copy(nn_lf, nn_lf + kNF, xn);
#else
            std::fill(xn, xn + kNF, static_cast<std::int16_t>(0));
            nn_feats_t<kC, kAF>(xn, nn_near(), 1);
            std::copy(nn_lf + kCOffL, nn_lf + kCOffL + kC * kCF, xn + kCOffL);
#endif
            std::printf("NRL %d %d %d %.5f %d %d %d %s\n", round, slot, a, lp, chg ? 1 : 0, nn_zid, bs, b64(xn, kNF).c_str());
        }
    });
    return out;
}
#endif
#endif
#ifdef CLNA_EPS
// rl-env (task rl-env-collector-1104, JOHNDOE NATIVE_ADAPTER_REVIEW.md): exploration-only baseline over the FROZEN native
// policy. Reference = the deterministic blend (nn_ens_keep). Candidates = the runtime's scored groups nn_pub.eg/es and the
// far slot, which falls back to v92's choice. Policy over PHYSICAL groups (duplicates merged):
//   pi(g) = (1 - eps) * [g == reference] + eps * softmax(native scores)(g)
// The sample is drawn here, charged, as the acting policy; only the row is logged in debug_block:
//   CNA1 <round> <slot> <id> <ref> <chosen> <logp> <eps> <v92> <nn> <k> {<group>:<q>}*k <b64 int16[kNF] features>
#ifndef CLNA_SEED
#define CLNA_SEED 1104
#endif
#include "clna_gate.h"
#ifdef CLNA_HEAD
#ifndef CLNA_HEAD_MIN
#define CLNA_HEAD_MIN 35000  // fuel left needed for the head's remainder + its log + v92's own work after the blend
#endif
#ifndef CLNA_STAGE_MIN
#define CLNA_STAGE_MIN 7000  // spare end-of-turn fuel needed for one more stage (~2.9k typical, up to ~4k): keeps >= ~3k
#endif
#include "clna_head_w.h"
#include "jd_codec.h"
#include "jd_head.h"
// One stage = 16 inputs of jd_head::dense<64>(x, w, 160, h, true): same accumulator start (the bias), same per-input
// mul-add order, so the staged h equals the one-shot h bit for bit; relu with the same f32x4.max at the end.
static void clna_stage() {  // one stage of the pending context; a completed one becomes the context in use
    ClnaCtx& c = clna_pend;
    const float* w = clna_head::kW;
    v128_t a[16];
    if (c.done == 0)
        for (int j = 0; j < 16; ++j) a[j] = wasm_v128_load(w + 160 * 64 + 4 * j);
    else
        for (int j = 0; j < 16; ++j) a[j] = wasm_v128_load(c.acc + 4 * j);
    const int end = c.done + 16;
    for (int i = c.done; i < end; ++i) {
        const auto xv = wasm_f32x4_splat(static_cast<float>(c.x[i]) * (1.0f / 1024.0f));
#pragma clang loop unroll(full)
        for (int j = 0; j < 16; ++j) a[j] = wasm_f32x4_add(a[j], wasm_f32x4_mul(xv, wasm_v128_load(w + i * 64 + 4 * j)));
    }
    c.done = end;
    if (end == 160)
        for (int j = 0; j < 16; ++j) a[j] = wasm_f32x4_max(a[j], wasm_f32x4_splat(0)), c.ready = true;
    for (int j = 0; j < 16; ++j) wasm_v128_store(c.acc + 4 * j, a[j]);
    if (c.ready) {
        // everything of jd_head::scores that depends on h alone, once per context (same operations, same order):
        // q = query(h), the folded pointer bias / key / feature vectors, the far residual and alpha
        const float* h = c.acc;
        float q[16];
        jd_head::dense<16>(h, w + 10304, 64, q, false);
        c.bias = 0;
        for (int j = 0; j < 16; ++j) c.bias += (w[11600 + j] + w[11680 + j]) * q[j];
        for (int i = 0; i < 16; ++i) {
            c.ek[i] = 0;
            for (int j = 0; j < 16; ++j) c.ek[i] += w[11344 + i * 16 + j] * q[j];
        }
        for (int i = 0; i < 4; ++i) {
            c.ef[i] = 0;
            for (int j = 0; j < 16; ++j) c.ef[i] += w[11616 + i * 16 + j] * q[j];
        }
        float far = w[11760], gate = w[11825];
        for (int j = 0; j < 64; ++j) far += h[j] * w[11696 + j], gate += h[j] * w[11761 + j];
        c.far = far, c.alpha = 1 / (1 + std::exp(-double(gate)));
        clna_act = c, c.at = -1;  // the next nn_pub starts a new pending context
    }
}
// the rest of jd_head::scores + probabilities: per-camp dot products and the mixture (unchanged operations)
static void clna_head_rest(const ClnaCtx& cx, const float* camps, const float* features, const float* native, int n,
                           const bool* valid, const int* map, int reference, int p, double* out, double& alpha) {
    float logits[64];
    for (int k = 0; k < n; ++k) {
        float z = cx.bias;
        for (int j = 0; j < 16; ++j) z += camps[k * 16 + j] * cx.ek[j];
        for (int j = 0; j < 4; ++j) z += features[k * 4 + j] * cx.ef[j];
        logits[k] = native[k] + z / 4;
    }
    logits[n] = native[n] + cx.far;
    alpha = cx.alpha;
    float mx = -INFINITY;
    for (int j = 0; j <= n; ++j)
        if (valid[j] && logits[j] > mx) mx = logits[j];
    double total = 0, expv[64];
    for (int j = 0; j <= n; ++j) expv[j] = valid[j] ? std::exp(double(logits[j] - mx)) : 0, total += expv[j];
    for (int j = 0; j < p; ++j) out[j] = 0;
    for (int j = 0; j <= n; ++j)
        if (valid[j]) out[map[j]] += alpha * (expv[j] / total);
    out[reference] += 1 - alpha;
}
#endif
static std::uint64_t clna_rng = 0;
#if CLNA_RLOG
// Release logger (JOHNDOE #69): the logging build IS the collected and evaluated policy, so logging is charged and
// deterministic: one fixed buffer, raw IEEE-754 bits as hex (no float formatting), one write per decision. It never
// branches on output success and never touches the RNG.
// (fuel) The writers take and return a local cursor and store two hex digits per table load (one 16-bit store): the
// per-character formatting was ~18 fuel/char (CLNA_FPROF). Output is byte-identical to the first CNR1 writer.
static char clna_rbuf[4096];  // (CNR2: ~2.1k characters at 10 slots)
struct ClnaHex2 {  // byte -> its two hex digits as one little-endian uint16 (first digit in the low byte)
    std::uint16_t t[256];
    constexpr ClnaHex2() : t{} {
        for (int i = 0; i < 256; ++i)
            t[i] = static_cast<std::uint16_t>("0123456789abcdef"[i >> 4] | ("0123456789abcdef"[i & 15] << 8));
    }
};
static constexpr ClnaHex2 clna_hex2{};
static char* clna_rint(char* o, long v) {  // decimal integer
    char t[24];
    int n = 0;
    unsigned long u = v < 0 ? 0ul - static_cast<unsigned long>(v) : static_cast<unsigned long>(v);
    if (v < 0) *o++ = '-';
    do t[n++] = static_cast<char>('0' + u % 10), u /= 10; while (u);
    while (n) *o++ = t[--n];
    return o;
}
static char* clna_rdbl(char* o, double d) {  // raw IEEE-754 bits, 16 hex digits
    std::uint64_t u;
    __builtin_memcpy(&u, &d, sizeof u);
    for (int i = 7; i >= 0; --i) __builtin_memcpy(o + 2 * i, &clna_hex2.t[u & 255u], 2), u >>= 8;
    return o + 16;
}
static char* clna_rstr(char* o, const char* s) {
    while (*s) *o++ = *s++;
    return o;
}
#ifdef CLNA_HEAD
static char* clna_rf32(char* o, float d) {  // raw IEEE-754 single bits, 8 hex digits
    std::uint32_t u;
    __builtin_memcpy(&u, &d, sizeof u);
    for (int i = 3; i >= 0; --i) __builtin_memcpy(o + 2 * i, &clna_hex2.t[u & 255u], 2), u >>= 8;
    return o + 8;
}
static char* clna_rh16(char* o, const std::int16_t* v, int n) {  // int16 array as one token, 4 hex digits each (two's complement)
    for (int i = 0; i < n; ++i, o += 4) {
        const unsigned u = static_cast<std::uint16_t>(v[i]);
        const std::uint32_t w = clna_hex2.t[u >> 8] | (static_cast<std::uint32_t>(clna_hex2.t[u & 255u]) << 16);
        __builtin_memcpy(o, &w, 4);
    }
    return o;
}
static char* clna_rh8(char* o, const int* v, int n) {  // values 0..255 as one token, 2 hex digits each
    for (int i = 0; i < n; ++i, o += 2) __builtin_memcpy(o, &clna_hex2.t[v[i] & 255], 2);
    return o;
}
#endif
#endif
// Base64 into a static buffer: logging must not touch the heap (allocator state is shared with charged code).
static const char* clna_b64(const std::int16_t* p, int n) {
    static char out[4 * ((2 * 828 + 2) / 3) + 1];
    static const char* T = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    const auto* b = reinterpret_cast<const unsigned char*>(p);
    const int len = 2 * n;
    int o = 0;
    for (int i = 0; i < len; i += 3) {
        const unsigned v = (b[i] << 16) | ((i + 1 < len ? b[i + 1] : 0) << 8) | (i + 2 < len ? b[i + 2] : 0);
        out[o++] = T[(v >> 18) & 63];
        out[o++] = T[(v >> 12) & 63];
        out[o++] = i + 1 < len ? T[(v >> 6) & 63] : '=';
        out[o++] = i + 2 < len ? T[v & 63] : '=';
    }
    out[o] = 0;
    return out;
}
static double clna_u01() {
    clna_rng += 0x9E3779B97F4A7C15ull;
    std::uint64_t z = clna_rng;
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
    z ^= z >> 31;
    return static_cast<double>(z >> 11) * (1.0 / 9007199254740992.0);
}
#if CLNA_FPROF
// Fuel profile of the release logger (measurement builds only): each CNR1 row ends " F <compute> <log>", compute =
// this decision's mixture work, log = what the logging rows (CNR1 + CNX3) cost since the previous CNR1 row, write = the
// fputs part of log.
static std::uint64_t clna_flog = 0, clna_fwr = 0;
#endif
#ifdef CLNA_HEAD
// CNR3 row of the decision just stashed in clna_row (format: clna_explore). Written at the decision itself: deferring
// it to the end of the turn moved ~5.6k past the fuel guard and raised fuel-outs (979 vs 688 on the 30 dev cells).
static void clna_emit_row() {
    if (clna_row.pending) {
        const ClnaRow& w = clna_row;
        clna_row.pending = false;
        char* o = clna_rstr(clna_rbuf, "CNR3 ");
        o = clna_rint(o, w.round), *o++ = ' ', o = clna_rint(o, w.slot), *o++ = ' ', o = clna_rint(o, w.id);
        *o++ = ' ', o = clna_rint(o, w.index), *o++ = ' ', o = clna_rint(o, w.ref), *o++ = ' ', o = clna_rint(o, w.chosen);
        *o++ = ' ', o = clna_rint(o, w.v92), *o++ = ' ', o = clna_rint(o, w.nn), *o++ = ' ', o = clna_rint(o, w.n);
        *o++ = ' ', o = clna_rint(o, w.pub), *o++ = ' ', o = clna_rint(o, w.ctx), *o++ = ' ', o = clna_rint(o, w.nu);
        *o++ = ' ', o = clna_rdbl(o, w.alpha), *o++ = ' ', o = clna_rdbl(o, w.p);
        *o++ = ' ', o = clna_rh8(o, w.ug, w.nu);
        *o++ = ' ', o = clna_rh8(o, w.map, w.n + 1);
        *o++ = ' ';
        for (int j = 0; j <= w.n; ++j) o = clna_rf32(o, w.nat[j]);
        const auto cap = [&] { return sizeof clna_rbuf - static_cast<std::size_t>(o - clna_rbuf); };
        *o++ = ' ', o += jd_codec::hex_simd(reinterpret_cast<const std::uint8_t*>(clna_act.x), 2 * 160, o, cap());
        *o++ = ' ', o += jd_codec::hex_simd(reinterpret_cast<const std::uint8_t*>(&w.ec[0][0]), 2 * 16 * w.n, o, cap());
        *o++ = ' ', o += jd_codec::hex_simd(reinterpret_cast<const std::uint8_t*>(&w.ft[0][0]), 2 * 4 * w.n, o, cap());
#if CLNA_FPROF
        // measurement builds: " F <before head> <head rest> <fuel left after head> <stash>"
        o = clna_rstr(o, " F "), o = clna_rint(o, w.f_before), *o++ = ' ', o = clna_rint(o, w.f_head), *o++ = ' ';
        o = clna_rint(o, w.f_left), *o++ = ' ', o = clna_rint(o, w.f_stash);
#endif
        *o++ = '\n';
        std::fwrite(clna_rbuf, 1, static_cast<std::size_t>(o - clna_rbuf), stdout);
    }
}
#endif
int Bot::clna_explore(int v92g, int ng) {
#if CLNA_FPROF
    const std::uint64_t clna_f0 = bc::fuel_remaining();
#endif
    if (!clna_rng) clna_rng = static_cast<std::uint64_t>(CLNA_SEED) * 0x100000001B3ull ^ (static_cast<std::uint64_t>(my_id) << 17);
    const int ref = nn_ens_keep(v92g, ng) ? v92g : ng;
    int pg[13];
    double lg[13];
    int m = 0;
    for (int i = 0; i < nn_pub.n && i < 12; ++i) pg[m] = nn_pub.eg[i], lg[m++] = nn_pub.es[i];
    pg[m] = v92g, lg[m++] = nn_pub.far;  // the far slot: outside the scored groups, falls back to v92
#ifdef CLNA_HEAD
#if !CLNA_RLOG
#error "CLNA_HEAD needs the release logger (CLNA_RLOG 1)"
#endif
    {
        // Target head (clna-head-abi-v1, JOHNDOE's jd_head): pi = (1 - alpha(h)) [ref] + alpha(h) softmax(native + residual(h))
        // over the n scored slots + far, merged per physical group (groups in first-slot order, as the eps policy).
        // h = relu(context(x)) of the context in use comes ready from spare end-of-turn fuel (clna_stage). Skips (the
        // reference acts, no stochastic row): 1 camp snapshot not paired with nn_pub, 2 reference outside the slots, 3 not
        // enough fuel left for the rest of the head + log + v92's own work, 4 no completed context yet.
        const int n = nn_pub.n;
        int ug[14], map[11], nu = 0, kr = 0;
        for (int j = 0; j < m && j < 11; ++j) {
            int k = 0;
            while (k < nu && ug[k] != pg[j]) ++k;
            if (k == nu) ug[nu++] = pg[j];
            map[j] = k;
        }
        while (kr < nu && ug[kr] != ref) ++kr;
        const int why = (clna_snap.at != nn_pub.at || clna_snap.n != n || n > 10 || m != n + 1) ? 1 : kr == nu ? 2
                        : bc::fuel_remaining() < static_cast<std::uint64_t>(CLNA_HEAD_MIN) ? 3 : !clna_act.ready ? 4 : 0;
        if (why) {
            clna_round = -1;
            ++clna_skips[why - 1];  // reported at the end of the turn (CNK, clna_turn_end)
            return ref;
        }
        float cf[10 * 16], ff[10 * 4], nat[11];
        bool val[11];
        for (int k = 0; k < n; ++k) {
            for (int j = 0; j < 16; ++j) cf[k * 16 + j] = static_cast<float>(clna_snap.ec[k][j]) * (1.0f / 1024.0f);
            const std::int16_t* t = clna_snap.ft[k];
            ff[k * 4 + 0] = static_cast<float>(t[0] < 0 ? 256 : std::min<int>(t[0], 256)) * (1.0f / 32.0f);
            ff[k * 4 + 1] = static_cast<float>(std::clamp<int>(t[1], 0, 8)) * 0.25f;
            ff[k * 4 + 2] = static_cast<float>(std::clamp<int>(t[2], 0, 8)) * 0.25f;
            ff[k * 4 + 3] = t[3] ? 1.0f : 0.0f;
            nat[k] = nn_pub.es[k], val[k] = true;
        }
        nat[n] = nn_pub.far, val[n] = true;
        double ph[14], alpha = 0, acc = 0;
#if CLNA_FPROF
        const std::uint64_t clna_h0 = bc::fuel_remaining();
#endif
        clna_head_rest(clna_act, cf, ff, nat, n, val, map, kr, nu, ph, alpha);
#if CLNA_FPROF
        const std::uint64_t clna_h1 = bc::fuel_remaining();
#endif
        const double u = clna_u01();
        int c = nu - 1;
        for (int k = 0; k < nu; ++k) {
            acc += ph[k];
            if (u < acc) {
                c = k;
                break;
            }
        }
        // CNR3 <round> <slot> <id> <index> <ref> <chosen> <v92> <nn> <n> <pub round> <context round> <nu> <alpha:hex64>
        //      <p chosen:hex64> <groups: nu x hex8> <slot->physical: (n+1) x hex8> <native logits: (n+1) x hex32 bits>
        //      <x: 160 int16> <ec: 16n int16> <fields: 4n int16>   (the last three as raw little-endian bytes in hex,
        //      jd_codec::hex_simd; groups < 256 always: World groups are at most ~51)
        // stash the row, then write it (clna_emit_row)
        ++clna_index;
        clna_round = round;
        ClnaRow& w = clna_row;
        w = ClnaRow{};
        w.pending = true, w.round = round, w.slot = slot, w.id = static_cast<long>(my_id), w.index = clna_index;
        w.ref = ref, w.chosen = ug[c], w.v92 = v92g, w.nn = ng, w.n = n, w.pub = nn_pub.at, w.ctx = clna_act.at, w.nu = nu;
        w.alpha = alpha, w.p = ph[c];
        std::copy(ug, ug + nu, w.ug), std::copy(map, map + n + 1, w.map), std::copy(nat, nat + n + 1, w.nat);
        std::copy(&clna_snap.ec[0][0], &clna_snap.ec[0][0] + 16 * n, &w.ec[0][0]);
        std::copy(&clna_snap.ft[0][0], &clna_snap.ft[0][0] + 4 * n, &w.ft[0][0]);
#if CLNA_FPROF
        w.f_before = static_cast<long>(clna_f0 - clna_h0), w.f_head = static_cast<long>(clna_h0 - clna_h1);
        w.f_left = static_cast<long>(clna_h1), w.f_stash = static_cast<long>(clna_h1 - bc::fuel_remaining());
#endif
        clna_emit_row();
        return ug[c];
    }
#endif
    double mx = -1e300;
    for (int i = 0; i < m; ++i) mx = lg[i] > mx ? lg[i] : mx;
    int ug[14];
    double uq[14];
    int nu = 0;
    double z = 0, ex[13];
    for (int i = 0; i < m; ++i) ex[i] = std::exp(lg[i] - mx), z += ex[i];  // (fuel) each exp once; same values
    for (int i = 0; i < m; ++i) {
        const double q = ex[i] / z;
        int k = 0;
        while (k < nu && ug[k] != pg[i]) ++k;
        if (k == nu) ug[nu] = pg[i], uq[nu++] = 0.0;
        uq[k] += q;
    }
    int kr = 0;
    while (kr < nu && ug[kr] != ref) ++kr;
    if (kr == nu) ug[nu] = ref, uq[nu++] = 0.0;
    // Learnable gate alpha(h) over explicit legal inputs (clna_gate.h); the default weights give alpha = CLNA_EPS.
    double gx[clna_gate::kN];
    {
        double qmax = 0, ent = 0;
        for (int k = 0; k < nu; ++k) {
            qmax = uq[k] > qmax ? uq[k] : qmax;
            if (uq[k] > 0) ent -= uq[k] * std::log(uq[k]);
        }
        gx[0] = uq[kr];
        gx[1] = qmax;
        gx[2] = nu > 1 ? ent / std::log(static_cast<double>(nu)) : 0.0;
        gx[3] = static_cast<double>(round) / 2000.0;
        gx[4] = static_cast<double>(gems) / 100.0;
        gx[5] = max_hp > 0 ? static_cast<double>(hp) / static_cast<double>(max_hp) : 0.0;
        gx[6] = static_cast<double>(w.enemies.size() < 6 ? w.enemies.size() : 6) / 6.0;
        gx[7] = static_cast<double>(nu) / 14.0;
    }
    double gz = clna_gate::kBias;
    for (int i = 0; i < clna_gate::kN; ++i) gz += static_cast<double>(clna_gate::kW[i]) * gx[i];
    const double eps = 1.0 / (1.0 + std::exp(-gz));  // alpha(h)
    double p[14], acc = 0;
    for (int k = 0; k < nu; ++k) p[k] = eps * uq[k] + (ug[k] == ref ? 1.0 - eps : 0.0);
    const double u = clna_u01();
    int c = nu - 1;
    for (int k = 0; k < nu; ++k) {
        acc += p[k];
        if (u < acc) {
            c = k;
            break;
        }
    }
#if CLNA_RLOG
    // CNR1 <round> <slot> <id> <index> <ref> <chosen> <alpha:hex64> <v92> <nn> <k> {<group>:<q hex64>}*k {<x hex64>}*8
    // (old logp is reconstructed offline from alpha, q, ref and the chosen group)
#if CLNA_FPROF
    const std::uint64_t clna_f1 = bc::fuel_remaining();
#endif
    ++clna_index;
    clna_round = round;
    char* o = clna_rstr(clna_rbuf, "CNR1 ");
    o = clna_rint(o, round), *o++ = ' ', o = clna_rint(o, slot), *o++ = ' ', o = clna_rint(o, static_cast<long>(my_id));
    *o++ = ' ', o = clna_rint(o, clna_index), *o++ = ' ', o = clna_rint(o, ref), *o++ = ' ', o = clna_rint(o, ug[c]);
    *o++ = ' ', o = clna_rdbl(o, eps), *o++ = ' ', o = clna_rint(o, v92g), *o++ = ' ', o = clna_rint(o, ng);
    *o++ = ' ', o = clna_rint(o, nu);
    for (int k = 0; k < nu; ++k) *o++ = ' ', o = clna_rint(o, ug[k]), *o++ = ':', o = clna_rdbl(o, uq[k]);
    for (int i = 0; i < clna_gate::kN; ++i) *o++ = ' ', o = clna_rdbl(o, gx[i]);
#if CLNA_FPROF
    o = clna_rstr(o, " F "), o = clna_rint(o, static_cast<long>(clna_f0 - clna_f1)), *o++ = ' ';
    o = clna_rint(o, static_cast<long>(clna_flog)), *o++ = ' ', o = clna_rint(o, static_cast<long>(clna_fwr));
    clna_flog = clna_fwr = 0;
#endif
    *o++ = '\n';
#if CLNA_FPROF
    const std::uint64_t clna_f2 = bc::fuel_remaining();
#endif
    std::fwrite(clna_rbuf, 1, static_cast<std::size_t>(o - clna_rbuf), stdout);
#if CLNA_FPROF
    const std::uint64_t clna_f3 = bc::fuel_remaining();
    clna_flog += clna_f1 - clna_f3, clna_fwr += clna_f2 - clna_f3;
#endif
    return ug[c];
#endif
    // Everything below that only serves the log runs inside debug_block: charged log-only work made debug and
    // release play different games (JOHNDOE #63-#65).
    debug_block({
        const double logp = std::log(p[c]);
        clna_round = round;
        ++clna_index;
        // CNA2 <cached_round> <engine_round> <slot> <id> <index> <ref> <chosen> <logp> <alpha> <v92> <nn> <k> {g:q}*k
        //      <gate x0..x7> <b64 features>   (round-trip %.17g for probabilities, logp and alpha)
        std::printf("CNA2 %d %u %d %u %d %d %d %.17g %.17g %d %d %d", round, bc::round_number(), slot, my_id, clna_index, ref,
                    ug[c], logp, eps, v92g, ng, nu);
        for (int k = 0; k < nu; ++k) std::printf(" %d:%.17g", ug[k], uq[k]);
        for (int i = 0; i < clna_gate::kN; ++i) std::printf(" %.17g", gx[i]);
        std::printf(" %s\n", clna_b64(nn_lf, kNF));
    });
    return ug[c];
}
#ifdef CLNA_HEAD
// CNX3 rows wait in a small queue and are written only with a safe fuel margin (clna_flush): an unguarded end-of-turn
// write that runs out suspends the bot into the next turn, which then ends unplayed. Order is kept; rows pair by
// (body, decision index), so writing one later is harmless. A full queue is written regardless.
struct ClnaX3 { int round, slot, index, group; long id; };
static ClnaX3 clna_xq[8];
static int clna_xn = 0;
static void clna_flush(bool force) {
    int i = 0;
    for (; i < clna_xn && (force || bc::fuel_remaining() > 4000u); ++i) {
        const ClnaX3& x = clna_xq[i];
        char* o = clna_rstr(clna_rbuf, "CNX3 ");
        o = clna_rint(o, x.round), *o++ = ' ', o = clna_rint(o, x.slot), *o++ = ' ', o = clna_rint(o, x.id);
        *o++ = ' ', o = clna_rint(o, x.index), *o++ = ' ', o = clna_rint(o, x.group), *o++ = '\n';
        std::fwrite(clna_rbuf, 1, static_cast<std::size_t>(o - clna_rbuf), stdout);
    }
    for (int j = i; j < clna_xn; ++j) clna_xq[j - i] = clna_xq[j];
    clna_xn -= i;
}
#endif
void Bot::clna_end() {
#ifdef CLNA_HEAD
    if (clna_round == round) {
        clna_round = -1;
        if (clna_xn == 8) clna_flush(true);
        clna_xq[clna_xn++] = ClnaX3{round, slot, clna_index, target_group, static_cast<long>(my_id)};
    }
    clna_flush(false);
    return;
#endif
#if CLNA_RLOG
    if (clna_round == round) {  // CNX3 <round> <slot> <id> <index> <executed group>
        clna_round = -1;
#if CLNA_FPROF
        const std::uint64_t clna_f1 = bc::fuel_remaining();
#endif
        char* o = clna_rstr(clna_rbuf, "CNX3 ");
        o = clna_rint(o, round), *o++ = ' ', o = clna_rint(o, slot), *o++ = ' ', o = clna_rint(o, static_cast<long>(my_id));
        *o++ = ' ', o = clna_rint(o, clna_index), *o++ = ' ', o = clna_rint(o, target_group), *o++ = '\n';
#if CLNA_FPROF
        const std::uint64_t clna_f2 = bc::fuel_remaining();
#endif
        std::fwrite(clna_rbuf, 1, static_cast<std::size_t>(o - clna_rbuf), stdout);
#if CLNA_FPROF
        const std::uint64_t clna_f3 = bc::fuel_remaining();
        clna_flog += clna_f1 - clna_f3, clna_fwr += clna_f2 - clna_f3;
#endif
    }
    return;
#endif
    debug_block({
        if (clna_round == round) {
            clna_round = -1;
            std::printf("CNX2 %d %u %d %u %d %d\n", round, bc::round_number(), slot, my_id, clna_index, target_group);
        }
    });
}
void Bot::clna_skip(int v92g, int ng) {
    debug_block({ std::printf("CNS1 %d %d %u %d %d %d\n", round, slot, my_id, v92g, ng, nn_stay ? 1 : 0); });
}
#ifdef CLNA_HEAD
void Bot::clna_turn_end() {
    // spare fuel after everything else this turn: advance the context projection of the current snapshot
#if CLNA_FPROF
    const std::uint64_t f0 = bc::fuel_remaining();
    const int d0 = clna_pend.at >= 0 ? clna_pend.done : -16;
#endif
    const auto r0 = bc::round_number();
    clna_flush(false);  // queued CNX3 rows first
    // (the last stage also computes the h-only terms, ~8k more)
    while (clna_pend.at >= 0 && bc::round_number() == r0 &&
           bc::fuel_remaining() > static_cast<std::uint64_t>(CLNA_STAGE_MIN) + (clna_pend.done == 144 ? 9000u : 0u))
        clna_stage();
    // skips since the last CNK row, one row at the end of a turn instead of one per skip on the decision path:
    // CNK <round> <slot> <id> <unpaired> <reference outside> <fuel guard> <no context>. Only with a safe margin left:
    // nn_turn_end spends down to its 1k reserve, and a write that runs out suspends the bot into the next turn, which
    // then ends unplayed (an unguarded CNK raised fuel-outs 461 -> ~1100 on the 30 dev cells); else the counts carry over.
    if ((clna_skips[0] | clna_skips[1] | clna_skips[2] | clna_skips[3]) && bc::round_number() == r0 &&
        bc::fuel_remaining() > 4000u) {
        char* k = clna_rstr(clna_rbuf, "CNK ");
        k = clna_rint(k, round), *k++ = ' ', k = clna_rint(k, slot), *k++ = ' ', k = clna_rint(k, static_cast<long>(my_id));
        for (int i = 0; i < 4; ++i) *k++ = ' ', k = clna_rint(k, clna_skips[i]), clna_skips[i] = 0;
        *k++ = '\n';
        std::fwrite(clna_rbuf, 1, static_cast<std::size_t>(k - clna_rbuf), stdout);
    }
#if CLNA_FPROF
    // measurement builds: CNF <round> <slot> <fuel left before> <after> <stages before> <after> <context in use round>
    char* o = clna_rstr(clna_rbuf, "CNF ");
    o = clna_rint(o, round), *o++ = ' ', o = clna_rint(o, slot), *o++ = ' ', o = clna_rint(o, static_cast<long>(f0));
    *o++ = ' ', o = clna_rint(o, static_cast<long>(bc::fuel_remaining())), *o++ = ' ', o = clna_rint(o, d0 / 16);
    *o++ = ' ', o = clna_rint(o, clna_pend.at >= 0 ? clna_pend.done / 16 : 10), *o++ = ' ', o = clna_rint(o, clna_act.at);
    *o++ = ' ', o = clna_rint(o, clna_memo_hits), *o++ = ' ', o = clna_rint(o, clna_memo_misses);  // (cumulative)
    *o++ = '\n';
    std::fwrite(clna_rbuf, 1, static_cast<std::size_t>(o - clna_rbuf), stdout);
#endif
}
#endif
#endif
#endif
// Neural bot (A2_NN bits: 1 the student picks the farming target group, 2 it decides when to bank).
void Bot::nn_decide() {
    nn_group = -1, nn_beh = -1;
    nn_v92best = target_group; // v92 keeps its target unless farm() chooses again
    if (!inited) return;
    nn_track();
#if A2_NN_FAST && !defined(A2_NN_RL)
    // apply the decision in force: the best target that is still worth going to (A2_NN_VALID), and the bank gate
    auto apply_net = [&] {
        if (round - nn_pub.at > A2_NN_TTL) return;
        for (int r = 0; r < 4 && nn_pub.rank[r] >= 0; ++r) {
#if A2_NN_VALID
            if (w.groups[static_cast<std::size_t>(nn_pub.rank[r])].state == GroupState::respawning &&
                nn_pub.st[r] != static_cast<int>(GroupState::respawning))
                continue;
#endif
            nn_group = nn_pub.rank[r];
            break;
        }
#if A2_NN_BEH == 2
        nn_beh = nn_pub.beh;
#elif A2_NN_BEH == 1
        nn_beh = nn_pub.beh == 1 ? 1 : -1;
#elif A2_NN_BEH == 3 && defined(A2_NN_LIVE) && A2_NN_LIVE
        // E123: the bank gate of the last summary (at most A2_NN_ZFRESH rounds old), held: "bank" stays in force until the bag is empty (at most 25
        // rounds); any other answer means no bank until a summary says so; no recent summary: v92 decides.
        static int bank_until = -1;
        const bool recent = nn_lv.z_ok && round - nn_zround <= A2_NN_ZFRESH;
        if (gems <= 0) bank_until = -1;
        if (recent && nn_lv.beh == 1 && gems > 0 && bank_until < round) bank_until = round + 25;
        nn_beh = round <= bank_until ? 1 : recent ? 0 : -1;
#endif
    };
    auto apply = [&] {
        apply_net();
#if defined(A2_NN_DPLAN) && A2_NN_DPLAN
        // the draft turn's opening plan (E122): its current step comes first, unless an enemy is near or health is low (as E62)
        const int plan_g = dplan_group();
        if (plan_g >= 0 && nn_near() > 6 && hp >= max_hp * 0.5f) nn_group = plan_g;
#endif
    };
#if defined(A2_NN_LIVE) && A2_NN_LIVE
    {
        // Real-fuel deployment (E121). Start of the turn, on start-of-turn features as in training: the camps are scored fresh (about
        // 25k), with this turn's own summary of the slow part (trunk, bank gate) if the fuel allows a whole refresh on top of what
        // v92 usually spends afterwards, else the last summary. What does not fit runs by stages at the end of the turn, on
        // what v92 left. Up to 99k a turn (A2_NN_RESERVE). Too little fuel to score camps: the target in force holds. In
        // contact: the decision in force holds, v92's fight code has the fuel. The first turn's spare fuel goes to v92's
        // initialisation and the distance fields. The bank gate applies only while the summary is fresh (a stale gate loses, E121);
        // after that v92 banks.
#ifdef A2_NN_SOT
        // E124 diagnosis at 20M: the plain network at the start of the turn in a LIVE build (same moment as the non-LIVE every-turn bot; only the LIVE patches differ)
        {
            nn_mark = 0, nn_path = 3, nn_round0 = bc::round_number();
            ++nn_live_turns;
            constexpr int kCOffL = kG + kS + kA * kAF + kE * kEF;
            const int near_e = nn_near();
            if (near_e > 6) {
                std::fill(nn_lf, nn_lf + kNF, static_cast<std::int16_t>(0));
                nn_feats_t<kC, kAF>(nn_lf, near_e, 3);
                nn::forward(nn_lf, nn_lo, nn::kHBeh | nn::kHTarget);
#ifdef A2_NN_LJIT
        for (int i = 0; i < kC + 1; ++i) {
            std::uint32_t h = (static_cast<std::uint32_t>(A2_NN_LJIT) * 2654435761u) ^ (static_cast<std::uint32_t>(i) * 40503u) ^
                              (static_cast<std::uint32_t>(round / 8) * 2246822519u) ^ (static_cast<std::uint32_t>(slot) * 97u);
            h = h * 1664525u + 1013904223u, h = h * 1664525u + 1013904223u;
            nn_lo.target[i] += static_cast<float>(A2_NN_LJIT_A) * (static_cast<float>(h >> 8) / 16777216.0f - 0.5f);
        }
#endif
                nn_pub = nn_make_pub(nn_lf, nn_lo.target, kC + 1, kC, kCOffL, -1, round);
            }
            apply();
            return;
        }
#endif
#if defined(A2_NN_NNUE) && !defined(A2_NN_LAZY)
        // E124: the scoring moment matters: the plain network at the start of the turn 62.9% on official maps at 20M (nnd6), in farm() 51-56% (nnd2, nnd3). So at the start of the turn: self + camps
        // (+ enemies in view) fresh, the rest of the network from the kept sums; the other blocks refresh at the end of the turn. In contact the decision in force holds. v92's fuel checks ignore what this spends (nn_spent).
        {
            constexpr int kCOffL = kG + kS + kA * kAF + kE * kEF;
            static bool first_scoring = true;
            nn_mark = 0, nn_path = 3, nn_round0 = bc::round_number();
            const int near_e = nn_near();
            if (near_e <= 6) {
                ++nn_c_contact;
                apply();
                return;
            }
            if (nn_live_turns++ == 0) return;
            nn_kind = w.enemies.empty() ? 0 : near_e > 10 ? 1 : 2;
            const std::uint64_t left = bc::fuel_remaining(), floor_f = std::max<std::uint64_t>(nn_need[nn_kind], 15000) + static_cast<std::uint64_t>(A2_NN_RESERVE);
            if (nn_warm == 2 && left >= nn_est_camps + floor_f) {
                const auto r0 = bc::round_number();
                std::fill(nn_lf + kCOffL, nn_lf + kCOffL + kC * kCF, static_cast<std::int16_t>(0));
                std::fill(nn_lf + kG, nn_lf + kG + kS, static_cast<std::int16_t>(0));
#if A2_FUELLOG
                static std::uint64_t cost[6] = {}, cost_n = 0;
                std::uint64_t cf = bc::fuel_remaining();
                const auto cmark = [&](int i) {
                    const std::uint64_t now = bc::fuel_remaining();
                    cost[i] += cf - now, cf = now;
                };
#else
                const auto cmark = [](int) {};
#endif
                nn_feats_t<kC, kAF>(nn_lf, near_e, 2 | 4);
                cmark(0);
                nn::live_camps(nn_lf, nn_lv, w.groups.size());
                cmark(1);
                nn::live_block(nn_lf, nn_lv, 1);
                cmark(2);
                nn::live_block(nn_lf, nn_lv, 4);
                cmark(3);
                std::uint64_t enemy_used = 0;
                {
                    const std::uint64_t fe0 = bc::fuel_remaining();
                    if (!w.enemies.empty() && fe0 >= nn_xest[0] + 12000 + floor_f) {
                        nn_x_refresh(0);
                        const std::uint64_t fe1 = bc::fuel_remaining();
                        enemy_used = fe0 > fe1 ? fe0 - fe1 : 0;
                    }
                }
                cmark(4);
                if (nn_xdone == 15) {
                    nn::live_top(nn_lv);
#if defined(A2_NN_RLIVE) && A2_NN_RLIVE
                    debug_block({
                        std::copy(nn_lf, nn_lf + kNF, nn_zf);
                        ++nn_zid;
                    });
#endif
                }
                cmark(5);
                if (nn_lv.z_ok) {
                    nn::live_target(nn_lv, nn_lo);
                    nn_pub = nn_make_pub(nn_lf, nn_lo.target, kC + 1, kC, kCOffL, -1, round);
                }
                const std::uint64_t f1 = bc::fuel_remaining();
#if A2_FUELLOG
                if (++cost_n % 200 == 0)
                    std::printf("nncost n %llu feats %llu camps %llu self %llu pool %llu enemy %llu top %llu est %llu need %llu %llu %llu xest %llu %llu %llu %llu\n", static_cast<unsigned long long>(cost_n),
                                static_cast<unsigned long long>(cost[0] / cost_n), static_cast<unsigned long long>(cost[1] / cost_n), static_cast<unsigned long long>(cost[2] / cost_n),
                                static_cast<unsigned long long>(cost[3] / cost_n), static_cast<unsigned long long>(cost[4] / cost_n), static_cast<unsigned long long>(cost[5] / cost_n),
                                static_cast<unsigned long long>(nn_est_camps), static_cast<unsigned long long>(nn_need[0]), static_cast<unsigned long long>(nn_need[1]), static_cast<unsigned long long>(nn_need[2]),
                                static_cast<unsigned long long>(nn_xest[0]), static_cast<unsigned long long>(nn_xest[1]), static_cast<unsigned long long>(nn_xest[2]), static_cast<unsigned long long>(nn_xest[3]));
#endif
                if (bc::round_number() != r0 || f1 > left) {
                    nn_est_camps = std::max(nn_est_camps, std::min<std::uint64_t>(left, 60000)); // (never out of reach)
                } else {
                    const std::uint64_t used = left - f1 - std::min(enemy_used, left - f1);
                    nn_sum_camps += used;
                    if (!first_scoring) nn_est_camps = std::max(used + used / 8, nn_est_camps - nn_est_camps / 32); // (the first carries one-time setup)
                }
                first_scoring = false;
                ++nn_c_camps, nn_path = 1;
            } else {
                nn_est_camps -= nn_est_camps / 16; // (an estimate pushed up by one costly turn must not lock the scoring out)
                ++nn_c_hold, nn_path = 0;
            }
            apply();
            nn_mark = bc::fuel_remaining(), nn_round0 = bc::round_number(), nn_field_fuel = 0;
            nn_spent = left >= nn_mark ? left - nn_mark : 0;
            return;
        }
#endif
#ifdef A2_NN_LAZY
        // E123: the camps are scored in farm(), after v92's own choice (nn_lazy_score): v92 has already spent what it needs by then. Here, only when a new refresh of the slow part
        // is due and no enemy is near: the features behind it, as they are at the start of a turn (v92's fuel checks ignore this, as nn_spent says).
        nn_mark = 0, nn_path = 3, nn_round0 = bc::round_number();
#ifdef A2_NN_NNUE
        ++nn_live_turns;
#ifdef A2_NN_SGAUTO
        nn_sg_need = nn_warm == 2 ? nn_est_camps + std::max<std::uint64_t>(nn_need[w.enemies.empty() ? 0 : nn_near() > 10 ? 1 : 2], A2_NN_LAZY_FLOOR) + 2000 : 0;
#endif
        return;
#endif
        if (nn_live_turns++ >= 1 && nn_warm == 2 && nn_zstage == 0) {
            const int near_e = nn_near();
            if (near_e > 10) {
                constexpr int kCOffL = kG + kS + kA * kAF + kE * kEF;
                const std::uint64_t f0 = bc::fuel_remaining();
                std::fill(nn_lf, nn_lf + kCOffL, static_cast<std::int16_t>(0));
                std::fill(nn_lf + kCOffL + kC * kCF, nn_lf + kNF, static_cast<std::int16_t>(0));
                nn_feats_t<kC, kAF>(nn_lf, near_e, 1);
                nn_zstage = 1, nn_zstart = round;
                const std::uint64_t f1 = bc::fuel_remaining();
                nn_spent = f0 > f1 ? f0 - f1 : 0;
            }
        }
        return;
#endif
        static bool first_camps = true;
        constexpr int kCOffL = kG + kS + kA * kAF + kE * kEF;
        nn_mark = 0, nn_path = 3, nn_round0 = bc::round_number();
        const int gate = round - nn_zround <= A2_NN_ZFRESH ? nn_lv.beh : -1;
        const int near_e = nn_near();
        if (near_e <= 6) {
            ++nn_c_contact;
            nn_pub.beh = gate;
            apply();
            return;
        }
        if (nn_live_turns++ == 0) return;
        nn_kind = w.enemies.empty() ? 0 : near_e > 10 ? 1 : 2;
        // (with no target in force the measured need includes v92's own target search, which a network target would skip: without
        // this cap the gate can stay shut for a whole game)
        // v92's fuel checks ignore what the network spends here (nn_spent, nn_mkbot.py), so it always gets at least a walk's worth.
        const std::uint64_t left = bc::fuel_remaining(),
                            floor_f = std::max<std::uint64_t>(nn_pub.rank[0] < 0 ? std::min<std::uint64_t>(nn_need[nn_kind], 20000) : nn_need[nn_kind], 15000) +
                                      static_cast<std::uint64_t>(A2_NN_RESERVE);
        if (nn_warm == 2 && left >= nn_est_camps + floor_f) {
            if (A2_NN_ZSTART) nn_run_stages(nn_est_camps + floor_f, round); // a refresh under way finishes first if this turn can afford it
            const auto r0 = bc::round_number();
            const std::uint64_t f0 = bc::fuel_remaining();
            const bool start = nn_zstage == 0; // a new refresh of the slow part takes all the features of this turn
            if (start) std::fill(nn_lf, nn_lf + kNF, static_cast<std::int16_t>(0));
            else std::fill(nn_lf + kCOffL, nn_lf + kCOffL + kC * kCF, static_cast<std::int16_t>(0));
            nn_feats_t<kC, kAF>(nn_lf, near_e, start ? 3 : 2);
            nn::live_camps(nn_lf, nn_lv, w.groups.size());
            const std::uint64_t f1 = bc::fuel_remaining();
            if (start) nn_zstage = 1, nn_zstart = round;
            if (A2_NN_ZSTART) nn_run_stages(floor_f + 2000, round); // a whole new refresh now, if it fits: this decision then uses this turn's summary
            const int gate_now = round - nn_zround <= A2_NN_ZFRESH ? nn_lv.beh : -1;
            if (nn_lv.z_ok) {
                nn::live_target(nn_lv, nn_lo);
#if defined(A2_NN_RLIVE) && A2_NN_RLIVE && !defined(A2_NN_ENS)
                int rl_a = -1;
                float rl_lp = 0.0f;
                debug_block({
                    rl_a = nn_sample(nn_lo.target, kC + 1, rl_lp, static_cast<std::uint64_t>(my_id) + 1);
                    nn_lo.target[rl_a] = 1e9f; // the sampled slot ranks first
                });
#endif
                nn_pub = nn_make_pub(nn_lf, nn_lo.target, kC + 1, kC, kCOffL, gate_now, round);
#if defined(A2_NN_RLIVE) && A2_NN_RLIVE && !defined(A2_NN_ENS)
                debug_block({
                    const bool chg = nn_pub.rank[0] != target_group;
                    if (chg || nn_rand(0) % A2_NN_RL_KEEP == 0) {
                        if (nn_zid_printed != nn_zid) {
                            std::printf("NRZ %d %s\n", nn_zid, b64(nn_zf, kNF).c_str());
                            nn_zid_printed = nn_zid;
                        }
                        // this turn's whole state: the camps as scored, the rest computed here (no fuel in this block)
                        static std::int16_t xn[kNF];
                        std::fill(xn, xn + kNF, static_cast<std::int16_t>(0));
                        nn_feats_t<kC, kAF>(xn, near_e, 1);
                        std::copy(nn_lf + kCOffL, nn_lf + kCOffL + kC * kCF, xn + kCOffL);
                        std::printf("NRL %d %d %d %.5f %d %d %s\n", round, slot, rl_a, rl_lp, chg ? 1 : 0, nn_zid, b64(xn, kNF).c_str());
                    }
                });
#endif
            }
            if (bc::round_number() != r0 || f1 > f0) {
                nn_est_camps = std::max(nn_est_camps, std::min<std::uint64_t>(f0, 45000)); // (never out of reach)
            } else {
                const std::uint64_t used = f0 - f1 + 1500; // (with the target scores)
                nn_sum_camps += used;
                if (!first_camps) nn_est_camps = std::max(used + used / 8, nn_est_camps - nn_est_camps / 32); // (the first carries one-time setup)
            }
            first_camps = false;
            ++nn_c_camps, nn_path = 1;
        } else {
            nn_pub.beh = gate;
            ++nn_c_hold, nn_path = 0;
        }
        apply();
        nn_mark = bc::fuel_remaining(), nn_round0 = bc::round_number(), nn_field_fuel = 0;
        nn_spent = left >= nn_mark ? left - nn_mark : 0;
        return;
    }
#endif
#if defined(A2_NN_PIPE) && A2_NN_PIPE
    // pipelined deployment: the decision in force was computed by nn_pipe_step() from the last turns' spare fuel
    apply();
    return;
#endif
    // deployment: in contact v92's fight code decides and needs the fuel - no network this turn (A2_NN_CONTACT=1: run
    // it anyway; E120 at 20M fuel: ladder 59 vs 61 / 140, pool-test 170 vs 170 / 300, so skipping costs nothing).
    // A2_NN_CHOLD=1 keeps the decision in force during contact instead of handing it back to v92 (pool-test 183 / 300).
#if defined(A2_NN_EVERY) && A2_NN_EVERY > 1
    // pipelined deployment, simulated (E120): the network runs on every A2_NN_EVERY-th network turn of this champion and
    // its decision takes effect A2_NN_LAG turns later (as if computed over several turns' spare fuel); until then the
    // decision in force holds
    static int nn_tick = 0, nn_pend_at = -1;
    static NNPub nn_pend;
    if (nn_pend_at >= 0 && round >= nn_pend_at) nn_pub = nn_pend, nn_pend_at = -1;
#endif
#if !defined(A2_NN_CONTACT) || !A2_NN_CONTACT
    if (nn_near() <= 6) {
#if defined(A2_NN_CHOLD) && A2_NN_CHOLD
        apply();
#endif
        return;
    }
#endif
#if defined(A2_NN_EVERY) && A2_NN_EVERY > 1
    if (nn_tick++ % A2_NN_EVERY != 0) {
        apply();
        return;
    }
#endif
#if defined(A2_NN_EVENT) && A2_NN_EVENT > 0
    // event-driven deployment, simulated (E120): the network runs only when no target is in force, when the target in
    // force has finished, or every A2_NN_EVENT rounds; in between the decision in force holds
    {
        const int g0 = nn_pub.rank[0];
        const bool need = g0 < 0 || round - nn_pub.at >= A2_NN_EVENT ||
                          (w.groups[static_cast<std::size_t>(g0)].state == GroupState::respawning &&
                           nn_pub.st[0] != static_cast<int>(GroupState::respawning));
        if (!need) {
            apply();
            return;
        }
    }
#endif
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
#if defined(A2_NN_ZMASK) && !defined(A2_NN_RL)
    {
        // E123, simulated at 20M fuel: an NNUE-like deployment. The blocks in A2_NN_ZMASK (1 global, 2 self, 4 allies, 8 enemies, 16 camps, 32 altars) are fresh every turn; the others are
        // taken every A2_NN_ZSLOWN network turns and take effect A2_NN_ZSLOWN - 1 turns later, as if refreshed by stages on spare fuel.
        static std::int16_t cur[kNFa], pend[kNFa];
        static int tick = 0;
        static bool have = false;
        const int t = tick++ % A2_NN_ZSLOWN;
        if (t == 0) std::copy(f, f + kNFa, pend);
        if (!have || t == A2_NN_ZSLOWN - 1) std::copy(pend, pend + kNFa, cur), have = true;
        const auto keep = [&](int off, int len, int bit) {
            if (!(A2_NN_ZMASK & bit)) std::copy(cur + off, cur + off + len, f + off);
        };
        keep(0, kG, 1), keep(kG, kS, 2), keep(kG + kS, kA * kAF, 4), keep(kG + kS + kA * kAF, kE * kEF, 8), keep(kCOff, NCt * kCF, 16), keep(kCOff + NCt * kCF, kL * kLF, 32);
    }
#endif
    nn::Out o;
#if defined(A2_NN_ZEVERY) && A2_NN_ZEVERY > 1 && A2_NN_FAST && !defined(A2_NN_RL)
    {
        // two-timescale deployment, simulated (E120): the trunk (the slow summary of the situation, most of the cost) runs
        // on every A2_NN_ZEVERY-th network turn and takes effect A2_NN_ZLAG turns later; the camp encoder and the target
        // pointer run on every turn's fresh features with the summary in force. The bank gate comes with the summary.
        static int z_tick = 0, z_at = -1, z_beh = -1, z_beh_pend = -1;
        static float z_cur[nnw::kTrunk], z_pend[nnw::kTrunk];
        static bool z_ok = false;
        if (z_at >= 0 && round >= z_at) {
            std::copy(z_pend, z_pend + nnw::kTrunk, z_cur);
            z_beh = z_beh_pend, z_ok = true, z_at = -1;
        }
        if (z_tick++ % A2_NN_ZEVERY == 0) {
            nn::forward(f, o, nn::kHBeh, z_pend);
            z_beh_pend = nn::argmax(o.behaviour), z_at = round + A2_NN_ZLAG;
        }
        if (!z_ok) return; // v92 decides until the first summary is in force
        nn::target_fresh(f, z_cur, o);
        nn_pub = nn_make_pub(f, o.target, NCt + 1, NCt, kCOff, z_beh, round);
        apply();
        return;
    }
#endif
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
#ifdef A2_NN_LJIT
        // E123: tiny seeded noise on the target logits (seed A2_NN_LJIT, total width A2_NN_LJIT_A): how much of a bot's score hangs on its exact game trajectory?
        for (int i = 0; i < NCt + 1; ++i) {
            std::uint32_t h = (static_cast<std::uint32_t>(A2_NN_LJIT) * 2654435761u) ^ (static_cast<std::uint32_t>(i) * 40503u) ^
                              (static_cast<std::uint32_t>(round / 8) * 2246822519u) ^ (static_cast<std::uint32_t>(slot) * 97u);
            h = h * 1664525u + 1013904223u, h = h * 1664525u + 1013904223u;
            o.target[i] += static_cast<float>(A2_NN_LJIT_A) * (static_cast<float>(h >> 8) / 16777216.0f - 0.5f);
        }
#endif
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
#ifdef A2_NN_ENSLOG
    std::copy(f, f + kNFa, nn_ef);
#endif
#if A2_NN_FAST && !defined(A2_NN_RL)
    {
        const NNPub made = nn_make_pub(f, o.target, NCt + 1, NCt, kCOff, nn_beh, round);
#if defined(A2_NN_EVERY) && A2_NN_EVERY > 1 && defined(A2_NN_LAG) && A2_NN_LAG > 0
        nn_pend = made, nn_pend_at = round + A2_NN_LAG;
#else
        nn_pub = made;
#endif
        nn_group = -1, nn_beh = -1;
        apply();
    }
#endif
#ifdef A2_NN_DBG
    // every turn up to round A2_NN_DBG: features and logits of the heads every path computes, to compare two builds on one game (E123)
    if (round <= A2_NN_DBG) {
        std::printf("NND %d %d %d %d %s", round, slot, nn_group, nn_beh, b64(f, kNFa).c_str());
        for (int i = 0; i < 8; ++i) std::printf(" %.4f", o.behaviour[i]);
        for (int i = 0; i < NCt + 1; ++i) std::printf(" %.4f", o.target[i]);
        std::printf("\n");
    }
#endif
}

#if defined(A2_NN_LIVE) && A2_NN_LIVE
// End of turn (main.cpp, after play_turn): what v92 spent after the camp scoring (a turn that ran out of fuel closes the gate for
// a while: it counts as having needed more than it had), then the slow part's next stages on what is left.
void Bot::nn_turn_end() {
    nn_spent = 0; // the next turn starts clean (also on turns nn_decide does not run)
#if A2_FUELLOG
    static int logged = -1;
    if ((round % 250 == 0 || round == 50 || round == 100) && round != logged) {
        logged = round;
        std::printf("nnlive round %d fields %d/%d refresh %d camps %d hold %d contact %d need %llu %llu %llu stages %llu %llu %llu %llu avg %llu\n", round,
                    static_cast<int>(w.fields_built), static_cast<int>(w.groups.size()), nn_c_refresh, nn_c_camps, nn_c_hold, nn_c_contact,
                    static_cast<unsigned long long>(nn_need[0]), static_cast<unsigned long long>(nn_need[1]), static_cast<unsigned long long>(nn_need[2]),
                    static_cast<unsigned long long>(nn_est_stage[0]), static_cast<unsigned long long>(nn_est_stage[1]),
                    static_cast<unsigned long long>(nn_est_stage[2] + nn_est_stage[3] + nn_est_stage[4]), static_cast<unsigned long long>(nn_est_stage[5] + nn_est_stage[6]),
                    static_cast<unsigned long long>(nn_sum_camps / std::max(1, nn_c_camps)));
    }
#endif
    // (nn_round0 is 0 on a turn nn_decide did not run: dead)
    const bool over = nn_round0 != 0 && bc::round_number() != nn_round0;
#if A2_FUELLOG
    if (over)
        std::printf("nnover round %d path %d kind %d mark %llu need %llu fields %d enemies %d\n", round, nn_path, nn_kind, static_cast<unsigned long long>(nn_mark),
                    static_cast<unsigned long long>(nn_need[nn_kind]), static_cast<int>(w.fields_built), static_cast<int>(w.enemies.size()));
#endif
    nn_round0 = 0;
    if (nn_mark) {
        const std::uint64_t now = bc::fuel_remaining();
        std::uint64_t used = !over && now <= nn_mark ? nn_mark - now : nn_mark + 20000;
        used -= std::min<std::uint64_t>(used, nn_field_fuel); // v92's optional distance-field building takes what is left: not a need
        nn_field_fuel = 0;
        auto& n = nn_need[nn_kind];
#if defined(A2_NN_LAZY) || defined(A2_NN_NNUE)
        n = std::max(used, n - n / 16);
#else
        n = std::max(used, n - n / 32);
#endif
        nn_mark = 0;
    }
    if (over) return; // already into the next round's fuel
#ifdef A2_NN_NNUE
    const auto nn_round0_end = bc::round_number();
#endif
    // One-time setup after v92's turn, from the first turn's spare fuel if it can, in steps that fit: all features (with the per-group
    // constants), then the first encoding of the nearest camps. The network is live as soon as the first summary is in.
    if (nn_warm < 2 && nn_live_turns >= 1) {
        if (nn_warm == 0 && bc::fuel_remaining() >= 45000 + static_cast<std::uint64_t>(A2_NN_RESERVE)) {
            std::fill(nn_lf, nn_lf + kNF, static_cast<std::int16_t>(0));
            nn_feats_t<kC, kAF>(nn_lf, nn_near(), 3);
            nn_warm = 1;
        }
        if (nn_warm == 1 && bc::fuel_remaining() >= 35000 + static_cast<std::uint64_t>(A2_NN_RESERVE)) {
            nn::live_camps(nn_lf, nn_lv, w.groups.size());
#ifndef A2_NN_NNUE
            nn_zstage = 1, nn_zstart = round;
#endif
            nn_warm = 2;
        }
    }
#ifdef A2_NN_FIELDS_FIRST
    if (!w.fields_ready()) return;
#endif
#if defined(A2_NN_NNUE) && defined(A2_NN_Q16) && A2_NN_Q16
    {
        static int rb = 0;
        if (++rb >= 128 && nn_lv.x_ok && bc::fuel_remaining() >= 16000 + static_cast<std::uint64_t>(A2_NN_RESERVE)) {
            nn::live_rebuild(nn_lv);
            rb = 0;
        }
    }
#endif
#ifdef A2_NN_NNUE
    if (nn_warm == 2) {
        for (int n = 0; n < 4; ++n) {
            const int x = nn_xnext;
            if (nn_xround[x] == round) {
                nn_xnext = (x + 1) % 4;
                continue;
            }
            if (bc::fuel_remaining() < nn_xest[x] + static_cast<std::uint64_t>(A2_NN_RESERVE)) {
                nn_xest[x] -= nn_xest[x] / 32;
                break;
            }
            nn_x_refresh(x);
            if (bc::round_number() != nn_round0_end) break;
            nn_xnext = (x + 1) % 4;
        }
    }
    return;
#endif
    nn_run_stages(static_cast<std::uint64_t>(A2_NN_RESERVE), round);
}
#endif

#if defined(A2_NN_PIPE) && A2_NN_PIPE
#ifndef A2_NN_RESERVE
#define A2_NN_RESERVE 5000 // fuel every turn leaves unspent (the user's 2-5k margin against overrunning into the next turn)
#endif
// End of turn (main.cpp, after play_turn): advance the pipelined network with the fuel this turn left. Step 0 takes the
// features (only out of contact), steps 1..6 are nn::pipe_stage 0..5, then the decision is published for the next
// turns. A step starts only if the fuel left covers the most it has cost so far (+1/8) plus A2_NN_RESERVE; the
// starting estimates are the E120 profile's per-stage costs with margin.
void Bot::nn_pipe_step() {
    static nn::Pipe p;
    static std::int16_t pf[kNF] = {};
    static int next = 0;
    // E120 profile (student, A2_NN_FAST): features ~25k, g+s+a ~10k, e+l <= 12k, camp halves ~15k, pool + trunk 0 ~20k,
    // trunk 1 + heads ~16k
    static std::uint64_t est[1 + nn::kPipeStages] = {34000, 13000, 14000, 17000, 17000, 24000, 19000};
    static bool ran[1 + nn::kPipeStages] = {};
    if (!inited) return;
#if A2_FUELLOG
    static int published = 0, last_pub = 0, logged = -1;
    if (round % 250 == 0 && round != logged) {
        logged = round;
        std::printf("nnpipe round %d decisions %d (last at %d) est %llu %llu %llu %llu %llu %llu %llu\n", round, published, last_pub,
                    static_cast<unsigned long long>(est[0]), static_cast<unsigned long long>(est[1]), static_cast<unsigned long long>(est[2]),
                    static_cast<unsigned long long>(est[3]), static_cast<unsigned long long>(est[4]), static_cast<unsigned long long>(est[5]),
                    static_cast<unsigned long long>(est[6]));
    }
#endif
    for (;;) {
        const std::uint64_t left = bc::fuel_remaining();
        if (left < est[next] + static_cast<std::uint64_t>(A2_NN_RESERVE)) return;
        const auto r0 = bc::round_number();
        if (next == 0) {
            if (nn_near() <= 6) return; // no new decision from a fight state
            std::fill(pf, pf + kNF, static_cast<std::int16_t>(0)); // absent entities must read 0, not the last decision's
            nn_feats(pf, nn_near());
        } else {
            nn::pipe_stage(p, pf, next - 1);
        }
        if (bc::round_number() != r0) {
            // the step ran past the end of the turn and finished on the next turn's fuel (that turn's play is lost):
            // it needs more than was left. Its result is still valid, so the pipeline carries on.
            est[next] = std::max(est[next], left + static_cast<std::uint64_t>(A2_NN_RESERVE));
        } else if (ran[next]) {
            const std::uint64_t used = left - bc::fuel_remaining();
            est[next] = std::max(est[next], used + used / 8); // (the first run carries one-time setup: not counted)
        }
        ran[next] = true;
        if (++next == 1 + nn::kPipeStages) {
            next = 0;
#if !defined(A2_NN_PIPE_NOPUB) || !A2_NN_PIPE_NOPUB // (control: compute everything, never act on it)
            nn_pub = nn_make_pub(pf, p.o.target, kC + 1, kC, kG + kS + kA * kAF + kE * kEF, nn::argmax(p.o.behaviour), round);
#endif
#if A2_FUELLOG
            ++published, last_pub = round;
#endif
            return; // at most one decision per turn
        }
    }
}
#endif

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
