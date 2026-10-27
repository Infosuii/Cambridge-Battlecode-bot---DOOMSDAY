#include "neural_policy.h"
// Draft: farming speed first, then durability. Both teams may own the same champion.
#include "draft.h"
#include "v67_meta.h"
#include "common.h"
#include "strategy.h"
#include <cstdio>

#ifndef APEX_DRAFT
#define APEX_DRAFT 6
#endif

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

#ifdef APEX_DRAFT_LIST
// Test override: an explicit priority list (comma-separated cd:: names), then the preset as fallback.
constexpr cd kOverride[] = {APEX_DRAFT_LIST};
#endif
// Test overrides per team size (the draft can read the team size, 3-5).
#ifdef APEX_DRAFT_T3
constexpr cd kT3[] = {APEX_DRAFT_T3};
#endif
#ifdef APEX_DRAFT_T4
constexpr cd kT4[] = {APEX_DRAFT_T4};
#endif
#ifdef APEX_DRAFT_T5
constexpr cd kT5[] = {APEX_DRAFT_T5};
#endif

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

#if A44_MOBILITY_DRAFT
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
#endif
} // namespace


// Map-aware draft (APEX_MAPDRAFT): the draft reads the map size and team size, which identify each
// official map, and picks a lineup for it. APEX_MD_<MAP> = lineup index (-1 = the default preset).
// Lineups: 0 melee (preset 6), 1 C&I+Stellar+Tavi, 2 C&I+Stellar+Varg, 3 Prism+Stellar+Tavi,
// 4 Vendetta+Varg+Stellar, 5 C&I+Tavi+Varg.
#ifndef APEX_MAPDRAFT
#define APEX_MAPDRAFT 0
#endif
#ifndef APEX_MD_COLLISION
#define APEX_MD_COLLISION -1
#endif
#ifndef APEX_MD_CORNERS
#define APEX_MD_CORNERS -1
#endif
#ifndef APEX_MD_ELKRING
#define APEX_MD_ELKRING -1
#endif
#ifndef APEX_MD_EXPANSE
#define APEX_MD_EXPANSE -1
#endif
#ifndef APEX_MD_INTERLOCK
#define APEX_MD_INTERLOCK -1
#endif
#ifndef APEX_MD_LANES
#define APEX_MD_LANES -1
#endif
#ifndef APEX_MD_MONOLITH
#define APEX_MD_MONOLITH -1
#endif
#ifndef APEX_MD_PACKS
#define APEX_MD_PACKS -1
#endif
#ifndef APEX_MD_ROWS
#define APEX_MD_ROWS -1
#endif
#ifndef APEX_MD_OTHER
#define APEX_MD_OTHER -1
#endif
// Class draft (APEX_CLASSDRAFT): lineup per map class (team size 3/4/5 x small/large, see strategy.h);
// APEX_L<k> = lineup index, -1 = fall through to the other draft rules.
#ifndef APEX_CLASSDRAFT
#define APEX_CLASSDRAFT 0
#endif
#ifndef APEX_L0
#define APEX_L0 -1
#endif
#ifndef APEX_L1
#define APEX_L1 -1
#endif
#ifndef APEX_L2
#define APEX_L2 -1
#endif
#ifndef APEX_L3
#define APEX_L3 -1
#endif
#ifndef APEX_L4
#define APEX_L4 -1
#endif
#ifndef APEX_L5
#define APEX_L5 -1
#endif
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
#ifndef NOVA_ALL_LINEUP
#define NOVA_ALL_LINEUP -1
#endif
// Lineup for maps outside the official pool (unseen maps get the best overall lineup).
// v28: comp 2 (C&I, Stellar, Varg, Tavi, Ren): 61.8% vs v26 on realistic fresh maps (no bush camps,
// separated groups); comp 6's edge had come from bush-camp artifact maps.
// v24: comp 6 = the strongest measured headhunter vs frozen opponents on fresh maps
// (58.8% n=250 + 52.0% + 56.0% on two more suites = 56.7% over 450 games vs the v22 artifact).
#ifndef NOVA_FALLBACK_LINEUP
#define NOVA_FALLBACK_LINEUP 2
#endif
// NOVA_CLUSTER_DRAFT (v28): packed-camp unknown maps draft NOVA_CLUSTER_LINEUP instead of the fallback.
#ifndef NOVA_CLUSTER_DRAFT
#define NOVA_CLUSTER_DRAFT 1
#endif
#ifndef NOVA_CLUSTER_FRAC
#define NOVA_CLUSTER_FRAC 0.5f
#endif
#ifndef NOVA_CLUSTER_LINEUP
#define NOVA_CLUSTER_LINEUP 6
#endif
#ifndef NOVA_MAP_LINEUPS
// v30: ladder-meta lineups (modal comps of the platform's top-12 teams over 5.6k games): 19 everywhere, the
// top teams' 3-pick C&I+Stellar+Varg on expanse (2), their stampede casters (20), and our own rows set (8),
// which is itself a top-team choice there. Official-map order as in nova_map_id.
#define NOVA_MAP_LINEUPS 19, 19, 19, 19, 19, 19, 2, 19, 19, 19, 19, 19, 19, 8, 19, 20, 19
#endif
constexpr int kNovaMapLineup[17] = {NOVA_MAP_LINEUPS};

