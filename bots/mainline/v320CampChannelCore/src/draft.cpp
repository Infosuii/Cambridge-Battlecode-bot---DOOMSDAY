#include "a2stack.h"
#include "neural_policy.h"
// Draft: farming speed first, then durability. Both teams may own the same champion.
#include "draft.h"
#include "common.h"
#include "lab.h"
#include "strategy.h"
#include "mapplan.h"
#include <cstdio>

#define APEX_DRAFT 6

using cd = bc::champion_draft;
namespace {
// Candidate priority lists; tests pick the preset (see docs/MASTER_PLAN.md, draft results).
constexpr cd kPresets[][11] = {
    {cd::vendetta, cd::varg, cd::cassi_and_issac, cd::tavi, cd::stellar, cd::ryth, cd::marcella, cd::ren,
        cd::vesper_vale, cd::willow, cd::prism},
    {cd::vendetta, cd::varg, cd::ryth, cd::marcella, cd::stellar, cd::tavi, cd::ren, cd::vesper_vale, cd::willow,
        cd::prism, cd::cassi_and_issac},
    {cd::vendetta, cd::varg, cd::stellar, cd::tavi, cd::ryth, cd::marcella, cd::ren, cd::vesper_vale, cd::willow,
        cd::prism, cd::cassi_and_issac},
    {cd::vendetta, cd::varg, cd::marcella, cd::ryth, cd::ren, cd::stellar, cd::tavi, cd::vesper_vale, cd::willow,
        cd::prism, cd::cassi_and_issac},
    {cd::varg, cd::vendetta, cd::willow, cd::ryth, cd::marcella, cd::stellar, cd::tavi, cd::ren, cd::vesper_vale,
        cd::prism, cd::cassi_and_issac},
    {cd::vendetta, cd::varg, cd::vesper_vale, cd::stellar, cd::ryth, cd::tavi, cd::marcella, cd::ren, cd::willow,
        cd::prism, cd::cassi_and_issac},
    // 6: Ren fourth. With dash escapes, Ren beat Marcella as the fourth pick (+59 on 4-champion
    // maps) and Stellar as the fifth (+91 on 5-champion maps).
    {cd::vendetta, cd::varg, cd::ryth, cd::ren, cd::marcella, cd::stellar, cd::tavi, cd::vesper_vale, cd::willow,
        cd::prism, cd::cassi_and_issac},
};
} // namespace

// Test overrides per team size (the draft can read the team size, 3-5).

