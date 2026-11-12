// World model: caches terrain and camp groups once, then tracks what each champion sees.
#include "world.h"
#include "a2map.h"

#include <cstring>

namespace d = cambc::detail;

namespace {
// Tile -> camp index, open addressing. Namespace-scope arrays start zeroed for free; filling a
// full-map table costs 1 fuel per byte (40k on 100x100).
constexpr std::uint32_t kCampSlots = 2048;
std::uint16_t camp_key[kCampSlots]; // tile index + 1, 0 = empty
std::int16_t camp_val[kCampSlots];
std::uint32_t slot_of(std::uint32_t key) { return (key * 2654435761u) >> 21; }
void put_camp(std::uint32_t key, int ci) {
    std::uint32_t s = slot_of(key);
    while (camp_key[s] != 0 && camp_key[s] != key) s = (s + 1) & (kCampSlots - 1);
    camp_key[s] = static_cast<std::uint16_t>(key);
    camp_val[s] = static_cast<std::int16_t>(ci);
}
int find_camp(std::uint32_t key) {
    for (std::uint32_t s = slot_of(key);; s = (s + 1) & (kCampSlots - 1)) {
        if (camp_key[s] == key) return camp_val[s];
        if (camp_key[s] == 0) return -1;
    }
}
} // namespace

float GroupRec::hp_left(const std::vector<CampRec>& all) const {
    switch (state) {
    case GroupState::reward: return 0.0f;
    case GroupState::respawning: return max_hp;
    case GroupState::alive: break;
    }
    float total = 0;
    for (int i : camps)
        if (!all[i].dead) total += all[i].hp;
    return total;
}