#if A2_DPLAN
namespace {
// Team opening plan (A2_DPLAN), computed once on the first draft turn (10x fuel) and passed to every champion in draft
// memory after the brain header. A simple farming model of the first A2_DP_UNTIL rounds (ladder/plan_proto.py: our
// bot farms like "each champion greedy and alone", 458 gold / 76 gems by round 150 over the 40 ladder maps; a team
// schedule where groups needing 2-3 champions are taken by a crew arriving together reaches 731 / 158, about the top
// teams' 707 gold): champions walk 1.25 tiles of Chebyshev distance per round, deal kDps each to camps, a group needs
// 1 / 2 / 3 champions by total health, capture takes 5 rounds, groups return `respawn` rounds after capture. Greedy
// team schedule plus randomised retries while fuel lasts; the best schedule's steps go to each slot.
struct PlanGroup {
    float x, y, hp, val;
    int n, respawn;
};
constexpr int kPlanSlots = 6, kPlanSteps = 12;
struct Plan {
    int steps[kPlanSlots][kPlanSteps][2]; // group index (map order), start round
    int count[kPlanSlots];
    float value;
};

std::uint32_t plan_rng = 12345u;
float plan_rand() { plan_rng = plan_rng * 1664525u + 1013904223u; return static_cast<float>(plan_rng >> 8) / 16777216.0f; }

Plan plan_once(const std::vector<PlanGroup>& G, float sx, float sy, int ncham, float noise) {
    constexpr float kDps = 50.0f, kWalk = 1.25f;
    const float horizon = static_cast<float>(A2_DP_UNTIL);
    Plan p{};
    float px[kPlanSlots], py[kPlanSlots], fr[kPlanSlots];
    for (int k = 0; k < ncham; ++k) px[k] = sx, py[k] = sy, fr[k] = 3.0f;
    std::vector<float> avail(G.size(), 0.0f);
    auto dist = [&](int k, const PlanGroup& g) { return kWalk * std::max(std::fabs(px[k] - g.x), std::fabs(py[k] - g.y)); };
    for (int guard = 0; guard < 400; ++guard) {
        int i = 0;
        for (int k = 1; k < ncham; ++k)
            if (fr[k] < fr[i]) i = k;
        const float t = fr[i];
        if (t >= horizon) break;
        int best = -1, crew[3] = {i, -1, -1}, best_crew[3] = {i, -1, -1}, best_n = 1;
        float best_s = 0.0f, best_done = 0.0f;
        for (std::size_t gi = 0; gi < G.size(); ++gi) {
            const PlanGroup& g = G[gi];
            if (g.n > ncham) continue;
            // The crew: us plus the n-1 other champions who can be there soonest.
            int n = 1;
            crew[1] = crew[2] = -1;
            for (int need = 1; need < g.n; ++need) {
                int pick = -1;
                float pt = 1e30f;
                for (int k = 0; k < ncham; ++k) {
                    if (k == i || k == crew[1] || k == crew[2]) continue;
                    const float at = std::max(fr[k], t) + dist(k, g);
                    if (at < pt) pt = at, pick = k;
                }
                crew[n++] = pick;
            }
            float arrive = 0.0f;
            for (int c = 0; c < n; ++c) arrive = std::max(arrive, std::max(fr[crew[c]], t) + dist(crew[c], g));
            const float start = std::max(arrive, avail[gi]);
            const float done = start + g.hp / (kDps * static_cast<float>(n)) + 5.0f;
            if (done > horizon) continue;
            float s = g.val / ((done - t) * static_cast<float>(n));
            if (noise > 0.0f) s *= 1.0f + noise * (2.0f * plan_rand() - 1.0f);
            if (s > best_s) {
                best_s = s, best = static_cast<int>(gi), best_done = done, best_n = n;
                for (int c = 0; c < 3; ++c) best_crew[c] = crew[c];
            }
        }
        if (best < 0) {
            fr[i] = horizon;
            continue;
        }
        for (int c = 0; c < best_n; ++c) {
            const int k = best_crew[c];
            if (p.count[k] < kPlanSteps) {
                p.steps[k][p.count[k]][0] = best;
                p.steps[k][p.count[k]][1] = static_cast<int>(std::max(fr[k], t));
                ++p.count[k];
            }
            fr[k] = best_done;
            px[k] = G[static_cast<std::size_t>(best)].x;
            py[k] = G[static_cast<std::size_t>(best)].y;
        }
        avail[static_cast<std::size_t>(best)] = best_done + static_cast<float>(G[static_cast<std::size_t>(best)].respawn);
        p.value += G[static_cast<std::size_t>(best)].val;
    }
    return p;
}

// Builds the plan once (static) and returns its draft-memory bytes: 'P', slots, then per slot a step count and
// (group index, start round / 2) pairs.
const std::vector<std::uint8_t>& team_plan_bytes(std::uint32_t size) {
    static std::vector<std::uint8_t> bytes;
    static bool done = false;
    if (done) return bytes;
    done = true;
    try {
        constexpr float kHp[6] = {1350, 2400, 120, 120, 20000, 5000};
        std::uint32_t n = 0;
        if (bc::detail::sdk_map_num_camp_groups(&n) != 0 || n == 0 || n > 200) return bytes;
        std::vector<std::uint32_t> handles(n);
        if (bc::detail::sdk_map_camp_groups(handles.data(), n, &n) != 0) return bytes;
        std::vector<PlanGroup> G;
        G.reserve(n);
        for (std::uint32_t k = 0; k < n; ++k) {
            bc::detail::camp_group_info info{};
            bc::detail::sdk_map_camp_group(handles[k], &info);
            std::uint32_t cnt = 0;
            bc::detail::sdk_map_camp_group_num_camps(handles[k], &cnt);
            std::vector<std::uint32_t> members(std::max<std::uint32_t>(cnt, 1));
            if (cnt) bc::detail::sdk_map_camp_group_camps(handles[k], members.data(), cnt, &cnt);
            float x = 0, y = 0, hp = 0;
            for (std::uint32_t m = 0; m < cnt; ++m) {
                bc::detail::camp_info spec{};
                if (bc::detail::sdk_map_camp_info(members[m], &spec) != 0) continue;
                x += static_cast<float>(spec.x), y += static_cast<float>(spec.y);
                hp += spec.type >= 0 && spec.type < 6 ? kHp[spec.type] : 5000.0f;
            }
            std::int32_t respawn = 60;
            bc::detail::sdk_bc_camp_group_max_respawn(handles[k], &respawn);
            PlanGroup g{cnt ? x / static_cast<float>(cnt) : -1000.0f, cnt ? y / static_cast<float>(cnt) : -1000.0f, hp,
                static_cast<float>(info.gold) + 10.0f * static_cast<float>(info.gems), hp <= 1500 ? 1 : hp <= 3000 ? 2 : 3, std::max(respawn, 10)};
            if (cnt == 0 || hp > 6000.0f) g.val = 0.0f, g.n = 99; // big jobs and empty groups stay with the usual logic
            G.push_back(g);
        }
        float sx = 0, sy = 0, sn = 0;
        for (vec2 p : bc::map::spawn_region(team::ally).positions()) sx += static_cast<float>(p.x), sy += static_cast<float>(p.y), ++sn;
        if (sn == 0) return bytes;
        sx /= sn, sy /= sn;
        const int ncham = static_cast<int>(std::min<std::uint32_t>(std::max<std::uint32_t>(size, 1), kPlanSlots));
        Plan best = plan_once(G, sx, sy, ncham, 0.0f);
        for (int r = 0; r < A2_DP_ROLLOUTS && bc::fuel_remaining() > 150000; ++r) {
            const Plan p = plan_once(G, sx, sy, ncham, 0.3f);
            if (p.value > best.value) best = p;
        }
        bytes.push_back('P');
        bytes.push_back(static_cast<std::uint8_t>(ncham));
        for (int k = 0; k < ncham; ++k) {
            bytes.push_back(static_cast<std::uint8_t>(best.count[k]));
            for (int s = 0; s < best.count[k]; ++s) {
                bytes.push_back(static_cast<std::uint8_t>(best.steps[k][s][0]));
                bytes.push_back(static_cast<std::uint8_t>(std::min(255, best.steps[k][s][1] / 2)));
            }
        }
    } catch (...) {
        bytes.clear();
    }
    return bytes;
}
} // namespace
#endif

