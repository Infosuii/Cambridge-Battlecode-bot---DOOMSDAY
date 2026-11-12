// Observation capture glue (agent C): fills nnobs::RawTurn from state the bot has ALREADY computed this turn.
// Rules: no distance-field builds, no bush labelling, no vision casts, no allocation, no exceptions. The only engine
// calls are O(1) host queries with a fixed count per turn: self champion record, self ward resources, both teams'
// submitted gems, is_alive per champion (<= 12), gems per visible ally (<= 5), and once per game the enemy handle
// list, champion identities (public types) and spawn boxes. Everything else is read from Bot/World members through the
// friend struct nn_obs_access declared in bot.h. Compiled only when some head exists (NN_ANY_HEAD).
#include "nn_config.h"

#if NN_ANY_HEAD
#include "bot.h"
#include "nn_obs.h"

namespace d = cambc::detail;

namespace {

constexpr int kSlots = 8;       // Bot::ally_handle capacity
constexpr int kFine = 16;       // per-observed-round history (hp, gems)
constexpr int kCoarse = 32;     // every >= 10 rounds (scores): covers >= 310 rounds
constexpr int kDeaths = 16;

struct Seen {
    std::int32_t round = -1; // -1 never / forgotten
    std::int32_t x = 0, y = 0, range = 0, gems = -1, state = 0;
    float hp = 0, max_hp = 0, strength = 0, focus = 0;
};
struct Mem {
    std::int32_t observed_round = -1000000;
    bool init = false;
    std::int32_t n_enemy = 0;
    std::uint32_t enemy_handle[nnobs::kEnemyRows] = {};
    std::int32_t enemy_type[nnobs::kEnemyRows] = {};
    std::int32_t ally_type[kSlots] = {};
    std::int8_t enemy_alive[nnobs::kEnemyRows] = {};
    std::int8_t ally_alive[kSlots] = {};
    Seen enemy[nnobs::kEnemyRows];
    Seen ally[kSlots];
    d::aabb own_box{}, enemy_box{};
    std::int32_t abs_team = 0;
    // history rings (newest at index (n - 1) % size)
    std::int32_t fine_round[kFine] = {}, fine_gems[kFine] = {};
    float fine_hp[kFine] = {};
    int fine_n = 0;
    std::int32_t coarse_round[kCoarse] = {}, coarse_ally[kCoarse] = {}, coarse_enemy[kCoarse] = {};
    int coarse_n = 0;
    std::int32_t ally_death[kDeaths] = {}, enemy_death[kDeaths] = {};
    int ally_deaths = 0, enemy_deaths = 0;
    std::int32_t alive_us = 0, alive_them = 0, ally_score = 0, enemy_score = 0;
};
constinit Mem g_mem{};

inline bool on_map(const World& w, vec2 p) { return p.x >= 0 && p.y >= 0 && p.x < w.width && p.y < w.height; }
inline std::int32_t field_tiles(const bc::distance_field& f, const World& w, vec2 p) {
    if (!on_map(w, p)) return -1;
    const std::uint16_t v = fdist(f, p);
    return v == kUnreach ? -2 : static_cast<std::int32_t>(v);
}
inline int count_recent(const std::int32_t* ring, int n, std::int32_t now, int window) {
    int c = 0;
    for (int i = 0; i < (n < kDeaths ? n : kDeaths); ++i) c += now - ring[i] < window;
    return c;
}

} // namespace

struct nn_obs_access {
    static void init_once(const Bot& b) {
        Mem& m = g_mem;
        if (m.init) return;
        m.init = true;
        m.abs_team = d::sdk_my_team();
        std::uint32_t n = 0, hs[16];
        if (d::sdk_num_enemies(&n) == 0 && n > 0 && d::sdk_enemies(hs, n < 16 ? n : 16, &n) == 0) {
            m.n_enemy = static_cast<std::int32_t>(n < static_cast<std::uint32_t>(nnobs::kEnemyRows) ? n : nnobs::kEnemyRows);
            for (int i = 0; i < m.n_enemy; ++i) {
                m.enemy_handle[i] = hs[i];
                d::champion_identity id{};
                m.enemy_type[i] = d::sdk_champion_identity(hs[i], &id) == 0 ? id.type : -1;
                m.enemy_alive[i] = 1;
            }
        }
        for (int s = 0; s < kSlots; ++s) {
            m.ally_type[s] = -1;
            m.ally_alive[s] = 1;
            if (s >= b.team_size) continue;
            d::champion_identity id{};
            if (d::sdk_champion_identity(b.ally_handle[static_cast<std::size_t>(s)], &id) == 0) m.ally_type[s] = id.type;
        }
        d::sdk_spawn_region(m.abs_team, &m.own_box);
        d::sdk_spawn_region(1 - m.abs_team, &m.enemy_box);
    }