void World::init() {
    std::uint64_t f0 = bc::fuel_remaining();
    auto mark = [&](const char* what) {
        PROF_CHECK(what);
        if (APEX_PROFILE) {
            std::printf("INIT %s %llu\n", what, static_cast<unsigned long long>(f0 - bc::fuel_remaining()));
            f0 = bc::fuel_remaining();
        }
    };
    width = bc::map::width();
    height = bc::map::height();
    ally_spawn = bc::map::spawn_region(team::ally);
    enemy_spawn = bc::map::spawn_region(team::enemy);
    spawn_tiles = ally_spawn.positions();
    static_blocked = bc::map::walls() | bc::map::holes() | bc::map::altars() | enemy_spawn;
    enemy_spawn_zone.clear();
    for (vec2 p : enemy_spawn.positions()) enemy_spawn_zone.draw_chebyshev(p, 2.0f);
    altars = bc::map::altars().positions();
    bushes = bc::map::bushes();
    bush_label.reset(new std::uint16_t[static_cast<std::size_t>(width * height)]); // not zeroed: filling costs fuel
    mark("boards");

    // Tribute range is Chebyshev 1 around each altar.
    altar_ring.clear();
    for (vec2 a : altars) altar_ring.draw_chebyshev(a, static_cast<float>(bc::constants::submit_gems_range));
    altar_ring &= ~static_blocked;
    if (tune::kSafeAltars) {
        // Altars beside the enemy spawn are traps: enemies step out of a full heal onto a channelling
        // carrier. Use them only if they are the only altars.
        bc::bitboard near_enemy;
        near_enemy.clear();
        for (vec2 p : enemy_spawn.positions()) near_enemy.draw_chebyshev(p, 5.0f);
        const bc::bitboard safe = altar_ring & ~near_enemy;
        if (!safe.is_empty()) altar_ring = safe;
    }
    bc::bitboard visited;
    walk_terrain = static_blocked;
    spawn_field.compute(walk_terrain, ally_spawn, visited);
    mark("spawn_field");

    // Camp groups are loaded once, through the raw engine calls: the SDK's map::camp_groups() builds
    // several vectors per group and cost 40-50k fuel on large maps (allocation is dear here).
    // Bits are set straight into board memory rather than through host calls.
    std::uint32_t n_groups = 0;
    d::check(d::sdk_map_num_camp_groups(&n_groups));
    std::vector<std::uint32_t> handles(n_groups);
    d::check(d::sdk_map_camp_groups(handles.data(), n_groups, &n_groups));
    groups.reserve(n_groups);
    camps.reserve(static_cast<std::size_t>(n_groups) * 4);
    d::camp_design designs[16]{};
    bool have_design[16]{};
    for (std::uint32_t k = 0; k < n_groups; ++k) {
        const std::uint32_t h = handles[k];
        d::camp_group_info info{};
        d::check(d::sdk_map_camp_group(h, &info));
        std::int32_t respawn = 0;
        d::check(d::sdk_bc_camp_group_max_respawn(h, &respawn));
        std::uint32_t members = 0;
        d::check(d::sdk_map_camp_group_num_camps(h, &members));
        std::uint32_t spawns[64];
        members = std::min<std::uint32_t>(members, 64);
        d::check(d::sdk_map_camp_group_camps(h, spawns, members, &members));
        GroupRec& rec = groups.emplace_back();
        rec.handle = h;
        rec.gems = info.gems;
        rec.gold = info.gold;
        rec.respawn = respawn;
        rec.camps.reserve(members);
        for (std::uint32_t m = 0; m < members; ++m) {
            d::camp_info spec{};
            d::check(d::sdk_map_camp_info(spawns[m], &spec));
            const int kind = spec.type & 15;
            if (!have_design[kind]) {
                d::check(d::sdk_camp_design(spec.type, &designs[kind]));
                have_design[kind] = true;
            }
            const d::camp_design& design = designs[kind];
            const vec2 at{spec.x, spec.y};
            const auto type = static_cast<bc::camp_type>(spec.type);
            CampRec cr{d::handle_access::make_camp(static_cast<bc::handle_camp_t>(spawns[m]), static_cast<bc::handle_camp_group_t>(h),
                           type, at),
                at, type, design.base_stats.base_health, design.base_stats.base_strength, design.base_stats.base_health};
            cr.range = std::max(1, design.base_stats.base_attack_range);
            rec.camps.push_back(static_cast<int>(camps.size()));
            set_bit(rec.tiles, at);
            rec.max_hp += cr.max_hp;
            rec.strength += cr.strength;
            if (cr.strength > 0) rec.harmless = false;
            camps.push_back(cr);
        }
    }
    mark("group_loop");
    camp_group.assign(camps.size(), -1);
    camp_tiles_all.clear();
    for (std::size_t gi = 0; gi < groups.size(); ++gi)
        for (int ci : groups[gi].camps) {
            camp_group[ci] = static_cast<std::int16_t>(gi);
            put_camp(static_cast<std::uint32_t>(camps[ci].pos.y * width + camps[ci].pos.x) + 1, ci);
            set_bit(camp_tiles_all, camps[ci].pos);
        }
    group_visible.assign(groups.size(), 0);
    camp_visible.assign(camps.size(), 0);
    mark("tables");
#if A2_ALTARFIX & 1
    {
        // Altar access: a tile beside an altar that holds a camp is blocked while the camp lives, and one our spawn
        // cannot walk to is no access at all. boss-battle's only access tiles are monolith tiles: every carrier walked
        // up to them and waited out the game. With no open access tile we stop banking (no_bank) and keep farming.
        bc::bitboard ring;
        ring.clear();
        for (vec2 a : altars) ring.draw_chebyshev(a, static_cast<float>(bc::constants::submit_gems_range));
        ring &= ~static_blocked;
        ring &= ~camp_tiles_all;
        for (vec2 t : ring.positions())
            if (fdist(spawn_field, t) == kUnreach) ring.set(t, false);
        if (ring.is_empty()) {
            // Gated altars: access tiles that hold camps open while their camp is dead (boss-battle's monoliths;
            // our farming kills them by round ~1000 and their capture alone is 400 gems).
            no_bank = true;
            bc::bitboard gates;
            gates.clear();
            for (vec2 a : altars) gates.draw_chebyshev(a, static_cast<float>(bc::constants::submit_gems_range));
            gates &= ~static_blocked;
            gates &= camp_tiles_all;
            for (vec2 t : gates.positions())
                if (fdist(spawn_field, t) != kUnreach) {
                    const int ci = find_camp(static_cast<std::uint32_t>(t.y * width + t.x) + 1);
                    if (ci >= 0) gate_camps.push_back(ci);
                }
            altar_gated = !gate_camps.empty();
        } else {
            const bc::bitboard safe = ring & altar_ring; // keep the safe-altar choice where it still has access
            altar_ring = safe.is_empty() ? ring : safe;
        }
    }
#endif
    if (APEX_PROFILE) std::printf("INIT size %dx%d groups %zu camps %zu\n", width, height, groups.size(), camps.size());
    if (APEX_LOG)
        for (std::size_t gi = 0; gi < groups.size(); ++gi)
            std::printf("GROUP %zu at (%d,%d) members %zu gems %u gold %u harmless %d\n", gi, camps[groups[gi].camps[0]].pos.x,
                camps[groups[gi].camps[0]].pos.y, groups[gi].camps.size(), groups[gi].gems, groups[gi].gold, groups[gi].harmless);
}

