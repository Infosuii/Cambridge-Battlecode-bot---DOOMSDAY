// Mimic runtime (see bot.h). Every decision goes through the core (core.cpp) with the fitted weights (weights.h);
// this file only reads the game, executes, shops, and applies the ability rules the models do not cover.
#include "bot.h"

#include <algorithm>
#include <cstdio>
#include <cmath>
#include <cstring>

#include "common.h"
#include "draft.h"
#include "weights.h"

namespace bc = cambc;
namespace d = cambc::detail;

#if MIMIC_FUEL
#define FUEL_MARK(name) fuel_mark(name)
namespace {
std::uint64_t fuel_last = 0;
const char* fuel_names[48];
std::uint64_t fuel_used[48];
int fuel_count = 0;
void fuel_mark(const char* name) {
    const std::uint64_t now = bc::fuel_remaining();
    if (fuel_count < 48) {
        fuel_names[fuel_count] = name;
        fuel_used[fuel_count++] = fuel_last >= now ? fuel_last - now : 0;
    }
    fuel_last = now;
}
} // namespace
#else
#define FUEL_MARK(name) ((void)0)
#endif

namespace {

inline int cheb(int ax, int ay, int bx, int by) { return std::max(std::abs(ax - bx), std::abs(ay - by)); }

// Two-stage choice for decisions whose candidate 0 is "do nothing" (stay, no attack, no spell): act when the
// candidates that act hold more than half the probability, then take the likeliest of them. A plain argmax freezes:
// the top teams' moves spread over several tiles, so staying is often the single likeliest candidate even when they
// move 70% of the time. Returns 0 (nothing) or the chosen index.
int act_or_not(float* s, int n) {
    if (n <= 1) return 0;
    float top = s[0];
    for (int i = 1; i < n; ++i) top = std::max(top, s[i]);
    float total = 0, acting = 0;
    for (int i = 0; i < n; ++i) {
        const float e = std::exp(s[i] - top);
        total += e;
        if (i) acting += e;
    }
    if (acting <= 0.5f * total) return 0;
    int best = 1;
    for (int i = 2; i < n; ++i)
        if (s[i] > s[best]) best = i;
    return best;
}

float dot(const float* w, const float* f, int n) {
    float s = 0;
    for (int i = 0; i < n; ++i) s += w[i] * f[i];
    return s;
}

// Row-major tile bits of an SDK bitboard.
void board_bytes(const bc::bitboard& b, int w, int h, std::uint8_t flag, std::uint8_t* terr) {
    const auto bits = b.export_linear_buffer();
    for (int i = 0; i < w * h; ++i)
        if ((bits[static_cast<std::size_t>(i) >> 3] >> (i & 7)) & 1) terr[i] |= flag;
}

float feat_buf[mc::kMaxObj * mc::NF_OBJ];
float score_buf[mc::kMaxObj];

} // namespace