    static vec2 spawn_centre() {
        const auto& bx = g_mem.own_box;
        return vec2{(bx.min_x + bx.max_x - 1) / 2, (bx.min_y + bx.max_y - 1) / 2};
    }

    // Memory tick: idempotent within a round.
    static void observe(const Bot& b) {
        if (!b.inited) return;
        init_once(b);
        Mem& m = g_mem;
        const std::int32_t now = b.round;
        if (m.observed_round == now) return;
        m.observed_round = now;
        const World& w = b.w;
        const bool dead = b.was_dead;
        // Public alive flags and death transitions.
        int alive_them = 0;
        for (int i = 0; i < m.n_enemy; ++i) {
            std::int32_t a = 1;
            if (d::sdk_champion_is_alive(m.enemy_handle[i], &a) != 0) a = m.enemy_alive[i];
            if (m.enemy_alive[i] && !a) {
                m.enemy_death[m.enemy_deaths % kDeaths] = now;
                ++m.enemy_deaths;
                m.enemy[i].round = -1; // dead: its last position means nothing now
            }
            m.enemy_alive[i] = static_cast<std::int8_t>(a != 0);
            alive_them += a != 0;
        }
        int alive_us = 0;
        const int ts = b.team_size < kSlots ? b.team_size : kSlots;
        for (int s = 0; s < ts; ++s) {
            std::int32_t a = 1;
            if (d::sdk_champion_is_alive(b.ally_handle[static_cast<std::size_t>(s)], &a) != 0) a = m.ally_alive[s];
            if (m.ally_alive[s] && !a) {
                m.ally_death[m.ally_deaths % kDeaths] = now;
                ++m.ally_deaths;
                m.ally[s].round = -1;
            }
            m.ally_alive[s] = static_cast<std::int8_t>(a != 0);
            alive_us += a != 0;
        }
        m.alive_us = alive_us;
        m.alive_them = alive_them;
        std::uint32_t sa = 0, se = 0;
        d::sdk_bc_submitted_gems(static_cast<std::uint32_t>(m.abs_team), &sa);
        d::sdk_bc_submitted_gems(static_cast<std::uint32_t>(1 - m.abs_team), &se);
        m.ally_score = static_cast<std::int32_t>(sa);
        m.enemy_score = static_cast<std::int32_t>(se);
        // Last-seen tables: World::enemies/allies are this turn's vision only when we are alive (a dead champion's
        // World was last updated on its last living turn).
        if (!dead) {
            for (const auto& e : w.enemies)
                for (int i = 0; i < m.n_enemy; ++i)
                    if (m.enemy_handle[i] == e.id) {
                        m.enemy[i] = Seen{now, e.pos.x, e.pos.y, e.range, e.gems, static_cast<std::int32_t>(e.state), e.hp, e.max_hp,
                            e.strength, e.focus};
                        break;
                    }
            for (const auto& a : w.allies)
                for (int s = 0; s < ts; ++s)
                    if (b.ally_handle[static_cast<std::size_t>(s)] == a.id) {
                        std::uint32_t g = 0;
                        const std::int32_t gems = d::sdk_champion_gems(a.id, &g) == 0 ? static_cast<std::int32_t>(g) : -1;
                        m.ally[s] = Seen{now, a.pos.x, a.pos.y, a.range, gems, 0, a.hp, a.max_hp, a.strength, a.focus};
                        break;
                    }
        }
        // History.
        const int fi = m.fine_n % kFine;
        m.fine_round[fi] = now;
        m.fine_hp[fi] = dead ? 0.0f : b.hp;
        m.fine_gems[fi] = dead ? 0 : b.gems;
        ++m.fine_n;
        const int last = (m.coarse_n + kCoarse - 1) % kCoarse;
        if (m.coarse_n == 0 || now - m.coarse_round[last] >= 10) {
            const int ci = m.coarse_n % kCoarse;
            m.coarse_round[ci] = now, m.coarse_ally[ci] = m.ally_score, m.coarse_enemy[ci] = m.enemy_score;
            ++m.coarse_n;
        }
    }

