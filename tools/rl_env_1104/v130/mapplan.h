// CL_PLAN (10 Nov 2026): map analysis on the draft's 10M-fuel turn. Nothing here is a per-map table: it reads any map.
// Gem and gold clusters (120 health, no attack, 7 gems per tile, back after 50 rounds) give ~10x the gems per health of any
// monster and cost no health, so a champion living beside a dense patch of them near an altar keeps a steady income
// while crews take the big camps (the "split up, then regroup" pattern of the top teams). The analysis:
//   1. harmless gem groups, real walking distances between them and to both spawns and the nearest altar ring;
//   2. sweep regions grown from the densest seeds (groups within CL_PLAN_RADIUS steps join while the rate holds);
//   3. per region: gems per round one sweeper can hold (a nearest-neighbour loop of walk + kill + capture against the
//      respawn time), discounted for the enemy side and for a far altar; capacity 2 when the loop is long;
//   4. 1-2 sweepers (team size >= CL_PLAN_TEAM1 / CL_PLAN_TEAM2) for the best regions above CL_PLAN_MIN rate.
// The plan rides in draft memory from byte kOff (brain::record_draft writes bytes 0-5 only, after it).
#pragma once
#include "common.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <vector>

#ifndef CL_PLAN
#define CL_PLAN 1 // bits: 1 sweepers, 2 effort terms (heal and bank trips), 4 carry risk, 8 sweeper banking
#endif
#ifndef CL_PLAN_FLOOR
#define CL_PLAN_FLOOR 4000000 // draft fuel left for the rest of the draft (v220's own map read runs after this)
#endif
#ifndef CL_PLAN_RADIUS
#define CL_PLAN_RADIUS 16 // walking steps from a region's seed to its other groups
#endif
#ifndef CL_PLAN_MIN
#define CL_PLAN_MIN 0.16f // gems per round a sweeper must expect from a region
#endif
#ifndef CL_PLAN_GOLDW
#define CL_PLAN_GOLDW 0.15f // gem value of one gold in region rates (gold clusters buy shards and emblems)
#endif
#ifndef CL_PLAN_TEAM1
#define CL_PLAN_TEAM1 3 // draft picks for one sweeper (Cassi and Issac: one pick, two bodies)
#endif
#ifndef CL_PLAN_TEAM2
#define CL_PLAN_TEAM2 5 // draft picks for two sweepers
#endif
#ifndef CL_SW_IN
#define CL_SW_IN 3.0f // sweeper: value of its region's groups
#endif
#ifndef CL_SW_OUT
#define CL_SW_OUT 0.35f // sweeper: value of groups outside its region
#endif
#ifndef CL_SW_OTHER
#define CL_SW_OTHER 0.6f // others: value of a living sweeper's region groups
#endif
#ifndef CL_SW_WAITW
#define CL_SW_WAITW 0.4f // sweeper: weight of respawn waits inside its region
#endif
#ifndef CL_SW_CARRY
#define CL_SW_CARRY 28 // sweeper: bank once carrying this many gems (CL_PLAN bit 8)
#endif
#ifndef CL_HEAL0
#define CL_HEAL0 6.0f // CL_PLAN bit 2: turns of a heal trip besides the walk home
#endif
#ifndef CL_BANK_C
#define CL_BANK_C 40.0f // CL_PLAN bit 2: gems per bank trip that share its walk
#endif
#ifndef CL_RISK
#define CL_RISK 0.004f // CL_PLAN bit 4: carried-gem risk per gem per step of enemy-side margin
#endif