void Mimic::init() {
    me_ = static_cast<std::uint32_t>(static_cast<bc::handle_champion_t>(bc::self()));
    team_row_ = (MIMIC_TEAM >= 0 && MIMIC_TEAM < mc::kNumTeams) ? MIMIC_TEAM + 1 : 0;
    perma_ = MIMIC_PERMA_RECALL && imitated_team().perma_recall;
    const int w = bc::map::width(), h = bc::map::height();
    mc::begin_map(map_, w, h, static_cast<int>(bc::map::symmetry()));
    board_bytes(bc::map::walls(), w, h, mc::T_WALL, map_.terr);
    board_bytes(bc::map::holes(), w, h, mc::T_HOLE, map_.terr);
    board_bytes(bc::map::altars(), w, h, mc::T_ALTAR, map_.terr);
    board_bytes(bc::map::bushes(), w, h, mc::T_BUSH, map_.terr);
    board_bytes(bc::map::spawn_region(bc::team::ally), w, h, mc::T_MYSPAWN, map_.terr);
    board_bytes(bc::map::spawn_region(bc::team::enemy), w, h, mc::T_ENEMYSPAWN, map_.terr);
    // Camps group by group (the engine's group order), each group's camps by (y, x), as the extractor does.
    const auto groups = bc::map::camp_groups();
    for (std::size_t g = 0; g < groups.size() && g < static_cast<std::size_t>(mc::kMaxGroups); ++g) {
        std::vector<bc::camp> members(groups[g].camps().begin(), groups[g].camps().end());
        std::sort(members.begin(), members.end(), [](const bc::camp& a, const bc::camp& b) {
            const auto p = a.spawn_position(), q = b.spawn_position();
            return p.y != q.y ? p.y < q.y : p.x < q.x;
        });
        for (const auto& c : members) {
            float hp, str;
            int range;
            const int type = static_cast<int>(c.kind());
            mc::camp_stats(type, hp, str, range);
            mc::add_camp(map_, static_cast<int>(g), c.spawn_position().x, c.spawn_position().y, type, hp, str, range);
            camps_.push_back(c);
            camp_handles_.push_back(static_cast<std::uint32_t>(static_cast<bc::handle_camp_t>(c)));
        }
        mc::set_group(map_, static_cast<int>(g), static_cast<int>(groups[g].gold_value()),
                      static_cast<int>(groups[g].gem_value()), groups[g].max_respawn_timer());
        group_handles_.push_back(static_cast<std::uint32_t>(static_cast<bc::handle_camp_group_t>(groups[g])));
    }
    mc::finish_map(map_);
    for (int i = 0; i < map_.n_camps; ++i) camp_tiles_.set({map_.camps[i].x, map_.camps[i].y});
    fields_.assign(static_cast<std::size_t>(map_.n_groups) + 2, {});
    // Fields to build: home, altars, then groups nearest our spawn first.
    field_order_.clear();
    field_order_.push_back(map_.n_groups + 1);
    if (map_.n_altars) field_order_.push_back(map_.n_groups);
    std::vector<int> gs;
    for (int g = 0; g < map_.n_groups; ++g) gs.push_back(g);
    const int sx = (map_.sx0 + map_.sx1) / 2, sy = (map_.sy0 + map_.sy1) / 2;
    std::stable_sort(gs.begin(), gs.end(), [&](int a, int b) {
        return cheb(sx, sy, map_.groups[a].cx, map_.groups[a].cy) < cheb(sx, sy, map_.groups[b].cx, map_.groups[b].cy);
    });
    field_order_.insert(field_order_.end(), gs.begin(), gs.end());
    // Allies: shared-memory slots by ascending id.
    std::uint32_t n = 0;
    d::check(d::sdk_num_allies(&n));
    std::vector<std::uint32_t> ids(n);
    d::check(d::sdk_allies(ids.data(), n, &n));
    ids.resize(n);
    std::sort(ids.begin(), ids.end());
    for (auto id : ids) ally_ids_.push_back(static_cast<int>(id));
    my_slot_ = static_cast<int>(std::find(ids.begin(), ids.end(), me_) - ids.begin());
    if (my_slot_ >= mc::kMaxSide) my_slot_ = -1;
    // Ability kinds, ranges and attributes.
    for (int s = 0; s < 2; ++s) {
        d::ability_props p{};
        if (d::sdk_champion_ability_props(me_, static_cast<std::uint32_t>(s), &p) != 0) continue;
        Slot& sl = slots_[s];
        sl.kind = static_cast<int>(p.kind);
        sl.exclusive = (p.attributes & d::ability_attribute_exclusive_with_movement) != 0;
        switch (static_cast<bc::ability_kind>(p.kind)) {
        case bc::ability_kind::damage: sl.range = p.payload.damage.range; break;
        case bc::ability_kind::heal: sl.range = p.payload.heal.range; break;
        case bc::ability_kind::aoe_damage: sl.range = p.payload.aoe_damage.range; sl.radius = p.payload.aoe_damage.radius; break;
        case bc::ability_kind::cc: sl.range = p.payload.cc.range; break;
        case bc::ability_kind::shield: sl.range = p.payload.shield.range; break;
        case bc::ability_kind::dash: sl.range = p.payload.dash.range; sl.radius = p.payload.dash.radius; dash_slot_ = s; break;
        default: break;
        }
    }
#if MIMIC_PARITY
    std::uint32_t mp[4];
    mc::hash_map_parts(map_, mp);
    std::printf("MPMAP %u %u %u %u %u %u\n", me_, mc::hash_map(map_), mp[0], mp[1], mp[2], mp[3]);
#endif
    ready_ = true;
}