int World::bush_cluster(vec2 p) {
    if (p.x < 0 || p.y < 0 || p.x >= width || p.y >= height || !bit(bushes, p)) return -1;
    if (!bit(bush_labeled, p)) {
#if A2_TEL
        const std::uint64_t a2_f0 = bc::fuel_remaining();
        const std::uint32_t a2_r0 = bc::round_number();
        int a2_size = 0;
        struct A2Done {
            const std::uint64_t& f0;
            const std::uint32_t& r0;
            int& size;
            ~A2Done() {
                a2tel::bump(4u * 4096 + static_cast<std::uint32_t>(std::min(size / 50, 63) * 64) +
                    static_cast<std::uint32_t>(std::min<std::uint64_t>(a2tel::spent(f0, r0) / 2000, 63)));
            }
        } a2_done{a2_f0, a2_r0, a2_size};
#endif
        // Label the whole 8-connected cluster on first use (8-connectivity is the cautious
        // choice: a bigger cluster never claims a hiding spot the engine would not give us).
        const auto id = static_cast<std::uint16_t>(bush_clusters++);
#if A2_BUSH_FAST
        if (!a2map::slow_bush()) {
        // Same tiles, same id; a fixed explicit stack instead of a growing vector (allocation and push_back cost
        // ~800 fuel per tile in the original, which put 50-120k labelling spikes inside ward_ahead/counter_ambush).
        static std::uint32_t stack[kBushStack];
        int sp = 0;
        stack[sp++] = static_cast<std::uint32_t>(p.x) | static_cast<std::uint32_t>(p.y) << 16;
        set_bit(bush_labeled, p);
        while (sp > 0) {
            const std::uint32_t t = stack[--sp];
            const int x = static_cast<int>(t & 0xFFFF), y = static_cast<int>(t >> 16);
#if A2_TEL
            ++a2_size;
#endif
            bush_label[static_cast<std::size_t>(y * width + x)] = id;
            const int x0 = x > 0 ? x - 1 : 0, x1 = x + 1 < width ? x + 1 : x;
            const int y0 = y > 0 ? y - 1 : 0, y1 = y + 1 < height ? y + 1 : y;
            for (int yy = y0; yy <= y1; ++yy)
                for (int xx = x0; xx <= x1; ++xx) {
                    const vec2 q{xx, yy};
                    if (!bit(bushes, q) || bit(bush_labeled, q)) continue;
                    set_bit(bush_labeled, q);
                    if (sp < kBushStack) stack[sp++] = static_cast<std::uint32_t>(xx) | static_cast<std::uint32_t>(yy) << 16;
                }
        }
#if A2_CHECK
        { // the original flood from p over bush tiles: every tile it reaches must carry this id, and no other tile may
            // (kind 18: 0 equal, 1 different)
            bc::bitboard seen;
            seen.clear();
            std::vector<vec2> st{p};
            set_bit(seen, p);
            bool ok = true;
            int reached = 0;
            while (!st.empty()) {
                const vec2 c = st.back();
                st.pop_back();
                ++reached;
                ok &= bit(bush_labeled, c) && bush_label[static_cast<std::size_t>(c.y * width + c.x)] == id;
                for (vec2 dlt : kDirs) {
                    const vec2 q = c + dlt;
                    if (q.x < 0 || q.y < 0 || q.x >= width || q.y >= height || !bit(bushes, q) || bit(seen, q)) continue;
                    set_bit(seen, q);
                    st.push_back(q);
                }
            }
            int labelled_with_id = 0;
            for (int i = 0; i < width * height; ++i)
                labelled_with_id += bit(bush_labeled, vec2{i % width, i / width}) && bush_label[static_cast<std::size_t>(i)] == id;
            a2tel::bump(18u * 4096 + (ok && labelled_with_id == reached ? 0u : 1u));
        }
#endif
        } else
#endif
        { // v34's labelling (A2_MAP_PROFILE keeps it on the maps where its fuel cost cut bush hiding short)
        std::vector<vec2> stack{p};
        set_bit(bush_labeled, p);
        while (!stack.empty()) {
            const vec2 c = stack.back();
            stack.pop_back();
#if A2_TEL
            ++a2_size;
#endif
            bush_label[static_cast<std::size_t>(c.y * width + c.x)] = id;
            for (vec2 d : kDirs) {
                const vec2 q = c + d;
                if (q.x < 0 || q.y < 0 || q.x >= width || q.y >= height) continue;
                if (!bit(bushes, q) || bit(bush_labeled, q)) continue;
                set_bit(bush_labeled, q);
                stack.push_back(q);
            }
        }
        }
    }
    return bush_label[static_cast<std::size_t>(p.y * width + p.x)];
}