namespace {
// Pick the first champion in the list we have not taken yet.
template <std::size_t N>
bool pick_from(const cd (&list)[N], const std::vector<cd>& chosen, bool skip_casters = false) {
    for (auto pick : list) {
        if (std::find(chosen.begin(), chosen.end(), pick) != chosen.end()) continue;
        // NOVA_COUNTER: fight enemy casters with bodies, not more casters of ours.
        if (skip_casters && (pick == cd::stellar || pick == cd::prism || pick == cd::tavi || pick == cd::willow))
            continue;
        bc::draft::pick(pick);
        return true;
    }
    return false;
}

// Read the map through the raw engine calls (draft phase: the map is loaded, w/h/groups already
// answer): total gem value, groups, monolith presence. False on anything unexpected.
struct MapFacts {
    int groups = 0, gems = 0, gold = 0, max_gems = 0;
    bool monolith = false, ok = false;
};
MapFacts read_facts() {
    static MapFacts cached{};
    static bool cached_ok = false;
    if (cached_ok) return cached;
    namespace d = cambc::detail;
    MapFacts f;
    std::uint32_t n = 0;
    if (bc::detail::sdk_map_num_camp_groups(&n) != 0) return f;
    std::vector<std::uint32_t> h(n == 0 ? 1 : n);
    if (bc::detail::sdk_map_camp_groups(h.data(), n, &n) != 0 || n == 0) return f;
    f.groups = static_cast<int>(n);
    f.ok = true;
    for (std::uint32_t k = 0; k < n; ++k) {
        d::camp_group_info info{};
        if (bc::detail::sdk_map_camp_group(h[k], &info) != 0) {
            f.ok = false;
            break;
        }
        f.gems += static_cast<int>(info.gems);
        f.gold += static_cast<int>(info.gold);
        f.max_gems = std::max(f.max_gems, static_cast<int>(info.gems));
        if (f.monolith) continue; // monolith check costs one extra loop per group: only until found
        std::uint32_t members = 0;
        if (bc::detail::sdk_map_camp_group_num_camps(h[k], &members) != 0 || members == 0) continue;
        std::vector<std::uint32_t> spawns(members);
        if (bc::detail::sdk_map_camp_group_camps(h[k], spawns.data(), members, &members) != 0) continue;
        for (std::uint32_t m = 0; m < members && !f.monolith; ++m) {
            d::camp_info spec{};
            if (bc::detail::sdk_map_camp_info(spawns[m], &spec) != 0) continue;
            f.monolith |= static_cast<bc::camp_type>(spec.type) == bc::camp_type::monolith;
        }
    }
    cached = f;
    cached_ok = f.ok;
    return f;
}

// Share of dangerous camp groups (wolves, elks, monoliths) with a camp of another dangerous group
// within 3 tiles (0 on fifteen of the seventeen official maps, ~0.9 on noise-generated maps).
// Computed once per draft; -1 when the map cannot be read.
float cluster_frac() {
    static float cached = -2.0f;
    if (cached > -1.5f) return cached;
    cached = -1.0f;
    std::uint32_t n = 0;
    if (bc::detail::sdk_map_num_camp_groups(&n) != 0 || n == 0) return cached;
    std::vector<std::uint32_t> h(n);
    if (bc::detail::sdk_map_camp_groups(h.data(), n, &n) != 0) return cached;
    std::vector<std::vector<vec2>> dang;
    for (std::uint32_t k = 0; k < n; ++k) {
        std::uint32_t members = 0;
        if (bc::detail::sdk_map_camp_group_num_camps(h[k], &members) != 0 || members == 0) continue;
        std::vector<std::uint32_t> spawns(members);
        if (bc::detail::sdk_map_camp_group_camps(h[k], spawns.data(), members, &members) != 0) continue;
        std::vector<vec2> cells;
        for (std::uint32_t m = 0; m < members; ++m) {
            bc::detail::camp_info spec{};
            if (bc::detail::sdk_map_camp_info(spawns[m], &spec) != 0) continue;
            const auto t = static_cast<bc::camp_type>(spec.type);
            if (t == bc::camp_type::wolf || t == bc::camp_type::elk || t == bc::camp_type::monolith) cells.push_back({spec.x, spec.y});
        }
        if (!cells.empty()) dang.push_back(std::move(cells));
    }
    if (dang.empty()) return cached = 0.0f;
    int packed = 0;
    for (std::size_t i = 0; i < dang.size(); ++i) {
        bool near = false;
        for (std::size_t j = 0; j < dang.size() && !near; ++j) {
            if (j == i) continue;
            for (vec2 a : dang[i]) {
                for (vec2 b : dang[j])
                    if (std::max(std::abs(a.x - b.x), std::abs(a.y - b.y)) <= 3) {
                        near = true;
                        break;
                    }
                if (near) break;
            }
        }
        packed += near;
    }
    return cached = static_cast<float>(packed) / static_cast<float>(dang.size());
}

// Prefer mobile champions only when hole crossings actually unlock gem camps.
// In the v43 islands replay, the three champions without dashes collected no gems.
// Check both fields: disconnected walls alone must not trigger this draft.
bool needs_gap_crossings() {
    static int cached = -1;
    if (cached >= 0) return cached != 0;
    cached = 0;
    const auto holes = bc::map::holes();
    if (holes.is_empty()) return false;
    const auto blocked = bc::map::walls() | holes | bc::map::altars() | bc::map::spawn_region(team::enemy);
    const auto open = ~blocked;
    const auto bridges = holes &
        ((open.shift_right(1) & open.shift_right(-1)) | (open.shift_up(1) & open.shift_up(-1)) |
            (open.shift_right(1).shift_up(1) & open.shift_right(-1).shift_up(-1)) |
            (open.shift_right(1).shift_up(-1) & open.shift_right(-1).shift_up(1)));
    if (bridges.is_empty()) return false;
    bc::distance_field walking, crossing;
    bc::bitboard visited;
    const auto spawn = bc::map::spawn_region(team::ally);
    walking.compute(blocked, spawn, visited);
    crossing.compute(blocked & ~bridges, spawn, visited);
    std::uint32_t n = 0;
    if (bc::detail::sdk_map_num_camp_groups(&n) != 0 || n == 0) return false;
    std::vector<std::uint32_t> handles(n);
    if (bc::detail::sdk_map_camp_groups(handles.data(), n, &n) != 0) return false;
    std::uint64_t total = 0, unlocked = 0;
    for (auto h : handles) {
        bc::detail::camp_group_info info{};
        if (bc::detail::sdk_map_camp_group(h, &info) != 0) return false;
        total += info.gems;
        std::uint32_t count = 0;
        if (bc::detail::sdk_map_camp_group_num_camps(h, &count) != 0 || count == 0) continue;
        std::vector<std::uint32_t> members(count);
        if (bc::detail::sdk_map_camp_group_camps(h, members.data(), count, &count) != 0) return false;
        bool walk = false, dash = false;
        for (auto member : members) {
            bc::detail::camp_info spec{};
            if (bc::detail::sdk_map_camp_info(member, &spec) != 0) return false;
            const vec2 p{spec.x, spec.y};
            walk |= fdist(walking, p) != kUnreach;
            dash |= fdist(crossing, p) != kUnreach;
        }
        if (!walk && dash) unlocked += info.gems;
    }
    cached = total > 0 && unlocked * 4 >= total ? 1 : 0;
    return cached != 0;
}
} // namespace