// Distance fields through the SDK (bc::distance_field), with the core's definition: blocked = walls, holes, altars,
// the enemy spawn and every camp tile, minus the roots.
void Mimic::build_fields(std::uint64_t reserve) {
    const int w = map_.w, h = map_.h;
    // A field is built only when it fits in what is left above the reserve (its cost: the dearest one so far).
    while (fields_built_ < field_order_.size() && bc::fuel_remaining() > reserve + field_cost_) {
        const std::uint64_t before = bc::fuel_remaining();
        const int which = field_order_[fields_built_++];
        bc::bitboard blocked = bc::map::walls() | bc::map::holes() | bc::map::altars() | bc::map::spawn_region(bc::team::enemy);
        for (int i = 0; i < map_.n_camps; ++i) blocked.set({map_.camps[i].x, map_.camps[i].y});
        bc::bitboard roots;
        if (which < map_.n_groups) {
            const mc::GroupStatic& G = map_.groups[which];
            for (int i = G.first; i < G.first + G.n; ++i) roots.set({map_.camps[i].x, map_.camps[i].y});
        } else if (which == map_.n_groups) {
            roots = bc::map::altars();
        } else {
            roots = bc::map::spawn_region(bc::team::ally);
        }
        bc::bitboard walls = blocked & ~roots, visited;
        bc::distance_field f;
        f.compute(walls, roots, visited);
        auto& buf = fields_[static_cast<std::size_t>(which)];
        buf.assign(static_cast<std::size_t>(w) * static_cast<std::size_t>(h), mc::kFar);
        f.export_linear_buffer(buf);
        if (which < map_.n_groups) map_.gfield[which] = buf.data();
        else if (which == map_.n_groups) map_.altar_field = buf.data();
        else {
            map_.home_field = buf.data();
            mc::refresh_group_cache(map_);
        }
        field_cost_ = std::max<std::uint64_t>(field_cost_, before - bc::fuel_remaining());
#if MIMIC_PARITY
        std::printf("MPFIELD %u %d %u\n", me_, which < map_.n_groups ? which : (which == map_.n_groups ? -1 : -2),
                    mc::hash_field(map_, buf.data()));
#endif
    }
}

void Mimic::observe_game() {
    mc::reset_obs(obs_);
    FUEL_MARK("o_clear");
    obs_.round = static_cast<int>(bc::round_number());
    d::champion_info info{};
    d::check(d::sdk_champion(me_, &info));
    std::uint32_t gems = 0, gold = 0;
    d::sdk_champion_gems(me_, &gems);
    d::sdk_champion_gold(me_, &gold);
    mc::UnitObs& me = obs_.me;
    me.id = static_cast<int>(me_);
    me.type = info.type;
    me.x = info.x;
    me.y = info.y;
    me.hp = info.health;
    me.max_hp = info.max_health;
    me.strength = info.strength;
    me.range = info.attack_range;
    me.gems = static_cast<int>(gems);
    me.flags = mc::flags_from_state(static_cast<std::uint32_t>(info.state));
    obs_.focus = info.focus;
    obs_.gold = static_cast<int>(gold);
    obs_.flags = me.flags;
    for (int s = 0; s < 2; ++s) {
        obs_.ability_kind[s] = slots_[s].kind;
        obs_.ability_range[s] = slots_[s].range;
        obs_.ability_radius[s] = slots_[s].radius;
        obs_.ability_excl[s] = slots_[s].exclusive ? 1 : 0;
        std::int32_t cd = 0;
        obs_.cooldown[s] = d::sdk_champion_cooldown(me_, static_cast<std::uint32_t>(s), &cd) == 0 ? cd : 0;
    }
    FUEL_MARK("o_self");
    for (int side = 0; side < 2; ++side) {
        std::uint32_t n = 0;
        if ((side == 0 ? d::sdk_num_allies(&n) : d::sdk_num_enemies(&n)) != 0) continue;
        std::uint32_t ids[16];
        n = std::min<std::uint32_t>(n, 16);
        if ((side == 0 ? d::sdk_allies(ids, n, &n) : d::sdk_enemies(ids, n, &n)) != 0) continue;
        for (std::uint32_t k = 0; k < n; ++k) {
            const std::uint32_t id = ids[k];
            if (id == me_) continue;
            d::champion_info u{};
            if (d::sdk_champion(id, &u) != 0 || (u.state & 1) == 0 || u.x < 0) continue;
            std::uint32_t g = 0;
            if (d::sdk_champion_gems(id, &g) != 0) g = 0;
            mc::UnitObs* o = nullptr;
            if (side == 1 && obs_.n_enemy < mc::kMaxSide) o = &obs_.enemy[obs_.n_enemy++];
            if (side == 0 && obs_.n_ally < mc::kMaxSide) o = &obs_.ally[obs_.n_ally++];
            if (!o) continue;
            *o = mc::UnitObs{}; // exact = true: in vision
            o->id = static_cast<int>(id);
            o->type = u.type;
            o->x = u.x;
            o->y = u.y;
            o->hp = u.health;
            o->max_hp = u.max_health;
            o->strength = u.strength;
            o->range = u.attack_range;
            o->gems = static_cast<int>(g);
            o->flags = mc::flags_from_state(static_cast<std::uint32_t>(u.state));
        }
    }
    // Camps: only those on a tile in vision can answer, so ask just those, in core index order (the extractor's).
    // Groups: every group is asked; the engine reports some (respawning ones) with none of their tiles in vision.
    FUEL_MARK("o_champs");
    bc::bitboard seen = bc::vision::visible_tiles() & camp_tiles_;
    std::vector<int> cs_idx;
    for (const bc::vec2 p : seen.positions()) {
        const int c = map_.camp_at[map_.idx(p.x, p.y)];
        if (c >= 0) cs_idx.push_back(c);
    }
    std::sort(cs_idx.begin(), cs_idx.end());
    for (const int i : cs_idx) {
        d::camp_state cs{};
        if (d::sdk_camp(camp_handles_[static_cast<std::size_t>(i)], &cs) != 0) continue;
        std::uint32_t s = 0;
        if (d::sdk_camp_state(camp_handles_[static_cast<std::size_t>(i)], &s) != 0 || s == 0) continue;
        if (obs_.n_camp < mc::kMaxCamps) obs_.camp[obs_.n_camp++] = mc::CampObs{i, cs.health, s == 1};
    }
    for (int g = 0; g < map_.n_groups; ++g) {
        std::uint32_t s = 0;
        if (d::sdk_camp_group_state(group_handles_[static_cast<std::size_t>(g)], &s) != 0 || s < 1 || s > 3) continue;
        std::int32_t timer = 0;
        if (s == 3 && d::sdk_camp_group_cooldown(group_handles_[static_cast<std::size_t>(g)], &timer) != 0) timer = 0;
        obs_.group[obs_.n_group++] = mc::GroupObs{g, static_cast<int>(s), s == 3 ? timer : 0};
    }
    FUEL_MARK("o_camps");
    std::uint8_t shared[8] = {};
    d::sdk_read_shared_memory(0, shared, 8);
    std::memcpy(shared_read_, shared, sizeof(shared_read_));
    int ids[mc::kMaxSide];
    const int n_ids = std::min<int>(static_cast<int>(ally_ids_.size()), mc::kMaxSide);
    for (int k = 0; k < n_ids; ++k) ids[k] = ally_ids_[static_cast<std::size_t>(k)];
    mc::add_remembered_allies(obs_, shared, ids, n_ids);
    mc::finalize_obs(map_, obs_);
}