#if A2_MLDRAFT
#include "draft_net.h"
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
#ifdef A2_MLD_DEBUG
        std::printf("MLDFEAT");
        for (int i = 0; i < 16; ++i) std::printf(" %.4f", f[i]);
        std::printf("%c", 10);
#endif
    }
    const auto ours = bc::draft::current_draft(team::ally), theirs = bc::draft::current_draft(team::enemy);
    bool taken[12] = {};
    for (auto c : ours) if (static_cast<int>(c) >= 0 && static_cast<int>(c) < 12) taken[static_cast<int>(c)] = true;
#if !V55_DRAFT_LEGAL
    for (auto c : theirs) if (static_cast<int>(c) >= 0 && static_cast<int>(c) < 12) taken[static_cast<int>(c)] = true;
#endif
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
#if A2_MLPLAN
    // Our last pick: choose the game plan for this comp on this map (net with the plan one-hot set) and pass it to the
    // champions in draft-memory byte 7 (0x80 | plan). Written before the brain header's 6-byte write, which keeps it.
    if (j >= sz) {
        int plan = 0;
        float plan_z = -1e30f;
        for (int k = 0; k < 8; ++k) {
            for (int i = 0; i < dn::kIn; ++i) x[i] = 0.0f;
            for (int i = 0; i < 16; ++i) x[i] = feat[i];
            for (auto o : ours) x[16 + static_cast<int>(o)] = 1.0f;
            x[16 + best] = 1.0f;
            for (auto o : theirs) x[28 + static_cast<int>(o)] = 1.0f;
            x[40 + std::min(std::max(sz, 3), 5) - 3] = 1.0f;
            x[43] = first ? 1.0f : 0.0f;
            x[44] = 1.0f;
            x[45 + k] = 1.0f;
            float z = dn::b2;
            for (int h = 0; h < dn::kHid; ++h) {
                float a = dn::b1[h];
                for (int i = 0; i < dn::kIn; ++i) a += dn::W1[i * dn::kHid + h] * x[i];
                z += dn::w2[h] * fast_tanh(a);
            }
            if (z > plan_z) plan_z = z, plan = k;
        }
        std::vector<std::uint8_t> mem(8, 0);
        mem[7] = static_cast<std::uint8_t>(0x80 | plan);
        bc::draft_memory = mem;
    }