void World::cluster_board(vec2 p, bc::bitboard& out) {
    out.clear();
    const int id = bush_cluster(p);
    if (id < 0) return;
    std::vector<vec2> stack{p};
    set_bit(out, p);
    while (!stack.empty()) {
        const vec2 c = stack.back();
        stack.pop_back();
        for (vec2 d : kDirs) {
            const vec2 q = c + d;
            if (q.x < 0 || q.y < 0 || q.x >= width || q.y >= height) continue;
            if (!bit(bushes, q) || bit(out, q)) continue;
            set_bit(out, q);
            stack.push_back(q);
        }
    }
}

void World::vision_from(vec2 viewer, bc::bitboard& out) {
    bc::bitboard opaque = bc::map::walls() | bushes;
    bc::bitboard own;
    cluster_board(viewer, own);
    opaque &= ~own;
    opaque.shadow_cast_into(viewer, 8, out);
    // Bush tiles outside the viewer's cluster are never visible to it.
    bc::bitboard other_bushes = bushes & ~own;
    out &= ~other_bushes;
    out |= own;
}

const std::uint16_t* World::pair_row(int from, bool may_build) {
    if (!has_field(from)) return nullptr;
    if (pair_rows.size() != groups.size()) pair_rows.resize(groups.size());
    auto& row = pair_rows[static_cast<std::size_t>(from)];
    if (row.empty()) {
        if (!may_build) return nullptr;
        row.resize(groups.size());
        const auto& f = group_dist[static_cast<std::size_t>(field_slot[from])];
        for (std::size_t g = 0; g < groups.size(); ++g) {
            int d = kUnreach;
            for (int ci : groups[g].camps) d = std::min<int>(d, fdist(f, camps[ci].pos));
            row[g] = static_cast<std::uint16_t>(d);
        }
    }
    return row.data();
}

std::vector<int> World::awake_camps_near(vec2 q) const {
    std::vector<int> out;
    if (!bit(hot_zone, q)) return out; // hot_zone covers the reach of every damaged live camp
    for (std::size_t ci = 0; ci < camps.size(); ++ci) {
        const auto& c = camps[ci];
        if (!c.dead && c.strength > 0 && c.hp < c.max_hp && cheb(c.pos, q) <= c.range) out.push_back(static_cast<int>(ci));
    }
    return out;
}

int World::group_to_group(int from, int to) {
    const std::uint16_t* row = pair_row(from, true);
    return row ? row[static_cast<std::size_t>(to)] : kUnreach;
}

// A2_BRIDGES: a champion with a dash plans over one-tile hole gaps (holes with open ground on two opposite sides; the
// travel dash in follow_field jumps them). islands is a ring around both spawns plus 44 islands, each one dash from a
// neighbour; without this our whole team farmed one gold group beside spawn for 2,000 rounds.
// At least a quarter of the map's gems lie in groups our spawn cannot walk to (islands: about 60%). Measured once, on
// the walking field (before any bridges).
bool World::value_cut_off() {
    if (cut_off_map < 0) {
        std::uint32_t total = 0, cut = 0;
        for (const auto& g : groups) {
            total += g.gems;
            bool reach = false;
            for (int ci : g.camps) reach |= fdist(spawn_field, camps[ci].pos) != kUnreach;
            if (!reach) cut += g.gems;
        }
        cut_off_map = total > 0 && cut * 4 >= total ? 1 : 0;
    }
    return cut_off_map == 1;
}