void Mimic::finish(bool alive) {
    if (alive) mc::end_observe(obs_, mem_);
    if (my_slot_ >= 0) {
        std::uint8_t shared[8] = {};
        d::sdk_read_shared_memory(0, shared, 8);
        d::champion_info info{};
        const bool live = alive && d::sdk_champion(me_, &info) == 0 && (info.state & 1) && info.x >= 0;
        mc::write_slot(shared, my_slot_, live ? mc::encode_slot(info.x, info.y) : 0u);
        d::sdk_write_shared_memory(0, shared, 8);
    }
}

bc::champion Mimic::champion(int id) {
    return d::handle_access::make_champion(static_cast<bc::handle_champion_t>(static_cast<std::uint32_t>(id)));
}

const mc::UnitObs* Mimic::enemy(int id) const {
    for (int i = 0; i < obs_.n_enemy; ++i)
        if (obs_.enemy[i].id == id) return &obs_.enemy[i];
    return nullptr;
}

// Deterministic per (seed, round, champion, salt), in [0, 1): breaks exact ties and lets seeds differ.
float Mimic::noise(int salt) const {
    std::uint32_t h = 2166136261u;
    for (std::uint32_t v : {static_cast<std::uint32_t>(NOVA_SEED), static_cast<std::uint32_t>(obs_.round), me_,
                            static_cast<std::uint32_t>(salt)}) {
        h ^= v;
        h *= 16777619u;
        h ^= h >> 15;
    }
    return static_cast<float>(h & 0xFFFFFF) / 16777216.0f;
}