#endif
    return true;
}
} // namespace
#endif


#if (V58_DIRECTOR && V58_ROUTE && V58_CARRY_SHOP && V58_DRAFT) || (V58_DRAFT >= 2 && V58_CAPTURE_STAND >= 2)
namespace {
bool economy_draft_supported() {
    static int cached = -1;
    if (cached >= 0) return cached != 0;
    cached = 0;
    namespace api = bc::detail;
    std::uint32_t count = 0;
    if (api::sdk_map_num_camp_groups(&count) != 0 || count > 48) return false;
    const auto home = bc::map::spawn_region(team::ally), enemy = bc::map::spawn_region(team::enemy);
    bc::bitboard visited;
    bc::distance_field distance;
    distance.compute(bc::map::walls() | bc::map::holes() | bc::map::altars() | enemy, home, visited);
    float ex = 0, ey = 0, en = 0;
    for (vec2 p : enemy.positions()) ex += p.x, ey += p.y, en += 1.0f;
    if (en <= 0) return false;
    ex /= en; ey /= en;
    std::vector<std::uint32_t> groups(count);
    if (api::sdk_map_camp_groups(groups.data(), count, &count) != 0) return false;
    api::camp_design designs[6]{};
    bool loaded[6] = {};
    for (auto handle : groups) {
        api::camp_group_info info{};
        if (api::sdk_map_camp_group(handle, &info) != 0 || info.gold == 0) continue;
        std::uint32_t n = 0;
        if (api::sdk_map_camp_group_num_camps(handle, &n) != 0 || n == 0) continue;
        std::vector<std::uint32_t> members(n);
        if (api::sdk_map_camp_group_camps(handle, members.data(), n, &n) != 0) continue;
        float hp = 0.0f;
        int travel = kUnreach;
        float enemy_distance = 0.0f;
        for (auto member : members) {
            api::camp_info camp{};
            if (api::sdk_map_camp_info(member, &camp) != 0 || camp.type < 0 || camp.type >= 6) continue;
            if (!loaded[camp.type]) {
                if (api::sdk_camp_design(camp.type, &designs[camp.type]) != 0) continue;
                loaded[camp.type] = true;
            }
            hp += designs[camp.type].base_stats.base_health;
            const int d = fdist(distance, {camp.x, camp.y});
            if (d < travel) travel = d, enemy_distance = std::max(std::fabs(camp.x - ex), std::fabs(camp.y - ey));
        }
        if (hp >= 2400.0f && hp <= 6500.0f && travel <= 30 && travel <= 0.9f * enemy_distance) return cached = 1;
    }
    return false;
}
} // namespace
#endif