void World::enable_bridges() {
    // Only where walking leaves real value out of reach (value_cut_off): on ordinary maps the hole shortcuts only made
    // dashers slower and deadlier.
    if (!value_cut_off()) return;
    const bc::bitboard open = ~static_blocked;
    bridges = bc::map::holes() &
        ((open.shift_right(1) & open.shift_right(-1)) | (open.shift_up(1) & open.shift_up(-1)) |
            (open.shift_right(1).shift_up(1) & open.shift_right(-1).shift_up(-1)) |
            (open.shift_right(1).shift_up(-1) & open.shift_right(-1).shift_up(1)));
    if (bridges.is_empty()) return;
    bridges_on = true;
    walk_terrain = static_blocked & ~bridges;
    bc::bitboard visited;
    spawn_field.compute(walk_terrain, ally_spawn, visited);
    altar_ready = false;
}

bool World::ensure_altar_field() {
    if (altar_ready) return true;
    bc::bitboard visited;
    altar_field.compute(walk_terrain, altar_ring, visited);
#if A2_ALTARFIX & 4
    // The way around camp tiles (live camps block like walls; the-farm's shortest way to its central altars runs
    // through a wolf group in a wall gap, where whole teams waited out the game). Access tiles stay goals. Carriers
    // walk it where it exists; distances and decisions keep using altar_field.
    bc::bitboard visited2;
    altar_walk.compute(walk_terrain | (camp_tiles_all & ~altar_ring), altar_ring, visited2);
#endif
    altar_ready = true;
    return true;
}

bool World::ensure_enemy_field() {
    if (enemy_ready) return true;
    bc::bitboard terrain = bc::map::walls() | bc::map::holes() | bc::map::altars();
    bc::bitboard visited;
    enemy_field.compute(terrain, enemy_spawn, visited);
    group_margin.assign(groups.size(), 0);
    for (std::size_t gi = 0; gi < groups.size(); ++gi) {
        int ours = kUnreach, theirs = kUnreach;
        for (int ci : groups[gi].camps) {
            ours = std::min<int>(ours, fdist(spawn_field, camps[ci].pos));
            theirs = std::min<int>(theirs, fdist(enemy_field, camps[ci].pos));
        }
        group_margin[gi] = static_cast<std::int16_t>(std::clamp(theirs - ours, -999, 999));
    }
    enemy_ready = true;
    return true;
}

void World::prepare_field_order() {
    if (!field_order.empty() || groups.empty()) return;
    group_dist.reserve(groups.size());
    field_slot.assign(groups.size(), -1);
    field_ptr.assign(groups.size(), nullptr);
    // Nearest to our spawn first; packed keys sort cheaply.
    std::vector<std::uint32_t> keys;
    keys.reserve(groups.size());
    for (std::size_t gi = 0; gi < groups.size(); ++gi) {
        int d = kUnreach;
        for (int ci : groups[gi].camps) d = std::min<int>(d, fdist(spawn_field, camps[ci].pos));
        keys.push_back(static_cast<std::uint32_t>(d) << 12 | static_cast<std::uint32_t>(gi));
    }
    std::sort(keys.begin(), keys.end());
    field_order.reserve(keys.size());
    for (std::uint32_t k : keys) field_order.push_back(static_cast<int>(k & 0xFFF));
}

bool World::build_next_group_field(std::uint64_t budget) {
    if (fields_ready()) return false;
    prepare_field_order();
    // Cost is (levels + 16) x chunks (measured to 0.3%), plus a small fixed overhead. Cap the search
    // depth so the build fits the budget; tiles beyond the cap read as unreachable.
    const std::uint64_t chunks = field_chunks();
    if (budget < 3000) return false;
    const std::uint64_t levels = (budget - 3000) / chunks;
    if (levels < 40) return false;
    const std::uint64_t cap = std::min<std::uint64_t>(levels - 24, 1000);
    if (cap < 150 && cap < static_cast<std::uint64_t>(width + height)) return false;
    const int gi = field_order[fields_built];
    bc::bitboard visited;
    group_dist.emplace_back();
    group_dist.back().compute(walk_terrain, groups[gi].tiles, visited, static_cast<std::uint16_t>(cap));
    field_slot[gi] = static_cast<int>(group_dist.size()) - 1;
    field_ptr[gi] = group_dist.back().ptr(); // the heap buffer stays put when the vector grows
    ++fields_built;
    return true;
}

int World::group_of_camp_tile(vec2 p) const {
    if (p.x < 0 || p.y < 0 || p.x >= width || p.y >= height) return -1;
    const int ci = find_camp(static_cast<std::uint32_t>(p.y * width + p.x) + 1);
    return ci < 0 ? -1 : camp_group[ci];
}