// The imitated team's item milestones for this hero (team_tables.h), then its stat stacks.
void Mimic::shop() {
    if (obs_.gold < 30) return;
    const proxy::Team& t = imitated_team();
    const proxy::Items* row = nullptr;
    for (int i = 0; i < t.n_items; ++i)
        if (static_cast<int>(t.items[i].hero) == obs_.me.type) row = &t.items[i];
    if (!row)
        for (int i = 0; i < proxy::kTeams[0].n_items; ++i)
            if (static_cast<int>(proxy::kTeams[0].items[i].hero) == obs_.me.type) row = &proxy::kTeams[0].items[i];
    if (!row) return;
    struct Step { bc::item_type item; int total; };
    std::vector<Step> plan;
    int base_main = 0, base_health = 0;
    for (int k = 0; k < row->n_open; ++k) {
        plan.push_back({row->open[k].item, row->open[k].total});
        if (row->open[k].item == row->main) base_main = std::max(base_main, row->open[k].total);
        if (row->open[k].item == row->health) base_health = std::max(base_health, row->open[k].total);
    }
    for (int k = 1; k <= 12; ++k) {
        plan.push_back({row->main, base_main + 5 * k});
        if (row->per_health > 0 && k % row->per_health == 0) plan.push_back({row->health, base_health + 5 * (k / row->per_health)});
    }
    try {
        auto& me = bc::self();
        const auto counts = me.item_count();
        std::vector<int> bought(static_cast<std::size_t>(bc::item_type::count), 0);
        int gold = obs_.gold;
        for (const auto& s : plan) {
            const int cost = std::max(1, static_cast<int>(s.item.cost()));
            int owned = bought[static_cast<std::size_t>(s.item)] + static_cast<int>(counts[s.item]);
            if (const auto emblem = s.item.result()) owned += static_cast<int>(counts[*emblem] * s.item.combine_count());
            const int want = std::min(s.total - owned, gold / cost);
            if (s.total - owned <= 0) continue;
            if (want <= 0) return; // the next milestone is not affordable yet: save for it
            if (!me.can_buy(s.item, static_cast<std::uint32_t>(want))) return;
            me.buy(s.item, static_cast<std::uint32_t>(want));
            bought[static_cast<std::size_t>(s.item)] += want;
            gold -= want * cost;
            if (s.total - owned > want) return;
        }
    } catch (const std::exception&) {
    }
}

mc::Objective Mimic::choose_objective() {
    // Re-decide every turn while an enemy is in view, when the last objective is spent (bank with no gems, home
    // reached, the group's state changed), and otherwise every third turn: the choice rarely changes in between and
    // costs a third of a turn's fuel on maps with many camp groups.
    if (have_prev_ && obs_.n_enemy == 0 && obs_.round - decided_round_ < 3) {
        bool spent = false;
        if (prev_obj_.kind == mc::O_BANK) spent = obs_.me.gems == 0;
        if (prev_obj_.kind == mc::O_HOME) spent = mc::on_my_spawn(map_, obs_.me.x, obs_.me.y);
        if (prev_obj_.kind == mc::O_FARM) {
            const auto& g = mem_.g[prev_obj_.arg];
            spent = g.state != decided_state_ || g.state == mc::G_REWARD || g.state == mc::G_RESPAWN;
        }
        if (prev_obj_.kind == mc::O_FIGHT) spent = true;
        if (!spent) return prev_obj_;
    }
    decided_round_ = obs_.round;
    static mc::Objective objs[mc::kMaxObj];
    FUEL_MARK("obj_in");
    const int n = mc::objective_candidates(map_, obs_, mem_, objs, feat_buf);
    FUEL_MARK("obj_feat");
    if (n == 0) return mc::Objective{mc::O_HOME, -1};
    mc::score_objectives(mc::kObjW[team_row_], feat_buf, objs, n, score_buf);
    FUEL_MARK("obj_score");
    for (int i = 0; i < n; ++i) {
        if (have_prev_ && objs[i].kind == prev_obj_.kind && objs[i].arg == prev_obj_.arg) score_buf[i] += MIMIC_STICKY;
        score_buf[i] += 0.01f * noise(i);
    }
    const mc::Objective ob = objs[mc::argmax(score_buf, n)];
#if MIMIC_TRACE
    {
        int order[3] = {-1, -1, -1};
        for (int i = 0; i < n; ++i)
            for (int k = 0; k < 3; ++k)
                if (order[k] < 0 || score_buf[i] > score_buf[order[k]]) {
                    for (int j = 2; j > k; --j) order[j] = order[j - 1];
                    order[k] = i;
                    break;
                }
        std::printf("TR r%d c%u (%d,%d) hp%.0f g%d gold%d obj", obs_.round, me_, obs_.me.x, obs_.me.y, obs_.me.hp, obs_.me.gems, obs_.gold);
        for (int k = 0; k < 3 && order[k] >= 0; ++k)
            std::printf(" %d:%d=%.2f", objs[order[k]].kind, objs[order[k]].arg, score_buf[order[k]]);
        std::printf(" d=%d", mc::objective_distance(map_, obs_, ob, obs_.me.x, obs_.me.y));
        if (ob.kind == mc::O_FARM) {
            const auto& gm = mem_.g[ob.arg];
            std::printf(" gstate=%d eta=%d vis=%d standing=%d", gm.state, gm.eta - obs_.round, obs_.gvis[ob.arg],
                        obs_.gstanding[ob.arg]);
        }
        std::printf("\n");
    }
#endif
    prev_obj_ = ob;
    if (ob.kind == mc::O_FARM) decided_state_ = mem_.g[ob.arg].state;
    have_prev_ = true;
    return ob;
}