void play_draft() {
    const auto chosen = bc::draft::current_draft(team::ally);
    [[maybe_unused]] std::uint32_t size = 0;
    try {
        size = bc::draft::team_size();
    } catch (...) {
    }
#if V67_OPENING || V67_META >= 0
    if (v67meta::draft(size)) {
        const auto facts = read_facts();
        unsigned flags = facts.monolith ? 2u : 0u;
        const float area = static_cast<float>(bc::map::width() * bc::map::height());
        if (area > 0 && facts.gems / area >= NOVA_RACE_DENS) flags |= 1u;
        brain::record_draft(size, facts.max_gems, flags);
        return;
    }
#endif
#if (V58_DIRECTOR && V58_ROUTE && V58_CARRY_SHOP && V58_DRAFT) || (V58_DRAFT >= 2 && V58_CAPTURE_STAND >= 2)
    if (economy_draft_supported()) {
        constexpr cd meta[] = {cd::vesper_vale, cd::heart_of_ruin, cd::vendetta, cd::ryth, cd::marcella, cd::tavi};
        if (pick_from(meta, chosen)) {
            const auto facts = read_facts();
            unsigned flags = facts.monolith ? 2u : 0u;
            const float area = static_cast<float>(bc::map::width() * bc::map::height());
            if (area > 0 && facts.gems / area >= NOVA_RACE_DENS) flags |= 1u;
            brain::record_draft(size, facts.max_gems, flags);
            return;
        }
    }
#endif
#if A2_MLDRAFT
    // ML draft on maps the lineup tables do not know (A2_MLDRAFT 2: unknown maps only; 1: every map).
    bool ml_done = false;
    try {
        bool known = false;
        if (A2_MLDRAFT == 2) {
            std::uint32_t n = 0;
            bc::detail::sdk_map_num_camp_groups(&n);
            known = nova_map_id(bc::map::width(), bc::map::height(), size, static_cast<int>(n)) >= 0;
        }
        ml_done = !known && ml_draft_pick(size);
    } catch (...) {
        ml_done = false; // fall back to the lineup tables
    }
#endif
#if A2_DPLAN
    // The team opening plan sits after the brain header at byte 8. Submitting writes from byte 0 and keeps later bytes,
    // so the plan (with an empty header) goes first and the brain header's 6-byte write below leaves it intact.
    try {
        const auto& plan = team_plan_bytes(size);
        if (!plan.empty() && 8 + plan.size() <= bc::constants::draft_memory_bytes) {
            std::vector<std::uint8_t> all(8, 0);
            all.insert(all.end(), plan.begin(), plan.end());
            bc::draft_memory = all;
        }
    } catch (...) {
    }
#endif
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
#if A2_MLDRAFT
    if (ml_done) return; // picked (and planned) by the net above; the header is written
#endif
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
#if A44_MOBILITY_DRAFT
        try {
            if (NOVA_ALL_LINEUP < 0 && needs_gap_crossings()) {
                constexpr cd mobile[] = {cd::vendetta, cd::heart_of_ruin, cd::ren, cd::vesper_vale,
                    cd::cassi_and_issac, cd::varg, cd::ryth, cd::stellar, cd::tavi, cd::marcella, cd::willow, cd::prism};
                if (pick_from(mobile, chosen)) return;
            }
        } catch (...) {
            // Preserve the existing draft if optional map analysis is unavailable.
        }
#endif
        int li = NOVA_ALL_LINEUP >= 0 ? NOVA_ALL_LINEUP
                                      : (mid >= 0 ? kNovaMapLineup[mid] : NOVA_FALLBACK_LINEUP);
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
#ifdef NOVA_UNSEEN_LIST
        // Draft search hook: an explicit pick list for unknown, spread-out maps (where comp 2 would go).
        {
            constexpr cd kUnseen[] = {NOVA_UNSEEN_LIST};
            if (mid < 0 && li == NOVA_FALLBACK_LINEUP && pick_from(kUnseen, chosen, skip)) return;
        }
#endif
#if defined(NOVA_UNSEEN3) && defined(NOVA_UNSEEN4) && defined(NOVA_UNSEEN5)
        // Per-pick-count lists for unknown, spread-out maps (the best set differs by draft size).
        {
            constexpr cd k3[] = {NOVA_UNSEEN3}, k4[] = {NOVA_UNSEEN4}, k5[] = {NOVA_UNSEEN5};
            if (mid < 0 && li == NOVA_FALLBACK_LINEUP) {
                if (size == 3 && pick_from(k3, chosen, skip)) return;
                if (size == 4 && pick_from(k4, chosen, skip)) return;
                if (size >= 5 && pick_from(k5, chosen, skip)) return;
            }
        }
#endif
        if (li >= 0 && li < kNumLineups && pick_from(kLineups[li], chosen, skip)) return;
    }