void World::apply_event(int gi, int ready_round, int round) {
    if (gi < 0 || gi >= static_cast<int>(groups.size())) return;
    if (!group_visible.empty() && group_visible[static_cast<std::size_t>(gi)]) return; // our own eyes win
    auto& g = groups[static_cast<std::size_t>(gi)];
    if (ready_round > round) {
        if (g.state == GroupState::respawning && std::abs(g.respawn_round - ready_round) <= 1) return;
        g.state = GroupState::respawning;
        g.respawn_round = ready_round;
        for (int i : g.camps) {
            camps[i].hp = camps[i].max_hp;
            camps[i].dead = false;
        }
    } else if (g.state != GroupState::alive && g.seen_round < ready_round) {
        g.state = GroupState::alive;
        g.available_since = ready_round;
        for (int i : g.camps) {
            camps[i].hp = camps[i].max_hp;
            camps[i].dead = false;
        }
    }
}

void World::observe_groups(int round) {
    PROF(groups);
    // One intersection plus table lookups instead of a bitboard AND per group (that cost ~25k fuel).
    std::fill(group_visible.begin(), group_visible.end(), 0);
    std::fill(camp_visible.begin(), camp_visible.end(), 0);
    bc::bitboard seen = visible;
    seen &= camp_tiles_all;
    if (!seen.is_empty())
        for (vec2 p : seen.positions()) {
            const int ci = find_camp(static_cast<std::uint32_t>(p.y * width + p.x) + 1);
            if (ci < 0) continue;
            camp_visible[ci] = 1;
            group_visible[camp_group[ci]] = 1;
        }
    for (std::size_t gi = 0; gi < groups.size(); ++gi) {
        auto& g = groups[gi];
        if (!group_visible[gi]) {
            // Not in view: advance predictions.
            if (g.state == GroupState::respawning && round >= g.respawn_round) {
                g.state = GroupState::alive;
                for (int i : g.camps) {
                    camps[i].hp = camps[i].max_hp;
                    camps[i].dead = false;
                }
            } else if (g.state == GroupState::reward && round - g.reward_seen > 12) {
                // Someone almost certainly captured it; assume the respawn clock started.
                g.state = GroupState::respawning;
                g.respawn_round = g.reward_seen + tune::kCaptureTime + g.respawn;
            }
            continue;
        }
        g.seen_round = round;
        std::uint32_t st = 0;
        if (d::sdk_camp_group_state(g.handle, &st) != 0) continue;
        if (st == 1) {
            g.state = GroupState::alive;
            for (int i : g.camps) {
                d::camp_state cs{};
                const int code = d::sdk_camp(static_cast<std::uint32_t>(static_cast<bc::handle_camp_t>(camps[i].camp)), &cs);
                if (code == 0) {
                    camps[i].hp = cs.health;
                    camps[i].dead = cs.health <= 0;
                } else if (camp_visible[i]) {
                    camps[i].dead = true;
                }
            }
        } else if (st == 2) {
            g.state = GroupState::reward;
            g.reward_seen = round;
        } else if (st == 3) {
            std::int32_t timer = 0;
            d::sdk_camp_group_cooldown(g.handle, &timer);
            if (APEX_EVENTS && (g.state != GroupState::respawning || std::abs(g.respawn_round - (round + timer)) > 1))
                pending_events.push_back(static_cast<int>(gi));
            g.state = GroupState::respawning;
            g.respawn_round = round + timer;
            for (int i : g.camps) {
                camps[i].hp = camps[i].max_hp;
                camps[i].dead = false;
            }
        }
    }
}

// A2_ALTARFIX gated altars: bank through the access tiles whose camp is dead (or whose group waits for capture or
// respawn); the altar field is rebuilt when the set of open tiles changes.
void World::update_altar_gates() {
    if (!altar_gated) return;
    bc::bitboard open;
    open.clear();
    for (int ci : gate_camps) {
        const auto& g = groups[static_cast<std::size_t>(camp_group[ci])];
        if (g.state != GroupState::alive || camps[ci].dead) open.set(camps[ci].pos, true);
    }
    if (open.is_empty()) {
        no_bank = true;
        return;
    }
    if (!no_bank && open == altar_ring) return;
    no_bank = false;
    altar_ring = open;
    altar_ready = false;
}