// Spells, chosen by the cast model (weights.h kCastW) from where I stand: an attack reset is held for right after
// a basic attack (pending_reset_); any other spell goes now. One successful cast per turn.
void Mimic::cast_phase(mc::Objective ob) {
    if (cast_done_ || pending_reset_ >= 0 || !(obs_.flags & mc::F_CAN_CAST)) return;
    static mc::CastCand cc[mc::kMaxCasts];
    const int n = mc::cast_candidates(map_, obs_, mem_, ob, x_, y_, cc, feat_buf);
    if (n <= 1) return;
    const int h = std::clamp(obs_.me.type, 0, 12);
    mc::score(mc::kCastW[team_row_][h], feat_buf, n, mc::NF_CAST, score_buf);
    for (int i = 0; i < n; ++i) score_buf[i] += 1e-3f * noise(400 + i);
    if (act_or_not(score_buf, n) == 0) return;
    score_buf[0] = -1e9f; // casting: the likeliest spell that goes off
    for (int tries = 0; tries < 3; ++tries) {
        const int k = mc::argmax(score_buf, n);
        if (k == 0 || score_buf[k] < -1e8f) return;
        const mc::CastCand& c = cc[k];
        if (c.kind == static_cast<int>(bc::ability_kind::attack_reset)) {
            pending_reset_ = c.slot;
            return;
        }
        bool ok = false;
        try {
            const auto ab = bc::self().abilities()[static_cast<std::size_t>(c.slot)];
            if (c.kind == static_cast<int>(bc::ability_kind::aoe_damage)) ok = ab.use(bc::vec2{c.x, c.y});
            else if (c.tkind == 1 || c.tkind == 3) ok = ab.use(champion(c.id));
            else if (c.tkind == 2) ok = ab.use(camps_[static_cast<std::size_t>(c.id)]);
            else if (c.tkind == 4) ok = ab.use();
        } catch (const std::exception&) {
            ok = false;
        }
        if (ok) {
            cast_done_ = true;
            if (slots_[c.slot].exclusive) excl_cast_ = true;
            return;
        }
        score_buf[k] = -1e9f;
    }
}

// After a basic attack: the held attack reset, then a second hit on the same target if it still stands, else the
// best other target in reach.
void Mimic::after_attack(mc::Objective ob, const mc::TargetCand& t) {
    if (pending_reset_ < 0 || cast_done_) return;
    try {
        const auto ab = bc::self().abilities()[static_cast<std::size_t>(pending_reset_)];
        pending_reset_ = -1;
        if (!ab.use()) return;
        cast_done_ = true;
        if (attack(t)) return;
        static mc::TargetCand tg[mc::kMaxTargets];
        const int n = mc::target_candidates(map_, obs_, mem_, ob, x_, y_, tg, feat_buf);
        const int h = std::clamp(obs_.me.type, 0, 12);
        mc::score(mc::kTgtW[team_row_][h], feat_buf, n, mc::NF_TGT, score_buf);
        for (int i = 1; i < n; ++i) score_buf[i] += 1e-3f * noise(100 + i);
        score_buf[0] = -1e9f; // the reset is spent: hit something
        if (n > 1) attack(tg[mc::argmax(score_buf, n)]);
    } catch (const std::exception&) {
    }
}

bool Mimic::attack(const mc::TargetCand& t) {
    try {
        auto& me = bc::self();
        if (t.kind == 1) {
            const bc::champion c = champion(t.id);
            if (!c.is_visible() || !c.is_alive()) return false;
            me.attack(c);
            return true;
        }
        if (t.kind == 2) {
            const auto& c = camps_[static_cast<std::size_t>(t.id)];
            if (!c.is_visible() || c.is_dead()) return false;
            me.attack(c);
            return true;
        }
    } catch (const std::exception&) {
    }
    return false;
}