// Map-aware draft (APEX_MAPDRAFT): the draft reads the map size and team size, which identify each
// official map, and picks a lineup for it. APEX_MD_<MAP> = lineup index (-1 = the default preset).
// Lineups: 0 melee (preset 6), 1 C&I+Stellar+Tavi, 2 C&I+Stellar+Varg, 3 Prism+Stellar+Tavi,
// 4 Vendetta+Varg+Stellar, 5 C&I+Tavi+Varg.
#define APEX_MD_COLLISION -1
#define APEX_MD_CORNERS -1
#define APEX_MD_EXPANSE -1
#define APEX_MD_INTERLOCK -1
#define APEX_MD_MONOLITH -1
#define APEX_MD_PACKS -1
#define APEX_MD_ROWS -1
#define APEX_MD_OTHER -1
// Class draft (APEX_CLASSDRAFT): lineup per map class (team size 3/4/5 x small/large, see strategy.h);
// APEX_L<k> = lineup index, -1 = fall through to the other draft rules.
namespace {
constexpr cd kLineups[][12] = { // 12 draft choices in engine 3.0 (older rows end with a repeated pick, skipped)
    {cd::vendetta, cd::varg, cd::ryth, cd::ren, cd::marcella, cd::stellar, cd::tavi, cd::vesper_vale, cd::willow,
        cd::prism, cd::cassi_and_issac},
    {cd::cassi_and_issac, cd::stellar, cd::tavi, cd::varg, cd::ren, cd::prism, cd::ryth, cd::vendetta, cd::willow,
        cd::marcella, cd::vesper_vale},
    {cd::cassi_and_issac, cd::stellar, cd::varg, cd::tavi, cd::ren, cd::prism, cd::ryth, cd::vendetta, cd::willow,
        cd::marcella, cd::vesper_vale},
    {cd::prism, cd::stellar, cd::tavi, cd::cassi_and_issac, cd::ren, cd::varg, cd::ryth, cd::vendetta, cd::willow,
        cd::marcella, cd::vesper_vale},
    {cd::vendetta, cd::varg, cd::stellar, cd::tavi, cd::ren, cd::ryth, cd::cassi_and_issac, cd::prism, cd::willow,
        cd::marcella, cd::vesper_vale},
    {cd::cassi_and_issac, cd::tavi, cd::varg, cd::stellar, cd::ren, cd::prism, cd::ryth, cd::vendetta, cd::willow,
        cd::marcella, cd::vesper_vale},
    // 6: Mite-style (v13b), 7: + Tavi fourth, 8: + Stellar fourth, 9: C&I second
    {cd::vendetta, cd::varg, cd::cassi_and_issac, cd::ryth, cd::ren, cd::marcella, cd::stellar, cd::tavi, cd::prism,
        cd::willow, cd::vesper_vale},
    {cd::vendetta, cd::varg, cd::cassi_and_issac, cd::tavi, cd::ren, cd::ryth, cd::stellar, cd::marcella, cd::prism,
        cd::willow, cd::vesper_vale},
    {cd::vendetta, cd::varg, cd::cassi_and_issac, cd::stellar, cd::ren, cd::ryth, cd::tavi, cd::marcella, cd::prism,
        cd::willow, cd::vesper_vale},
    {cd::vendetta, cd::cassi_and_issac, cd::varg, cd::ryth, cd::ren, cd::marcella, cd::stellar, cd::tavi, cd::prism,
        cd::willow, cd::vesper_vale},
    // 10: the top team's stampede caster lineup (Ryth tanks, casters nuke from range 4).
    {cd::stellar, cd::tavi, cd::ryth, cd::prism, cd::willow, cd::ren, cd::varg, cd::cassi_and_issac, cd::vendetta,
        cd::marcella, cd::vesper_vale},
    // 11: the top team's interlock/contest lineup (burst and stuns).
    {cd::tavi, cd::stellar, cd::prism, cd::ren, cd::willow, cd::ryth, cd::varg, cd::cassi_and_issac, cd::vendetta,
        cd::marcella, cd::vesper_vale},
    // 12: casters first, Varg as the front line.
    {cd::stellar, cd::tavi, cd::varg, cd::prism, cd::ryth, cd::ren, cd::cassi_and_issac, cd::willow, cd::vendetta,
        cd::marcella, cd::vesper_vale},
    // 13: Stellar + Tavi beside the melee core.
    {cd::stellar, cd::vendetta, cd::varg, cd::tavi, cd::ryth, cd::cassi_and_issac, cd::ren, cd::prism, cd::willow,
        cd::marcella, cd::vesper_vale},
    // v25 clean-map screen (inert unless a chart or NOVA_FALLBACK_LINEUP names them); all keep C&I in
    // the first three picks (one pick, two bodies).
    // 14: lineup 6 with Marcella fifth instead of Ren.
    {cd::vendetta, cd::varg, cd::cassi_and_issac, cd::ryth, cd::marcella, cd::ren, cd::stellar, cd::tavi, cd::prism,
        cd::willow, cd::vesper_vale},
    // 15: lineup 6 with Marcella fourth instead of Ryth.
    {cd::vendetta, cd::varg, cd::cassi_and_issac, cd::marcella, cd::ren, cd::ryth, cd::stellar, cd::tavi, cd::prism,
        cd::willow, cd::vesper_vale},
    // 16: Ryth in place of Vendetta.
    {cd::ryth, cd::varg, cd::cassi_and_issac, cd::vendetta, cd::ren, cd::marcella, cd::stellar, cd::tavi, cd::prism,
        cd::willow, cd::vesper_vale},
    // 17: Ryth in place of Varg.
    {cd::vendetta, cd::ryth, cd::cassi_and_issac, cd::varg, cd::ren, cd::marcella, cd::stellar, cd::tavi, cd::prism,
        cd::willow, cd::vesper_vale},
    // 18: lineup 6 with Ren fourth and Ryth fifth.
    {cd::vendetta, cd::varg, cd::cassi_and_issac, cd::ren, cd::ryth, cd::marcella, cd::stellar, cd::tavi, cd::prism,
        cd::willow, cd::vesper_vale},
    // 19: ladder meta (platform top-12 teams, 5.6k games): C&I + Stellar + Ren (3), + Ryth (4), + Varg (5).
    {cd::cassi_and_issac, cd::stellar, cd::ren, cd::ryth, cd::varg, cd::tavi, cd::prism, cd::willow, cd::vendetta,
        cd::marcella, cd::vesper_vale},
    // 20: top teams' stampede comp: Ryth + C&I + Stellar + Prism + Tavi.
    {cd::cassi_and_issac, cd::stellar, cd::ryth, cd::prism, cd::tavi, cd::ren, cd::varg, cd::willow, cd::vendetta,
        cd::marcella, cd::vesper_vale},
    // Engine 3.0 (C&I, Stellar, Tavi's stun weaker; Vendetta, Willow, Marcella stronger; Heart of Ruin new):
    // 21: Heart of Ruin and Vendetta lead a melee core with Varg's splash.
    {cd::heart_of_ruin, cd::vendetta, cd::varg, cd::ryth, cd::marcella, cd::willow, cd::stellar, cd::tavi, cd::ren,
        cd::prism, cd::cassi_and_issac, cd::vesper_vale},
    // 22: buffed picks first: Vendetta, Marcella, Willow (heals), Heart of Ruin, Varg.
    {cd::vendetta, cd::marcella, cd::willow, cd::heart_of_ruin, cd::varg, cd::ryth, cd::stellar, cd::tavi, cd::ren,
        cd::prism, cd::cassi_and_issac, cd::vesper_vale},
    // 23: the ladder-meta core with Heart of Ruin in place of Ren.
    {cd::cassi_and_issac, cd::stellar, cd::heart_of_ruin, cd::ryth, cd::varg, cd::vendetta, cd::tavi, cd::prism,
        cd::willow, cd::marcella, cd::ren, cd::vesper_vale},
    // 24: Vendetta + Heart of Ruin divers behind Varg, Stellar for range, Willow to sustain.
    {cd::varg, cd::vendetta, cd::heart_of_ruin, cd::stellar, cd::willow, cd::ryth, cd::marcella, cd::tavi, cd::ren,
        cd::prism, cd::cassi_and_issac, cd::vesper_vale},
    // 25-27: engine 1.0.3 ladder, top teams (Oct 23, ladder/analyse.py): Vesper (+33% gold) in nearly every comp.
    // 25: Intercontinental Fish (#1, 80%): Vesper first, Vendetta, Heart, C&I, Ryth.
    {cd::vesper_vale, cd::vendetta, cd::heart_of_ruin, cd::cassi_and_issac, cd::ryth, cd::marcella, cd::varg, cd::stellar,
        cd::willow, cd::tavi, cd::ren, cd::prism},
    // 26: print dont int: Vesper first, Heart, Vendetta, Ryth, Marcella.
    {cd::vesper_vale, cd::heart_of_ruin, cd::vendetta, cd::ryth, cd::marcella, cd::varg, cd::stellar, cd::willow,
        cd::cassi_and_issac, cd::tavi, cd::ren, cd::prism},
    // 27: our lineup 24 with Vesper first (Varg, Vendetta, Heart behind her).
    {cd::vesper_vale, cd::varg, cd::vendetta, cd::heart_of_ruin, cd::stellar, cd::willow, cd::ryth, cd::marcella, cd::tavi,
        cd::ren, cd::prism, cd::cassi_and_issac},
    // 28: ladder proxy (:3 / prism best girl / Pantheon): Vesper, Marcella, Heart, Prism, Vendetta.
    {cd::vesper_vale, cd::marcella, cd::heart_of_ruin, cd::prism, cd::vendetta, cd::ryth, cd::tavi, cd::willow, cd::varg,
        cd::stellar, cd::ren, cd::cassi_and_issac},
};
constexpr int kNumLineups = sizeof(kLineups) / sizeof(kLineups[0]);

// Which official map is this? Width, height and team size are unique per map. -1 = unknown map.
int map_lineup(int w, int h, unsigned size) {
    struct Key { int w, h; unsigned size; int lineup; };
    constexpr Key kMaps[] = {
        {41, 41, 3, APEX_MD_COLLISION}, {71, 71, 5, APEX_MD_CORNERS}, {30, 30, 5, APEX_MD_ELKRING},
        {80, 80, 3, APEX_MD_EXPANSE}, {40, 40, 4, APEX_MD_INTERLOCK}, {90, 30, 5, APEX_MD_LANES},
        {50, 50, 5, APEX_MD_MONOLITH}, {31, 31, 3, APEX_MD_PACKS}, {50, 50, 4, APEX_MD_ROWS},
    };
    for (const auto& k : kMaps)
        if (((k.w == w && k.h == h) || (k.w == h && k.h == w)) && k.size == size) return k.lineup;
    return APEX_MD_OTHER;
}
} // namespace