#ifdef APEX_MAPINFO
    {
        static bool printed = false;
        if (!printed) {
            printed = true;
            std::printf("MAPINFO %d %d %u\n", bc::map::width(), bc::map::height(), size);
        }
    }
#endif
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
#ifdef APEX_DRAFT_T3
    if (size == 3 && pick_from(kT3, chosen)) return;
#endif
#ifdef APEX_DRAFT_T4
    if (size == 4 && pick_from(kT4, chosen)) return;
#endif
#ifdef APEX_DRAFT_T5
    if (size == 5 && pick_from(kT5, chosen)) return;
#endif
#ifdef APEX_DRAFT_LIST
    if (pick_from(kOverride, chosen)) return;
#endif
    pick_from(kPresets[APEX_DRAFT], chosen);
}

#if A2_SPARSE_BUILD
// Agent 2 (A2_SPARSE_BUILD): total camp gems per map tile, from the same map facts as the draft (-1 = unreadable).
// Sparse maps (expanse .16, corners .18; every other official map >= .32) are farming races with few fights.
float a2_gem_density() {
    static float cached = -2.0f; // first call from Bot::init (turn one): camps are full, so live gems = design gems
    if (cached > -1.5f) return cached;
    const MapFacts f = read_facts();
    int w = 0, h = 0;
    try {
        w = bc::map::width(), h = bc::map::height();
    } catch (...) {
    }
    cached = f.ok && w > 0 && h > 0 ? static_cast<float>(f.gems) / static_cast<float>(w * h) : -1.0f;
    return cached;
}
#endif