    static bool capture(const Bot& b, nnobs::RawTurn& r) {
        using namespace nnobs;
        if (!b.inited) return false;
        observe(b);
        const Mem& m = g_mem;
        const World& w = b.w;
        const std::int32_t now = b.round;
        const bool dead = b.was_dead;
        r = RawTurn{};
        r.magic = kRawMagic, r.version = kRawVersion, r.schema_hash = kObsSchemaHash, r.size = static_cast<std::uint32_t>(sizeof(RawTurn));
        r.round = now;
        r.max_rounds = static_cast<std::int32_t>(bc::constants::max_rounds);
        r.winning_gems = static_cast<std::int32_t>(bc::constants::winning_gems);
        r.abs_team = m.abs_team;
        r.my_handle = b.my_id;
        r.slot = b.slot;
        r.team_size = b.team_size;
        r.enemy_count = m.n_enemy;
        r.width = w.width, r.height = w.height;
        r.symmetry = static_cast<std::int32_t>(bc::map::symmetry());
        r.n_groups = static_cast<std::int32_t>(w.groups.size());
        r.fields_built = static_cast<std::int32_t>(w.fields_built);
        r.altar_ready = w.altar_ready, r.enemy_ready = w.enemy_ready;
        r.own_spawn_x0 = m.own_box.min_x, r.own_spawn_y0 = m.own_box.min_y, r.own_spawn_x1 = m.own_box.max_x - 1, r.own_spawn_y1 = m.own_box.max_y - 1;
        r.enemy_spawn_x0 = m.enemy_box.min_x, r.enemy_spawn_y0 = m.enemy_box.min_y, r.enemy_spawn_x1 = m.enemy_box.max_x - 1,
        r.enemy_spawn_y1 = m.enemy_box.max_y - 1;

        // ---- self (live record for position/health/state: the Bot snapshot is from the start of the turn)
        d::champion_info info{};
        const bool live = !dead && d::sdk_champion(b.my_id, &info) == 0;
        const vec2 pos = dead ? spawn_centre() : live ? vec2{info.x, info.y} : b.pos;
        r.alive = dead ? 0 : 1;
        r.pos_x = pos.x, r.pos_y = pos.y;
        r.gems = dead ? 0 : b.gems;
        r.gold = b.gold;
        r.attack_range = b.range;
        r.type = static_cast<std::int32_t>(b.type);
        r.state_bits = live ? info.state : 0;
        r.cast_done = b.cast_done, r.heading_home = b.heading_home, r.target_group = b.target_group;
        r.tribute_carry = tune::kTributeCarry;
        {
            d::ward_resources wr{};
            if (!dead && d::sdk_champion_wards(b.my_id, &wr) == 0) r.ward_charges = static_cast<std::int32_t>(wr.charges), r.ward_cooldown = wr.cooldown;
        }
        r.spawn_dist = field_tiles(w.spawn_field, w, pos);
        r.altar_dist = w.altar_ready ? field_tiles(w.altar_field, w, pos) : -1;
        r.enemy_spawn_walk = w.enemy_ready ? field_tiles(w.enemy_field, w, pos) : -1;
        if (on_map(w, pos)) {
            r.in_bush = bit(w.bushes, pos);
            r.on_own_spawn = bit(w.ally_spawn, pos);
            r.in_hot_zone = !dead && bit(w.hot_zone, pos);
            r.in_enemy_zone = bit(w.enemy_spawn_zone, pos);
        }
        for (int s = 0; s < 2; ++s) {
            const auto& sp = b.spells[static_cast<std::size_t>(s)];
            r.spell_present[s] = sp.present;
            r.spell_kind[s] = sp.present ? static_cast<std::int32_t>(sp.kind) : 0;
            r.spell_cooldown[s] = sp.present ? b.cooldown[static_cast<std::size_t>(s)] : 0;
            r.spell_range[s] = sp.range;
        }
        r.hp = dead ? 0.0f : live ? info.health : b.hp;
        r.max_hp = live ? std::max(1.0f, info.max_health) : b.max_hp;
        r.prev_hp = b.prev_hp;
        r.strength = live ? info.strength : b.strength;
        r.focus = live ? info.focus : b.focus;
        r.items = b.my_items();
        r.camp_taken_mult = b.camp_taken_mult, r.camp_dealt_mult = b.camp_dealt_mult;

        // ---- history
        r.hist10_age = r.hist50_age = r.hist200_age = -1;
        for (int k = 1; k <= (m.fine_n < kFine ? m.fine_n : kFine); ++k) {
            const int i = (m.fine_n - k) % kFine;
            if (now - m.fine_round[i] >= 10) {
                r.hist10_age = now - m.fine_round[i], r.hist10_hp = m.fine_hp[i], r.hist10_gems = m.fine_gems[i];
                break;
            }
        }
        for (int k = 1; k <= (m.coarse_n < kCoarse ? m.coarse_n : kCoarse); ++k) {
            const int i = (m.coarse_n - k) % kCoarse;
            const std::int32_t age = now - m.coarse_round[i];
            if (r.hist50_age < 0 && age >= 50) r.hist50_age = age, r.hist50_ally = m.coarse_ally[i], r.hist50_enemy = m.coarse_enemy[i];
            if (age >= 200) {
                r.hist200_age = age, r.hist200_ally = m.coarse_ally[i], r.hist200_enemy = m.coarse_enemy[i];
                break;
            }
        }

        // ---- global
        r.ally_score = m.ally_score, r.enemy_score = m.enemy_score;
        r.alive_us = m.alive_us, r.alive_them = m.alive_them;
        r.ally_deaths_50 = count_recent(m.ally_death, m.ally_deaths, now, 50);
        r.enemy_deaths_50 = count_recent(m.enemy_death, m.enemy_deaths, now, 50);
        r.ally_deaths_total = m.ally_deaths, r.enemy_deaths_total = m.enemy_deaths;
        r.vis_enemies = dead ? 0 : static_cast<std::int32_t>(w.enemies.size());
        r.vis_allies = dead ? 0 : static_cast<std::int32_t>(w.allies.size());
        r.sight_age = -1;
        {
            int best = 1 << 30;
            for (const auto& sg : w.sightings) {
                const int age = now - sg.round;
                if (age < 0) continue;
                r.sight_n5 += age <= 5;
                r.sight_n20 += age <= 20;
                const int dd = cheb(sg.pos, pos);
                if (dd < best) best = dd, r.sight_x = sg.pos.x, r.sight_y = sg.pos.y, r.sight_age = age;
            }
        }
        r.distress_age = -1;
        if (b.distress.pos.x >= 0 && now - b.distress.round >= 0 && now - b.distress.round <= 10)
            r.distress_x = b.distress.pos.x, r.distress_y = b.distress.pos.y, r.distress_age = now - b.distress.round;
        r.enemy_wards = dead ? 0 : static_cast<std::int32_t>(w.warded_clusters.size());

        // ---- objectives: teacher target + 3 nearest other groups (walking distance where a static field exists)
        {
            const int ng = static_cast<int>(w.groups.size());
            auto dist_of = [&](int gi, std::int32_t& walk, std::int32_t& chb) {
                const vec2 a = w.camps[static_cast<std::size_t>(w.groups[static_cast<std::size_t>(gi)].camps[0])].pos;
                chb = cheb(a, pos);
                walk = -1;
                if (w.has_field(gi) && on_map(w, pos)) {
                    const int v = w.group_distance(gi, pos);
                    walk = v == kUnreach ? -2 : v;
                }
            };
            int pick[kObjSlots] = {-1, -1, -1, -1};
            std::int64_t pkey[kObjSlots] = {};
            const int tg = b.target_group >= 0 && b.target_group < ng ? b.target_group : -1;
            pick[0] = tg;
            for (int gi = 0; gi < ng; ++gi) {
                if (gi == tg || w.groups[static_cast<std::size_t>(gi)].camps.empty()) continue;
                std::int32_t wk, ch;
                dist_of(gi, wk, ch);
                const std::int64_t key = (static_cast<std::int64_t>(wk >= 0 ? wk : wk == -2 ? 1 << 20 : ch) << 12) | gi;
                for (int k = 1; k < kObjSlots; ++k)
                    if (pick[k] < 0 || key < pkey[k]) {
                        for (int j = kObjSlots - 1; j > k; --j) pick[j] = pick[j - 1], pkey[j] = pkey[j - 1];
                        pick[k] = gi, pkey[k] = key;
                        break;
                    }
            }
            for (int k = 0; k < kObjSlots; ++k) {
                const int gi = pick[k];
                if (gi < 0 || w.groups[static_cast<std::size_t>(gi)].camps.empty()) continue;
                const GroupRec& g = w.groups[static_cast<std::size_t>(gi)];
                ObjRaw& o = r.obj[k];
                const vec2 a = w.camps[static_cast<std::size_t>(g.camps[0])].pos;
                o.valid = 1, o.group = gi, o.anchor_x = a.x, o.anchor_y = a.y;
                dist_of(gi, o.dist_walk, o.dist_cheb);
                o.gems = static_cast<std::int32_t>(g.gems), o.gold = static_cast<std::int32_t>(g.gold);
                o.state = static_cast<std::int32_t>(g.state);
                o.respawn_in = g.state == GroupState::respawning ? std::max(0, g.respawn_round - now) : 0;
                o.harmless = g.harmless;
                for (int s = 0; s < (b.team_size < kClaimSlots ? b.team_size : kClaimSlots); ++s)
                    o.ally_claims += s != b.slot && b.claim_of(s) == gi;
                o.enemy_age = g.enemy_round > -1000 ? now - g.enemy_round : -1;
                o.hp_left = g.hp_left(w.camps), o.max_hp = g.max_hp;
            }
        }

        // ---- allies (every teammate body, by slot)
        {
            int j = 0;
            const int ts = b.team_size < kSlots ? b.team_size : kSlots;
            for (int s = 0; s < ts && j < kAllyRows; ++s) {
                if (s == b.slot) continue;
                AllyRaw& a = r.ally[j++];
                const Seen& sn = m.ally[s];
                a.present = 1;
                a.handle = b.ally_handle[static_cast<std::size_t>(s)];
                a.slot = s, a.type = m.ally_type[s], a.alive = m.ally_alive[s];
                a.visible = !dead && sn.round == now;
                a.known = sn.round >= 0 && now - sn.round <= kMemoryMaxAge;
                a.age = sn.round >= 0 ? now - sn.round : -1;
                a.x = sn.x, a.y = sn.y, a.range = sn.range, a.gems = sn.gems;
                a.hp = sn.hp, a.max_hp = sn.max_hp, a.strength = sn.strength, a.focus = sn.focus;
                a.claim_code = s < kClaimSlots ? b.claim_of(s) : -1;
                a.claim_dist = -1;
                if (a.claim_code >= 0 && a.claim_code < static_cast<int>(w.groups.size()) && a.claim_code < 126) {
                    a.claim_gems = static_cast<std::int32_t>(w.groups[static_cast<std::size_t>(a.claim_code)].gems);
                    const vec2 ap{sn.x, sn.y};
                    if (a.known && w.has_field(a.claim_code) && on_map(w, ap)) {
                        const int v = w.group_distance(a.claim_code, ap);
                        a.claim_dist = v == kUnreach ? 9999 : v;
                    }
                }
            }
        }

        // ---- enemies (every enemy body: public identity + own last observation)
        for (int i = 0; i < m.n_enemy && i < kEnemyRows; ++i) {
            EnemyRaw& e = r.enemy[i];
            const Seen& sn = m.enemy[i];
            e.present = 1;
            e.handle = m.enemy_handle[i], e.type = m.enemy_type[i], e.alive = m.enemy_alive[i];
            e.visible = !dead && sn.round == now;
            e.known = sn.round >= 0 && now - sn.round <= kMemoryMaxAge;
            e.age = sn.round >= 0 ? now - sn.round : -1;
            e.x = sn.x, e.y = sn.y, e.range = sn.range, e.gems = sn.gems, e.state_bits = sn.state;
            e.hp = sn.hp, e.max_hp = sn.max_hp, e.strength = sn.strength, e.focus = sn.focus;
        }
        return true;
    }
};

namespace nnobs {
bool capture(const Bot& bot, RawTurn& out) { return nn_obs_access::capture(bot, out); }
void observe(const Bot& bot) { nn_obs_access::observe(bot); }
} // namespace nnobs
#endif // NN_ANY_HEAD