// Official map pool identity: width, height, team size and camp-group count.
int nova_map_id(int w, int h, unsigned size, int groups) {
    if (NO_MAPID) return -1; // NO_MAPID: no old-official-map identity (the 4.0 ladder pool is new maps)
    struct Key { int w, h; unsigned size; int groups; };
    constexpr Key kMaps[] = {
        {100, 100, 5, 12}, {41, 41, 3, 20}, {50, 50, 5, 14}, {71, 71, 5, 30}, {41, 30, 5, 8}, {30, 30, 5, 10},
        {80, 80, 3, 24}, {30, 30, 3, 6}, {40, 40, 4, 14}, {90, 30, 5, 42}, {50, 50, 5, 22}, {31, 31, 3, 8},
        {50, 65, 5, 23}, {50, 50, 4, 9}, {30, 80, 4, 18}, {60, 50, 5, 13}, {45, 30, 4, 22},
    };
    for (int i = 0; i < static_cast<int>(sizeof(kMaps) / sizeof(kMaps[0])); ++i) {
        const auto& k = kMaps[i];
        if (((k.w == w && k.h == h) || (k.w == h && k.h == w)) && k.size == size && k.groups == groups) return i;
    }
    return -1;
}

// Lineup per official map (order: ambush collision contest corners eight elkring expanse fragment interlock
// lanes monolith packs pilgrimage rows rushbait-v2 stampede swirl); -1 = the older draft rules.
#define NOVA_ALL_LINEUP -1
// Lineup for maps outside the official pool (unseen maps get the best overall lineup).
// v28: comp 2 (C&I, Stellar, Varg, Tavi, Ren): 61.8% vs v26 on realistic fresh maps (no bush camps,
// separated groups); comp 6's edge had come from bush-camp artifact maps.
// v24: comp 6 = the strongest measured headhunter vs frozen opponents on fresh maps
// (58.8% n=250 + 52.0% + 56.0% on two more suites = 56.7% over 450 games vs the v22 artifact).
// NOVA_CLUSTER_DRAFT (v28): packed-camp unknown maps draft NOVA_CLUSTER_LINEUP instead of the fallback.
#define NOVA_CLUSTER_FRAC 0.5f
#define NOVA_CLUSTER_LINEUP 6
constexpr int kNovaMapLineup[17] = {NOVA_MAP_LINEUPS};