namespace mapplan {
inline constexpr std::size_t kOff = 16;
inline constexpr std::uint8_t kMagic = 0xC7;
inline constexpr int kMaxRegions = 2;
inline constexpr int kMaxEntries = 120;

// Draft side: analyse the map and submit [0..kOff) zero + plan. Call before brain::record_draft on a turn with fuel.
inline bool draft_write(unsigned team_size) {
    if (!(CL_PLAN & 1)) return false;
    if (bc::fuel_remaining() < static_cast<std::uint64_t>(CL_PLAN_FLOOR) + 2000000ull) return false;
    namespace d = cambc::detail;
    std::uint32_t n = 0;
    if (d::sdk_map_num_camp_groups(&n) != 0 || n == 0 || n > 400) return false;
    std::vector<std::uint32_t> hs(n);
    if (d::sdk_map_camp_groups(hs.data(), n, &n) != 0) return false;
    struct G {
        std::vector<vec2> camps;
        bc::bitboard tiles;
        int gems = 0, gold = 0, respawn = 50, dus = kUnreach, dthem = kUnreach, dalt = kUnreach;
    };
    std::vector<G> gs;
    for (std::uint32_t k = 0; k < n; ++k) {
        d::camp_group_info info{};
        if (d::sdk_map_camp_group(hs[k], &info) != 0) return false;
        if (info.gems == 0 && info.gold == 0) continue;
        std::uint32_t members = 0;
        if (d::sdk_map_camp_group_num_camps(hs[k], &members) != 0 || members == 0 || members > 64) continue;
        std::uint32_t spawns[64];
        if (d::sdk_map_camp_group_camps(hs[k], spawns, members, &members) != 0) continue;
        G g;
        bool harmless = true;
        for (std::uint32_t m = 0; m < members; ++m) {
            d::camp_info spec{};
            if (d::sdk_map_camp_info(spawns[m], &spec) != 0) {
                harmless = false;
                break;
            }
            const auto t = static_cast<bc::camp_type>(spec.type);
            if (t != bc::camp_type::gem_cluster && t != bc::camp_type::gold_cluster) harmless = false;
            const vec2 at{spec.x, spec.y};
            g.camps.push_back(at);
            g.tiles.set(at, true);
        }
        if (!harmless || g.camps.empty()) continue;
        g.gems = static_cast<int>(info.gems);
        g.gold = static_cast<int>(info.gold);
        std::int32_t rs = 0;
        if (d::sdk_bc_camp_group_max_respawn(hs[k], &rs) == 0 && rs > 0) g.respawn = rs;
        gs.push_back(std::move(g));
        if (gs.size() >= static_cast<std::size_t>(kMaxEntries)) break;
    }
    const int ng = static_cast<int>(gs.size());
    std::vector<std::uint8_t> buf(kOff + 8, 0);
    buf[kOff] = kMagic;
    buf[kOff + 1] = 1; // version
    if (ng == 0) {
        bc::draft_memory = buf;
        return true;
    }
    const auto walls_holes = bc::map::walls() | bc::map::holes() | bc::map::altars();
    const auto ours = bc::map::spawn_region(team::ally), theirs = bc::map::spawn_region(team::enemy);
    const auto blocked = walls_holes | theirs;
    bc::bitboard visited;
    bc::distance_field f_us, f_them, f_alt, f_g;
    f_us.compute(blocked, ours, visited);
    f_them.compute(walls_holes | ours, theirs, visited);
    bc::bitboard ring;
    ring.clear();
    for (vec2 a : bc::map::altars().positions()) ring.draw_chebyshev(a, static_cast<float>(bc::constants::submit_gems_range));
    ring &= ~blocked;
    const bool have_alt = !ring.is_empty();
    if (have_alt) f_alt.compute(blocked, ring, visited);
    for (auto& g : gs)
        for (vec2 c : g.camps) {
            g.dus = std::min<int>(g.dus, fdist(f_us, c));
            g.dthem = std::min<int>(g.dthem, fdist(f_them, c));
            if (have_alt) g.dalt = std::min<int>(g.dalt, fdist(f_alt, c));
        }
    // Pairwise walking distances (one field per group, read at the other groups' camps).
    std::vector<std::uint16_t> dist(static_cast<std::size_t>(ng * ng), static_cast<std::uint16_t>(kUnreach));
    for (int a = 0; a < ng; ++a) {
        if (bc::fuel_remaining() < static_cast<std::uint64_t>(CL_PLAN_FLOOR)) return false;
        f_g.compute(blocked, gs[a].tiles, visited);
        for (int b = 0; b < ng; ++b) {
            int best = kUnreach;
            for (vec2 c : gs[b].camps) best = std::min<int>(best, fdist(f_g, c));
            dist[static_cast<std::size_t>(a * ng + b)] = static_cast<std::uint16_t>(best);
        }
    }
    // Sweep regions, grown from each seed: its neighbours within CL_PLAN_RADIUS steps join nearest first while the
    // loop's rate holds (value per round over a nearest-neighbour tour of walk + kill + capture, at least the respawn).
    auto val_of = [&](int i) {
        const auto& g = gs[static_cast<std::size_t>(i)];
        return static_cast<float>(g.gems) + CL_PLAN_GOLDW * static_cast<float>(g.gold);
    };
    auto dd = [&](int a, int b) { return static_cast<int>(dist[static_cast<std::size_t>(a * ng + b)]); };
    auto loop_of = [&](const std::vector<int>& m) {
        std::vector<char> seen(m.size(), 0);
        std::size_t cur = 0;
        for (std::size_t i = 1; i < m.size(); ++i)
            if (gs[static_cast<std::size_t>(m[i])].dus < gs[static_cast<std::size_t>(m[cur])].dus) cur = i;
        const std::size_t start = cur;
        seen[cur] = 1;
        int walk = 0, work = 0;
        for (std::size_t step = 1; step < m.size(); ++step) {
            std::size_t nxt = m.size();
            int nd = kUnreach;
            for (std::size_t i = 0; i < m.size(); ++i)
                if (!seen[i] && dd(m[cur], m[i]) < nd) nd = dd(m[cur], m[i]), nxt = i;
            if (nxt == m.size()) return static_cast<int>(kUnreach);
            walk += nd;
            seen[nxt] = 1;
            cur = nxt;
        }
        if (m.size() > 1) walk += std::min(dd(m[cur], m[start]), 60);
        for (int i : m) work += 5 + 3 * static_cast<int>(gs[static_cast<std::size_t>(i)].camps.size());
        return walk + work;
    };
    auto resp_of = [&](const std::vector<int>& m) {
        int r = 1;
        for (int i : m) r = std::max(r, gs[static_cast<std::size_t>(i)].respawn);
        return r;
    };
    struct R {
        std::vector<int> members;
        float rate = 0, value = 0, val = 0;
        int loop = 0, dalt = kUnreach, dus = kUnreach, cap = 1;
    };
    // Seeds: the groups with the most value within reach (at most 24 of them).
    std::vector<std::pair<float, int>> seeds;
    for (int s = 0; s < ng; ++s) {
        if (gs[static_cast<std::size_t>(s)].dus >= kUnreach) continue;
        float near = val_of(s);
        for (int h = 0; h < ng; ++h)
            if (h != s && dd(s, h) <= CL_PLAN_RADIUS) near += val_of(h);
        seeds.push_back({near, s});
    }
    std::sort(seeds.begin(), seeds.end(), [](const auto& a, const auto& b) { return a.first > b.first || (a.first == b.first && a.second < b.second); });
    if (seeds.size() > 24) seeds.resize(24);
    std::vector<char> excl(static_cast<std::size_t>(ng), 0);
    auto grow = [&](int s) {
        std::vector<int> nb;
        for (int h = 0; h < ng; ++h)
            if (h != s && !excl[static_cast<std::size_t>(h)] && dd(s, h) <= CL_PLAN_RADIUS) nb.push_back(h);
        std::sort(nb.begin(), nb.end(), [&](int a, int b) { return dd(s, a) < dd(s, b) || (dd(s, a) == dd(s, b) && a < b); });
        if (nb.size() > 14) nb.resize(14);
        R r;
        r.members = {s};
        r.val = val_of(s);
        r.loop = loop_of(r.members);
        r.rate = r.val / static_cast<float>(std::max(r.loop, resp_of(r.members)));
        for (int h : nb) {
            r.members.push_back(h);
            const float v = r.val + val_of(h);
            const int l = loop_of(r.members);
            const float rt = l >= kUnreach ? 0.0f : v / static_cast<float>(std::max(l, resp_of(r.members)));
            if (rt >= r.rate * 0.98f) r.val = v, r.rate = rt, r.loop = l;
            else r.members.pop_back();
        }
        float margin = 0.0f;
        for (int i : r.members) {
            const auto& g = gs[static_cast<std::size_t>(i)];
            r.dalt = std::min(r.dalt, g.dalt);
            r.dus = std::min(r.dus, g.dus);
            margin += static_cast<float>(std::min(g.dthem, 200) - std::min(g.dus, 200));
        }
        margin /= static_cast<float>(r.members.size());
        const float side = margin >= -2.0f ? 1.0f : 0.5f;
        const float alt = r.dalt >= kUnreach ? 0.3f : 1.0f / (1.0f + std::max(0.0f, static_cast<float>(r.dalt) - 6.0f) / 10.0f);
        r.value = r.rate * side * alt;
        r.cap = static_cast<float>(r.loop) >= 1.6f * static_cast<float>(resp_of(r.members)) ? 2 : 1;
        return r;
    };
    auto good = [&](const R& r) { return r.value >= CL_PLAN_MIN && (r.members.size() >= 2 || r.val >= 21.0f); };
    std::vector<R> cands;
    for (const auto& sd : seeds) {
        if (bc::fuel_remaining() < static_cast<std::uint64_t>(CL_PLAN_FLOOR)) break;
        R r = grow(sd.second);
        if (good(r)) cands.push_back(std::move(r));
    }
    std::sort(cands.begin(), cands.end(), [](const R& a, const R& b) { return a.value > b.value; });
    const int want = static_cast<int>(team_size) >= CL_PLAN_TEAM2 ? 2 : static_cast<int>(team_size) >= CL_PLAN_TEAM1 ? 1 : 0;
    std::vector<int> used; // indices into cands
    int assign[2] = {0, 0}; // 1-based into used
    int sweepers = 0;
    if (want >= 1 && !cands.empty()) used.push_back(0), assign[0] = 1, sweepers = 1;
    if (want >= 2 && sweepers == 1) {
        if (cands[0].cap >= 2) assign[1] = 1, sweepers = 2;
        else {
            // The second sweeper's region is grown again without the first region's groups.
            for (int i : cands[0].members) excl[static_cast<std::size_t>(i)] = 1;
            R best;
            for (const auto& sd : seeds) {
                if (excl[static_cast<std::size_t>(sd.second)] || bc::fuel_remaining() < static_cast<std::uint64_t>(CL_PLAN_FLOOR)) continue;
                R r = grow(sd.second);
                if (good(r) && r.value > best.value) best = std::move(r);
            }
            if (!best.members.empty()) {
                cands.push_back(std::move(best));
                used.push_back(static_cast<int>(cands.size()) - 1);
                assign[1] = 2;
                sweepers = 2;
            }
        }
    }
    // Encode: [kOff] magic, version, sweepers, region of sweeper 0 / 1 (1-based into the used list), used regions,
    // then per used region: rate x 100, altar steps; then entry count and entries (x, y, used region).
    buf.assign(kOff, 0);
    for (std::size_t i = 0; i < kOff && i < bc::draft_memory.size(); ++i) buf[i] = static_cast<std::uint8_t>(bc::draft_memory[i]);
    buf.push_back(kMagic);
    buf.push_back(1);
    buf.push_back(static_cast<std::uint8_t>(sweepers));
    buf.push_back(static_cast<std::uint8_t>(assign[0]));
    buf.push_back(static_cast<std::uint8_t>(assign[1]));
    buf.push_back(static_cast<std::uint8_t>(used.size()));
    for (int r : used) {
        buf.push_back(static_cast<std::uint8_t>(std::min(255.0f, cands[static_cast<std::size_t>(r)].rate * 100.0f)));
        buf.push_back(static_cast<std::uint8_t>(std::min(255, cands[static_cast<std::size_t>(r)].dalt)));
    }
    int count = 0;
    for (int r : used) count += static_cast<int>(cands[static_cast<std::size_t>(r)].members.size());
    buf.push_back(static_cast<std::uint8_t>(std::min(count, 255)));
    for (std::size_t u = 0; u < used.size(); ++u)
        for (int i : cands[static_cast<std::size_t>(used[u])].members) {
            const vec2 c = gs[static_cast<std::size_t>(i)].camps[0];
            buf.push_back(static_cast<std::uint8_t>(c.x));
            buf.push_back(static_cast<std::uint8_t>(c.y));
            buf.push_back(static_cast<std::uint8_t>(u + 1));
        }
    bc::draft_memory = buf;
    debug_block({
        std::printf("CLPLAN team %u groups %d cands %zu sweepers %d fuel_left %llu", team_size, ng, cands.size(), sweepers, static_cast<unsigned long long>(bc::fuel_remaining()));
        for (int r : used) {
            const auto& c = cands[static_cast<std::size_t>(r)];
            std::printf(" | rate %.2f n %zu val %.0f loop %d alt %d us %d cap %d", c.rate, c.members.size(), c.val, c.loop, c.dalt, c.dus, c.cap);
        }
        std::printf("\n");
    });
    return true;
}

// Game side: the decoded plan.
struct Plan {
    bool ok = false;
    int sweepers = 0;
    int region_of_sweeper[2] = {0, 0}; // 1-based used-region index, 0 = none
    float rate[kMaxRegions + 1] = {};
    int dalt[kMaxRegions + 1] = {};
    std::vector<std::array<std::uint8_t, 3>> entries;
};
inline Plan read() {
    Plan p;
    try {
        if (bc::draft_memory.size() < kOff + 8) return p;
        auto at = [&](std::size_t i) { return static_cast<std::uint8_t>(bc::draft_memory[kOff + i]); };
        if (at(0) != kMagic || at(1) != 1) return p;
        p.sweepers = std::min<int>(at(2), 2);
        p.region_of_sweeper[0] = at(3);
        p.region_of_sweeper[1] = at(4);
        const int used = std::min<int>(at(5), kMaxRegions);
        std::size_t i = 6;
        for (int u = 1; u <= used; ++u) {
            p.rate[u] = static_cast<float>(at(i)) / 100.0f;
            p.dalt[u] = at(i + 1);
            i += 2;
        }
        const int count = at(i++);
        for (int e = 0; e < count && kOff + i + 2 < bc::draft_memory.size(); ++e, i += 3) p.entries.push_back({at(i), at(i + 1), at(i + 2)});
        p.ok = true;
    } catch (...) {
        p.ok = false;
    }
    return p;
}
} // namespace mapplan