bool Mimic::move(mc::Objective ob) {
    if (!(obs_.flags & mc::F_CAN_MOVE) || excl_cast_) return false;
    static mc::MoveCand mv[mc::kMaxMoves];
    // The kernel scores candidates around my turn-start tile; after a melee attack I have not moved, so it holds.
    const bool dash_ready = dash_slot_ >= 0 && (obs_.flags & mc::F_CAN_CAST) && obs_.cooldown[dash_slot_] <= 0;
    FUEL_MARK("m_in");
    const int n = mc::move_candidates(map_, obs_, mem_, ob, dash_ready, mv, feat_buf);
    FUEL_MARK("m_feat");
    const int h = std::clamp(obs_.me.type, 0, 12);
    mc::score(mc::kMoveW[team_row_][h], feat_buf, n, mc::NF_MOVE, score_buf);
    FUEL_MARK("m_score");
    for (int i = 0; i < n; ++i) score_buf[i] += 1e-3f * noise(200 + i);
    auto& me = bc::self();
    const int first = act_or_not(score_buf, n);
#if MIMIC_TRACE
    {
        const float* fk = feat_buf + first * mc::NF_MOVE;
        std::printf("TM r%d c%u n%d pick%d (%d,%d)%s stay=%.2f best=%.2f dd=%.2f goal=%.0f\n", obs_.round, me_, n, first,
                    mv[first].x, mv[first].y, mv[first].dash ? "D" : "", score_buf[0], score_buf[first], fk[2], fk[5]);
    }
#endif
    if (first == 0) return false; // staying put
    score_buf[0] = -1e9f;         // moving: the likeliest tile that is free
    for (int tries = 0; tries < 4; ++tries) {
        const int k = mc::argmax(score_buf, n);
        if (k == 0 || score_buf[k] < -1e8f) return false;
        bool ok = false;
        try {
            if (mv[k].dash) ok = me.abilities()[static_cast<std::size_t>(dash_slot_)].use(bc::vec2{mv[k].x, mv[k].y});
            else ok = me.move_absolute(bc::vec2{mv[k].x, mv[k].y});
        } catch (const std::exception&) {
            ok = false;
        }
        if (ok) {
            x_ = mv[k].x;
            y_ = mv[k].y;
            moved_ = true;
            return true;
        }
        score_buf[k] = -1e9f;
    }
    return false;
}

void Mimic::act(mc::Objective ob) {
    static mc::TargetCand tg[mc::kMaxTargets];
    const int h = std::clamp(obs_.me.type, 0, 12);
    const bool ranged = obs_.me.range > 1;
    auto pick_target = [&](int x, int y) -> mc::TargetCand {
        if (!(obs_.flags & mc::F_CAN_ATTACK)) return mc::TargetCand{0, -1};
        const int n = mc::target_candidates(map_, obs_, mem_, ob, x, y, tg, feat_buf);
        if (n <= 1) return mc::TargetCand{0, -1};
        mc::score(mc::kTgtW[team_row_][h], feat_buf, n, mc::NF_TGT, score_buf);
        for (int i = 0; i < n; ++i) score_buf[i] += 1e-3f * noise(300 + i);
        return tg[act_or_not(score_buf, n)];
    };
    pending_reset_ = -1;
    cast_done_ = false;
    cast_phase(ob);
    FUEL_MARK("a_cast");
    const mc::TargetCand first = pick_target(x_, y_);
#if MIMIC_TRACE
    {
        const int nt = mc::target_candidates(map_, obs_, mem_, ob, x_, y_, tg, feat_buf);
        std::printf("TA r%d c%u targets=%d pick=%d:%d cast=%d reset=%d canatk=%d\n", obs_.round, me_, nt, first.kind, first.id,
                    cast_done_ ? 1 : 0, pending_reset_, (obs_.flags & mc::F_CAN_ATTACK) ? 1 : 0);
    }
#endif
    FUEL_MARK("a_pick");
    if (first.kind != 0 && attack(first)) {
        attacked_ = true;
        after_attack(ob, first);
    }
    if (ranged && attacked_) return; // moving and attacking share the ranged allowance
    FUEL_MARK("a_attack");
    move(ob);
    FUEL_MARK("a_move");
    if (moved_) {
        // After a step: spells and (melee) a basic attack from the new tile (others have not moved this turn).
        if (!cast_done_ && pending_reset_ < 0) cast_phase(ob);
        if (!attacked_) {
            const mc::TargetCand t = pick_target(x_, y_);
            if (t.kind != 0 && attack(t)) {
                attacked_ = true;
                after_attack(ob, t);
            }
        }
    }
}

void Mimic::maybe_tribute() {
    if (obs_.me.gems <= 0) return;
    int ax = -1, ay = -1;
    for (int i = 0; i < map_.n_altars; ++i)
        if (cheb(x_, y_, map_.ax[i], map_.ay[i]) <= 1) {
            ax = map_.ax[i];
            ay = map_.ay[i];
            break;
        }
    if (ax < 0) return;
    float f[mc::NF_TRIB];
    mc::tribute_features(map_, obs_, mem_, f);
    if (dot(mc::kTribW[team_row_], f, mc::NF_TRIB) <= 0) return;
    try {
        bc::self().submit_gems(bc::vec2{ax, ay});
    } catch (const std::exception&) {
    }
}