#include "draft_net.h"

// Keep the incumbent draft policy while comparing the donor's gameplay.
#undef A2_MLDRAFT
#define A2_MLDRAFT 1
#undef A3_BIG_LINEUP
#define A3_BIG_LINEUP 6
#undef A3_BIG_PICKS
#define A3_BIG_PICKS cd::vendetta, cd::varg, cd::cassi_and_issac, cd::marcella, cd::heart_of_ruin
#undef NOVA_ALL_LINEUP
#define NOVA_ALL_LINEUP -1

namespace {
// ML draft (agent2/lab/draft_data.js + draft_fit.py): a net trained on random-lineup lab games scores every free
// champion by P(win | our side's map features, our picks with it, their picks so far, team size, picking first, draft
// progress); we take the best. The 16 map features mirror draft_data.js draftFeatures exactly.
// tanh by Lambert's continued fraction (error < 1e-6 for |x| < 5): std::tanh is a libm call that costs ~150 fuel in
// wasm, and 700 of them overran a 100k draft turn (real engine: the draft then stopped picking).
inline float fast_tanh(float x) {
    if (x > 4.97f) return 1.0f;
    if (x < -4.97f) return -1.0f;
    const float x2 = x * x;
    return x * (135135.0f + x2 * (17325.0f + x2 * (378.0f + x2))) / (135135.0f + x2 * (62370.0f + x2 * (3150.0f + x2 * 28.0f)));
}

bool ml_draft_pick(std::uint32_t size) {
    namespace dn = draft_net;
    // Map features and the net's map part are computed once (first draft turn, 10x fuel) and kept: later draft turns
    // have the normal 100k budget, so each pick then only adds a few weight rows per candidate.
    static float feat[16] = {};
    static float h_map[dn::kHid] = {};
    static bool have_feat = false;
    if (!have_feat) {
        const float W = static_cast<float>(bc::map::width()), Hh = static_cast<float>(bc::map::height());
        float sp[2][2] = {};
        const team sides[2] = {team::ally, team::enemy};
        for (int t = 0; t < 2; ++t) {
            // the spawn region's bounding-box centre, as draft_data.js computes it ((min + max_exclusive - 1) / 2)
            int x0 = 1 << 20, y0 = 1 << 20, x1 = -1, y1 = -1;
            for (vec2 q : bc::map::spawn_region(sides[t]).positions())
                x0 = std::min(x0, q.x), y0 = std::min(y0, q.y), x1 = std::max(x1, q.x), y1 = std::max(y1, q.y);
            sp[t][0] = static_cast<float>(x0 + x1) / 2.0f, sp[t][1] = static_cast<float>(y0 + y1) / 2.0f;
        }
        std::uint32_t n = 0;
        if (bc::detail::sdk_map_num_camp_groups(&n) != 0 || n > 400) return false;
        std::vector<std::uint32_t> handles(n);
        if (n && bc::detail::sdk_map_camp_groups(handles.data(), n, &n) != 0) return false;
        float gems = 0, gold = 0, maxg = 0, near = 0, dsum = 0, cnt[6] = {};
        for (std::uint32_t k = 0; k < n; ++k) {
            bc::detail::camp_group_info info{};
            bc::detail::sdk_map_camp_group(handles[k], &info);
            const float g = static_cast<float>(info.gems);
            gems += g, gold += static_cast<float>(info.gold), maxg = std::max(maxg, g);
            std::uint32_t m = 0;
            bc::detail::sdk_map_camp_group_num_camps(handles[k], &m);
            std::vector<std::uint32_t> mem(std::max<std::uint32_t>(m, 1));
            if (m) bc::detail::sdk_map_camp_group_camps(handles[k], mem.data(), m, &m);
            float x = 0, y = 0, c = 0;
            for (std::uint32_t q = 0; q < m; ++q) {
                bc::detail::camp_info spec{};
                if (bc::detail::sdk_map_camp_info(mem[q], &spec) != 0) continue;
                if (spec.type >= 0 && spec.type < 6) cnt[spec.type] += 1;
                x += static_cast<float>(spec.x), y += static_cast<float>(spec.y), c += 1;
            }
            if (c > 0) {
                const float d = std::max(std::fabs(x / c - sp[0][0]), std::fabs(y / c - sp[0][1]));
                dsum += d;
                if (d <= 20) near += g;
            }
        }
        const float sd = std::max(std::fabs(sp[0][0] - sp[1][0]), std::fabs(sp[0][1] - sp[1][1]));
        const float nn = static_cast<float>(n);
        const float f[16] = {W / 100, Hh / 100, W * Hh / 10000, nn / 30, gems / 500, gold / 3000, cnt[0] / 20, cnt[1] / 20, cnt[2] / 20,
            cnt[3] / 20, cnt[5] / 4, cnt[4] / 2, sd / 100, n ? dsum / nn / 100 : 0, gems > 0 ? near / gems : 0, maxg / 60};
        for (int i = 0; i < 16; ++i) feat[i] = f[i];
        for (int h = 0; h < dn::kHid; ++h) {
            float a = dn::b1[h];
            for (int i = 0; i < 16; ++i) a += dn::W1[i * dn::kHid + h] * feat[i];
            h_map[h] = a;
        }
        ngp::map_trace(feat);
        have_feat = true;
    }
    const auto ours = bc::draft::current_draft(team::ally), theirs = bc::draft::current_draft(team::enemy);
    bool taken[12] = {};
    for (auto c : ours) if (static_cast<int>(c) >= 0 && static_cast<int>(c) < 12) taken[static_cast<int>(c)] = true;
    // Enemy picks remain model features, but only our own picks make a champion unavailable.
    const int sz = static_cast<int>(std::max<std::uint32_t>(size, 1));
    const int j = static_cast<int>(ours.size()) + 1;
    const bool first = theirs.size() == ours.size();
    float x[dn::kIn];
    int best = -1;
    float best_z = -1e30f;
    // Active input rows besides the map part: our picks, their picks, team size, picking first, progress (weight).
    int rows[32];
    float rw[32];
    int nr = 0;
    for (auto o : ours) rows[nr] = 16 + static_cast<int>(o), rw[nr++] = 1.0f;
    for (auto o : theirs) rows[nr] = 28 + static_cast<int>(o), rw[nr++] = 1.0f;
    rows[nr] = 40 + std::min(std::max(sz, 3), 5) - 3, rw[nr++] = 1.0f;
    if (first) rows[nr] = 43, rw[nr++] = 1.0f;
    rows[nr] = 44, rw[nr++] = static_cast<float>(j) / static_cast<float>(sz);
    float h_base[dn::kHid];
    for (int h = 0; h < dn::kHid; ++h) {
        float a = h_map[h];
        for (int r = 0; r < nr; ++r) a += dn::W1[rows[r] * dn::kHid + h] * rw[r];
        h_base[h] = a;
    }
    for (int c = 0; c < 12; ++c) {
        if (taken[c]) continue;
        float z = dn::b2;
        const float* wc = dn::W1 + (16 + c) * dn::kHid; // the candidate's own pick row
        for (int h = 0; h < dn::kHid; ++h) z += dn::w2[h] * fast_tanh(h_base[h] + wc[h]);
        if (z > best_z) best_z = z, best = c;
    }
    (void)x;
    if (best < 0) return false;
    bc::draft::pick(static_cast<cd>(best));
    return true;
}
} // namespace