void World::observe_champions() {
    PROF(champs);
    enemies.clear();
    allies.clear();
    const auto me = bc::self();
    for (vec2 p : bc::vision::champion_tiles().positions()) {
        std::uint32_t handle = 0;
        if (d::sdk_champion_at(p.x, p.y, &handle) != 0) continue;
        d::champion_info info{};
        if (d::sdk_champion(handle, &info) != 0) continue;
        auto unit = d::handle_access::make_champion(static_cast<bc::handle_champion_t>(handle));
        if (info.team == d::sdk_my_team()) {
            if (unit == me) continue;
            allies.push_back(AllyRec{unit, p, info.health, info.max_health, info.strength, info.attack_range, handle, info.focus,
                static_cast<bc::champion_type>(info.type)});
        } else {
            std::uint32_t gems = 0;
            d::sdk_champion_gems(handle, &gems);
            auto state = static_cast<std::uint32_t>(info.state);
#if V80_RECALL
            // Five of the top twelve teams start a recall at the end of nearly every turn and cancel it at the start of
            // the next (research/proxy/README.md). A recalling champion cannot act, so our search, caster micro, kiting
            // and escape code took them for harmless and misjudged every fight against them. A recall counts only once
            // its channel time has gone down between two rounds (a real one runs 5 turn ends; a restarted one never
            // progresses).
            if (state & (1u << 1)) {
                const int now = static_cast<int>(bc::round_number());
                RecallSeen* t = nullptr;
                for (auto& r : recall_seen)
                    if (r.id == handle) t = &r;
                if (!t) {
                    t = &recall_seen[0];
                    for (auto& r : recall_seen)
                        if (r.round < t->round) t = &r;
                    *t = RecallSeen{};
                    t->id = handle;
                }
                if (t->round != now) {
                    std::int32_t left = -1;
                    if (d::sdk_champion_channel_time(handle, &left) != 0) left = -1;
                    const bool fresh = t->round == now - 1 && t->left > 0 && left >= 0;
                    t->genuine = fresh && (left < t->left || (t->genuine && left <= t->left));
                    t->left = left;
                    t->round = now;
                }
                if (!t->genuine) state &= ~(1u << 1);
            } else {
                for (auto& r : recall_seen)
                    if (r.id == handle) r.left = 0, r.genuine = false;
            }
#endif
            enemies.push_back(EnemyRec{unit, p, info.health, info.max_health, info.strength, info.focus,
                info.attack_range, static_cast<bc::champion_type>(info.type), static_cast<int>(gems), handle, state});
        }
    }
}

void World::add_sighting(vec2 p, int round) {
    for (auto& s : sightings)
        if (cheb(s.pos, p) <= 1) {
            if (round >= s.round) {
                s.pos = p;
                s.round = round;
            }
            return;
        }
    sightings.push_back({p, round});
}

void World::update_beliefs(int round, std::uint64_t min_fuel) {
    if (beliefs.empty()) {
        enemy_walk = ~(bc::map::walls() | bc::map::holes() | bc::map::altars() | ally_spawn);
        for (const auto& e : bc::champions(team::enemy)) {
            Belief b;
            b.handle = static_cast<std::uint32_t>(static_cast<bc::handle_champion_t>(e));
            b.reach = enemy_spawn;
            b.area = b.reach.count();
            b.round = round;
            beliefs.push_back(std::move(b));
        }
    }
    bc::bitboard unseen = ~visible;
    bc::bitboard h, t;
    for (auto& b : beliefs) {
        std::int32_t alive = 1;
        if (d::sdk_champion_is_alive(b.handle, &alive) == 0 && !alive) {
            b.alive = false;
            b.area = 0;
            b.round = round;
            continue;
        }
        const EnemyRec* seen = nullptr;
        for (const auto& e : enemies)
            if (e.id == b.handle) seen = &e;
        if (seen) {
            b.reach.clear();
            set_bit(b.reach, seen->pos);
            b.area = 1;
            b.round = round;
            b.alive = true;
            continue;
        }
        if (!b.alive) { // back from the dead: on its spawn
            b.alive = true;
            b.reach = enemy_spawn;
            b.area = b.reach.count();
            b.round = round;
            continue;
        }
        int steps = round - b.round;
        if (steps <= 0 || bc::fuel_remaining() < min_fuel) continue; // a later turn catches up
        if (steps > 6) {
            b.reach = enemy_walk;
            steps = 0;
        }
        for (int k = 0; k < steps; ++k) {
            b.reach.shift_right_into(1, h);
            h |= b.reach;
            b.reach.shift_right_into(-1, t);
            h |= t;
            h.shift_up_into(1, b.reach);
            b.reach |= h;
            h.shift_up_into(-1, t);
            b.reach |= t;
            b.reach &= enemy_walk;
        }
        b.reach &= unseen;
        b.round = round;
        b.area = b.reach.count();
        if (b.area == 0) { // it went somewhere we did not model (teleport, recall): anywhere unseen
            b.reach = enemy_walk;
            b.reach &= unseen;
            b.area = b.reach.count();
        }
    }
}