void Mimic::turn() {
#if MIMIC_FUEL
    fuel_last = bc::fuel_remaining();
    fuel_count = 0;
    struct Print {
        ~Print() {
            // Format only after all actions and the shared-memory write. Formatting each mark consumed ~2.3k
            // fuel and made the old probe itself suspend turns. A zero delta denotes a suspension/refill.
            const auto left = bc::fuel_remaining();
            if (bc::round_number() % 25 || left < 12000) return;
            std::printf("FUEL r%u left=%llu", bc::round_number(), static_cast<unsigned long long>(left));
            for (int i = 0; i < fuel_count; ++i)
                std::printf(" %s=%llu", fuel_names[i], static_cast<unsigned long long>(fuel_used[i]));
            std::printf("\n");
        }
    } print_at_end;
#endif
    if (!ready_) init();
    // Cancel the deliberate end-of-turn recall BEFORE taking this turn's observation. The engine removes the
    // action-permission bits while recalling; clearing only F_RECALLING on a stale snapshot left these champions
    // unable to move, attack or cast forever, even though the host had accepted the cancellation.
    if (trick_pending_) {
        d::champion_info current{};
        if (d::sdk_champion(me_, &current) == 0 && (current.state & (1u << 1))) {
            try { bc::self().cancel_recall(); } catch (const std::exception&) {}
        }
        trick_pending_ = false;
    }
    FUEL_MARK("init");
    // Fields first (from spare fuel), leaving enough for this turn's own work.
    build_fields(bc::round_number() <= 1 ? 90000 : 50000);
    FUEL_MARK("fields");
    observe_game();
    FUEL_MARK("observe");
    x_ = obs_.me.x;
    y_ = obs_.me.y;
    attacked_ = moved_ = excl_cast_ = false;
    d::champion_info info{};
    const bool live = d::sdk_champion(me_, &info) == 0 && (info.state & 1) && info.x >= 0;
    if (!live) {
        // Dead: shop only. Memory is not updated while dead (the extractor folds in living turns only).
        shop();
        trick_pending_ = false;
        finish(false);
        return;
    }
    mc::observe(map_, obs_, mem_);
    FUEL_MARK("memory");
#if MIMIC_PARITY
    std::uint32_t op[5];
    mc::hash_obs_parts(obs_, op);
    std::printf("MP %d %u %u %u %u %zu %u %u %u %u %u %u %u\n", obs_.round, me_, mc::hash_obs(obs_), mc::hash_memory(map_, mem_),
                mc::hash_decisions(map_, obs_, mem_), fields_built_, op[0], op[1], op[2], op[3], op[4], shared_read_[0], shared_read_[1]);
    if (obs_.round <= 150) { // readable dumps for the parity report
        static char dump[8192];
        mc::dump_obs(obs_, dump, sizeof(dump));
        std::printf("MPDOBS %d %u %s\n", obs_.round, me_, dump);
    }
#endif
    const bool home = mc::on_my_spawn(map_, x_, y_);
    if (home || obs_.me.type == mc::TAVI) shop();
    if (obs_.flags & (mc::F_RECALLING | mc::F_TRIBUTING | mc::F_TELEPORTING)) {
        finish(true);
        return;
    }
    if (!home && (obs_.flags & mc::F_CAN_MOVE)) {
        float f[mc::NF_RECALL];
        mc::recall_features(map_, obs_, mem_, f);
        // A recall is a per-turn hazard (about 1% of the top teams' turns): drawn with the model's probability, as a
        // threshold at one half would almost never fire.
        const float p = 1.0f / (1.0f + std::exp(-dot(mc::kRecallW[team_row_], f, mc::NF_RECALL)));
        if (noise(500) < p) {
            try {
                bc::self().recall();
                finish(true);
                return;
            } catch (const std::exception&) {
            }
        }
    }
    FUEL_MARK("pre");
    const mc::Objective ob = choose_objective();
    FUEL_MARK("objective");
    act(ob);
    FUEL_MARK("act");
    maybe_tribute();
    if (perma_) {
        try {
            const auto st = bc::self().state();
            if (!st.contains(bc::champion_state::recalling) && !st.contains(bc::champion_state::submitting_gems) &&
                !mc::on_my_spawn(map_, x_, y_)) {
                bc::self().recall();
                trick_pending_ = true;
            }
        } catch (const std::exception&) {
        }
    }
    FUEL_MARK("tail");
    finish(true);
    FUEL_MARK("finish");
}