// V70_DRAFT_TABLE: lineup per pool map (research/v70/draft_table.json; key = width, height, team size, camp groups).
int v70_lineup(int w, int h, unsigned size, int groups) {
    struct Row { int w, h; unsigned size; int groups, lineup; };
    constexpr Row kRows[] = {
        {100, 100, 5, 12, 6}, // 00ambush
        {41, 41, 3, 20, 26}, // 00collision
        {50, 50, 5, 14, 6}, // 00contest
        {71, 71, 5, 30, 6}, // 00corners
        {61, 61, 5, 6, 22}, // 00crater
        {79, 79, 5, 11, 22}, // 00dunes
        {41, 30, 5, 8, 22}, // 00eight
        {30, 30, 5, 10, 21}, // 00elkring
        {93, 93, 5, 9, 21}, // 00galaxy
        {50, 40, 5, 18, 22}, // 00gem-fields
        {35, 31, 5, 34, 22}, // 00lost-world
        {31, 31, 3, 8, 6}, // 00packs
        {45, 45, 5, 21, 21}, // 00quadrants
        {51, 85, 5, 13, 22}, // 00ribs
        {45, 35, 5, 32, 22}, // 00split
        {60, 50, 5, 13, 22}, // 00stampede
        {50, 41, 5, 31, 6}, // 01boss-battle
        {40, 40, 3, 22, 21}, // 01broken-curve
        {61, 61, 5, 11, 6}, // 01concentrated-wealth
        {50, 50, 5, 29, 22}, // 01elk-arena
        {61, 71, 5, 28, 21}, // 01fracture
        {31, 31, 3, 15, 24}, // 01gold-rush
        {40, 40, 4, 21, 27}, // 01shortcut
        {50, 50, 5, 16, 21}, // 01starfish
        {80, 80, 5, 14, 22}, // 01starvation
        {91, 75, 5, 11, 26}, // 02famine
        {89, 71, 5, 14, 6}, // 02geodes
        {100, 100, 5, 21, 26}, // 02harvest
        {30, 30, 4, 15, 21}, // 02stalactites
        {30, 30, 3, 20, 27}, // 02the-pond
    };
    for (const auto& r : kRows)
        if (r.w == w && r.h == h && r.size == size && r.groups == groups) return r.lineup;
    return -1;
}