float World::expected_enemies(vec2 p, int radius) {
    bc::bitboard box, tmp;
    box.clear();
    box.draw_chebyshev(p, static_cast<float>(radius));
    float e = 0.0f;
    for (const auto& b : beliefs) {
        if (!b.alive || b.area == 0) continue;
        tmp = b.reach;
        tmp &= box;
        e += static_cast<float>(tmp.count()) / static_cast<float>(b.area);
    }
    return e;
}

bc::bitboard World::threat_zone(int round, int max_age, float radius) const {
    bc::bitboard zone;
    zone.clear();
    for (const auto& s : sightings)
        if (round - s.round <= max_age) zone.draw_chebyshev(s.pos, radius);
    return zone;
}

void World::update(int round) {
    {
        PROF(w_vis);
        visible = bc::vision::visible_tiles();
        unit_tiles = bc::vision::champion_tiles() | bc::vision::camp_tiles() | bc::vision::teleport_tiles();
    }
    PROF_CHECK("w_vis");
    observe_groups(round);
#if A2_ALTARFIX & 1
    update_altar_gates();
#endif
    PROF_CHECK("w_groups");
    PROF(w_hot);
    hot_zone.clear();
    for (const auto& g : groups) {
        if (g.state != GroupState::alive || g.harmless) continue;
        // A group wakes as a whole: once any member is damaged or dead, its healthy members hit back too.
        bool awake = false;
        if (tune::kAwakeZone)
            for (int i : g.camps)
                if (camps[i].dead || camps[i].hp < camps[i].max_hp) {
                    awake = true;
                    break;
                }
        for (int i : g.camps) {
            const auto& c = camps[i];
            if (!c.dead && c.strength > 0 && (c.hp < c.max_hp || awake)) hot_zone.draw_chebyshev(c.pos, static_cast<float>(c.range));
        }
    }
    PROF_CHECK("w_hot");
    observe_champions();
    PROF_CHECK("w_champs");
    PROF(w_tail);
    warded_clusters.clear();
    if (tune::kWardAware) {
        const bc::bitboard wt = bc::vision::ward_tiles(team::enemy);
        if (!wt.is_empty())
            for (vec2 p : wt.positions()) {
                const int c = bush_cluster(p);
                if (c >= 0) warded_clusters.push_back(c);
            }
    }
    PROF_CHECK("w_ward");
    std::erase_if(sightings, [&](const Sighting& s) { return round - s.round > 20; });
    for (const auto& e : enemies) add_sighting(e.pos, round);
    PROF_CHECK("w_sight");
#if A2_FASTGRP
    // Groups with a camp within 4 tiles of a visible enemy, through one bitboard: the triple loop below (enemies x
    // groups x camps) cost 30-44k fuel a turn on maps with many camps (yellow-brick-road's 60 gold clusters), where
    // half the turns ran out of fuel and team A banked nothing all game. Same groups marked.
    if (!enemies.empty()) {
        bc::bitboard near;
        near.clear();
        for (const auto& e : enemies) near.draw_chebyshev(e.pos, 4.0f);
        near &= camp_tiles_all;
        if (!near.is_empty())
            for (vec2 p : near.positions()) {
                const int ci = find_camp(static_cast<std::uint32_t>(p.y * width + p.x) + 1);
                if (ci >= 0) groups[static_cast<std::size_t>(camp_group[ci])].enemy_round = round;
            }
    }
#else
    for (const auto& e : enemies)
        for (auto& g : groups)
            for (int i : g.camps)
                if (cheb(camps[i].pos, e.pos) <= 4) {
                    g.enemy_round = round;
                    break;
                }
#endif
}