static void choose_draft() {
    const auto chosen = bc::draft::current_draft(team::ally);
    [[maybe_unused]] std::uint32_t size = 0;
    try {
        size = bc::draft::team_size();
    } catch (...) {
    }
    int v70 = -1; // LADDER_TABLES: the user's per-map lineup for recognised ladder maps
    if (a2stack::cfg() & 16384) { // E135: what the top 15 teams field most (4,500 games): Heart of Ruin, Vesper, Marcella, then Vendetta, Cassi and Issac
        constexpr cd kTop[] = {cd::heart_of_ruin, cd::vesper_vale, cd::marcella, cd::vendetta, cd::cassi_and_issac, cd::ryth};
        for (auto c : kTop)
            if (std::find(chosen.begin(), chosen.end(), c) == chosen.end()) {
                bc::draft::pick(c);
                return;
            }
    }
    if (a2stack::cfg() & 64) {
        constexpr cd kMeta[] = {cd::heart_of_ruin, cd::marcella, cd::vesper_vale, cd::ryth, cd::vendetta, cd::varg};
        for (auto c : kMeta)
            if (std::find(chosen.begin(), chosen.end(), c) == chosen.end()) {
                bc::draft::pick(c);
                return;
            }
    }
    // A2_HOR (E81): the top-7 ladder teams all field Heart of Ruin. Take it at our pick number A2_HOR (1 = first; 9 = our
    // last pick) unless we already have it or the enemy took it.
    {
        const auto theirs = bc::draft::current_draft(team::enemy);
        const bool have = std::find(chosen.begin(), chosen.end(), cd::heart_of_ruin) != chosen.end() ||
            std::find(theirs.begin(), theirs.end(), cd::heart_of_ruin) != theirs.end();
        const std::size_t at = A2_HOR >= 9 ? (size > 0 ? size - 1 : 0) : static_cast<std::size_t>(A2_HOR - 1);
        if (RTG(63) && !have && chosen.size() >= at) {
            bc::draft::pick(cd::heart_of_ruin);
            return;
        }
    }
    try {
        std::uint32_t v70_ng = 0;
        bc::detail::sdk_map_num_camp_groups(&v70_ng);
        v70 = v70_lineup(bc::map::width(), bc::map::height(), size, static_cast<int>(v70_ng));
    } catch (...) {
        v70 = -1;
    }
    // ML draft on maps the lineup tables do not know (A2_MLDRAFT 2: unknown maps only; 1: every map).
    bool ml_done = false;
    try {
        bool known = false;
        if (A2_MLDRAFT == 2) {
            std::uint32_t n = 0;
            bc::detail::sdk_map_num_camp_groups(&n);
            known = nova_map_id(bc::map::width(), bc::map::height(), size, static_cast<int>(n)) >= 0;
        }
        bool a3_custom = A3_BIG_LINEUP >= 0 && size >= static_cast<std::uint32_t>(A3_BIG_SIZE);
        a3_custom |= size >= static_cast<std::uint32_t>(A3_BIG_SIZE);
        ml_done = !known && !a3_custom && v70 < 0 && ml_draft_pick(size);
    } catch (...) {
        ml_done = false; // fall back to the lineup tables
    }
    // Draft memory (APEX_BRAIN): enemies' picks are visible and the pick order alternates, so record
    // what the champions need to know on every turn (the last write wins and includes all picks).
    try {
        const MapFacts mf = read_facts(); // cached; gives the biggest camp-group gem value too
        unsigned fl = 0;
        try {
            const int aw = bc::map::width(), ah = bc::map::height();
            // bit0 = dense-score-race map, bit1 = monolith map; both swallowed by an exception
            // guard. NOVA_CLASSIFY writes the bits even when the banking switches are off.
            if ((raceBank || classify) && mf.ok && aw > 0 && ah > 0 &&
                static_cast<float>(mf.gems) / static_cast<float>(aw * ah) >= raceDens)
                fl |= 1u;
        } catch (...) {
        }
        if ((monoBank || classify) && mf.ok && mf.monolith) fl |= 2u;
        brain::record_draft(size, mf.ok ? mf.max_gems : 0, fl);
    } catch (...) {
        try {
            brain::record_draft(size);
        } catch (...) {
        }
    }
    if (ml_done) return; // picked (and planned) by the net above; the header is written
    {
        int w = 0, h = 0, ng = 0;
        try {
            w = bc::map::width();
            h = bc::map::height();
            std::uint32_t n = 0;
            if (bc::detail::sdk_map_num_camp_groups(&n) == 0) ng = static_cast<int>(n);
        } catch (...) {
        }
        const int mid = nova_map_id(w, h, size, ng);
        try {
            if (NOVA_ALL_LINEUP < 0 && v70 < 0 && needs_gap_crossings()) {
                constexpr cd mobile[] = {cd::vendetta, cd::heart_of_ruin, cd::ren, cd::vesper_vale,
                    cd::cassi_and_issac, cd::varg, cd::ryth, cd::stellar, cd::tavi, cd::marcella, cd::willow, cd::prism};
                if (pick_from(mobile, chosen)) return;
            }
        } catch (...) {
            // Preserve the existing draft if optional map analysis is unavailable.
        }
        int li = NOVA_ALL_LINEUP >= 0 ? NOVA_ALL_LINEUP
                                      : (mid >= 0 ? kNovaMapLineup[mid] : NOVA_FALLBACK_LINEUP);
        if (A3_BIG_LINEUP >= 0 && size >= static_cast<std::uint32_t>(A3_BIG_SIZE)) li = A3_BIG_LINEUP; // A3 hybrid draft
        // NOVA_CLUSTER_DRAFT (v28): unknown maps whose dangerous camp groups sit packed together
        // (another dangerous group within 3 tiles for at least NOVA_CLUSTER_FRAC of them) get the melee
        // splash comp; spread-out maps (like every official map but lanes/rushbait) the caster comp.
        if (NOVA_CLUSTER_DRAFT && mid < 0 && NOVA_ALL_LINEUP < 0) {
            const float frac = cluster_frac();
            if (frac >= NOVA_CLUSTER_FRAC) li = NOVA_CLUSTER_LINEUP;
        }
        // NOVA_DRAFT_AI: unknown maps choose by reading the map itself (monolith -> melee wrecking
        // crew; big and sparse -> the siege-farm caster comp; otherwise the proven fallback).
        if (NOVA_DRAFT_AI && mid < 0 && (w > 0 && h > 0)) {
            const MapFacts f = read_facts();
            const int area = w * h;
            if (f.ok) {
                if (f.monolith) li = NOVA_AI_MONO_LINEUP;
                else if (area >= NOVA_AI_BIG_AREA && area / std::max(f.groups, 1) >= NOVA_AI_SPARSE) li = NOVA_AI_BIG_LINEUP;
            }
        }
        // NOVA_COUNTER: on board enemy caster picks (picks alternate and are visible).
        bool skip = false;
        if (NOVA_COUNTER > 0) {
            try {
                int ec = 0;
                for (auto c : bc::draft::current_draft(team::enemy)) ec += brain::is_caster(c) ? 1 : 0;
                skip = ec >= NOVA_COUNTER;
            } catch (...) {
                skip = false;
            }
        }
        if (v70 >= 0 && v70 < kNumLineups && pick_from(kLineups[v70], chosen)) return; // LADDER_TABLES
        // A3 custom pick lists per team size (lab hooks; picked in order, skipping champions already ours).
        if (size >= static_cast<std::uint32_t>(A3_BIG_SIZE)) {
            constexpr cd kA3Big[] = {A3_BIG_PICKS};
            if (pick_from(kA3Big, chosen, skip)) return;
        }
        if (li >= 0 && li < kNumLineups && pick_from(kLineups[li], chosen, skip)) return;
    }
    // Official maps first (APEX_MAPDRAFT), then the map-class draft for any other map.
    if (APEX_MAPDRAFT) {
        int w = 0, h = 0;
        try {
            w = bc::map::width();
            h = bc::map::height();
        } catch (...) {
        }
        const int li = map_lineup(w, h, size);
        if (li >= 0 && li < kNumLineups && pick_from(kLineups[li], chosen)) return;
    }
    if (APEX_CLASSDRAFT) {
        constexpr int kClassLineup[6] = {APEX_L0, APEX_L1, APEX_L2, APEX_L3, APEX_L4, APEX_L5};
        int w = 0, h = 0;
        try {
            w = bc::map::width();
            h = bc::map::height();
        } catch (...) {
        }
        const int li = kClassLineup[brain::map_class(w, h, static_cast<int>(size))];
        if (li >= 0 && li < kNumLineups && pick_from(kLineups[li], chosen)) return;
    }
    pick_from(kPresets[APEX_DRAFT], chosen);
}


void play_draft() {
    choose_draft();
    // The plan only advises camp travel. Draft picks and the strategy header
    // are already selected and the planner preserves that header.
    static bool camp_plan_written = false;
    if (camp_plan_written) return;
    try {
        const auto size = bc::draft::team_size();
        if (size >= 3) camp_plan_written = mapplan::draft_write(size);
    } catch (...) {
    }
}
