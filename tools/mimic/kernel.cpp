// Offline host for the mimic core (bots/mimic/src/core.cpp): the same code compiled to a wasm reactor that
// tools/mimic/extract.mjs drives from replays. Two map slots (one per team) and one memory per champion entity.
// Build: python tools/mimic/build_kernel.py (wasi-sdk clang, the bot's own optimisation flags).
#include "../../bots/mimic/src/core.h"

#include <cstring>

namespace {
mc::Map maps[2];
std::uint16_t fields[2][mc::kMaxGroups + 2][mc::kMaxTiles]; // groups, then altar, then home
std::uint8_t blocked[mc::kMaxTiles], roots[mc::kMaxTiles];
constexpr int kSlots = 16;
mc::Memory mem[kSlots];
mc::Obs obs;
std::uint8_t shared[2][8];
mc::Objective objs[mc::kMaxObj];
mc::MoveCand moves[mc::kMaxMoves];
mc::TargetCand tgts[mc::kMaxTargets];
mc::CastCand casts[mc::kMaxCasts];
float feat[mc::kMaxObj * mc::NF_OBJ];
std::int32_t ibuf[mc::kMaxObj * 5];
char names[4096];
} // namespace

#define EXPORT(name) extern "C" __attribute__((export_name(#name)))

EXPORT(mk_map_begin) void mk_map_begin(int team, int w, int h, int sym) { mc::begin_map(maps[team], w, h, sym); }
EXPORT(mk_terr) std::uint8_t* mk_terr(int team) { return maps[team].terr; }
EXPORT(mk_add_camp) void mk_add_camp(int team, int group, int x, int y, int type) {
    float hp, str;
    int range;
    mc::camp_stats(type, hp, str, range);
    mc::add_camp(maps[team], group, x, y, type, hp, str, range);
}
EXPORT(mk_set_group) void mk_set_group(int team, int g, int gold, int gems, int respawn) {
    mc::set_group(maps[team], g, gold, gems, respawn);
}
// Finish the map and build every field with the core's BFS (the bot builds the same fields with bc::distance_field).
EXPORT(mk_map_finish) void mk_map_finish(int team) {
    mc::Map& m = maps[team];
    mc::finish_map(m);
    mc::blocked_mask(m, blocked);
    for (int g = 0; g < m.n_groups; ++g) {
        mc::group_roots(m, g, roots);
        mc::bfs(m, blocked, roots, fields[team][g]);
        m.gfield[g] = fields[team][g];
    }
    mc::altar_roots(m, roots);
    mc::bfs(m, blocked, roots, fields[team][mc::kMaxGroups]);
    m.altar_field = fields[team][mc::kMaxGroups];
    mc::home_roots(m, roots);
    mc::bfs(m, blocked, roots, fields[team][mc::kMaxGroups + 1]);
    m.home_field = fields[team][mc::kMaxGroups + 1];
    mc::refresh_group_cache(m);
}
// Read-only access to a field (which: group index, -1 altar, -2 home) for the parity check.
EXPORT(mk_field) const std::uint16_t* mk_field(int team, int which) {
    return fields[team][which >= 0 ? which : (which == -1 ? mc::kMaxGroups : mc::kMaxGroups + 1)];
}
EXPORT(mk_map_info) std::int32_t* mk_map_info(int team) {
    const mc::Map& m = maps[team];
    ibuf[0] = m.n_camps;
    ibuf[1] = m.n_groups;
    ibuf[2] = m.n_altars;
    ibuf[3] = m.sx0;
    ibuf[4] = m.sy0;
    ibuf[5] = m.sx1;
    ibuf[6] = m.sy1;
    return ibuf;
}

EXPORT(mk_mem_reset) void mk_mem_reset(int slot) { mem[slot] = mc::Memory{}; }

EXPORT(mk_obs_self) void mk_obs_self(int round, int id, int type, int x, int y, float hp, float max_hp, float strength,
                                     float focus, int range, int gems, int gold, int state, int ak0, int ak1, int cd0,
                                     int cd1) {
    mc::reset_obs(obs);
    obs.round = round;
    obs.me.id = id;
    obs.me.type = type;
    obs.me.x = x;
    obs.me.y = y;
    obs.me.hp = hp;
    obs.me.max_hp = max_hp;
    obs.me.strength = strength;
    obs.me.range = range;
    obs.me.gems = gems;
    obs.me.flags = mc::flags_from_state(static_cast<std::uint32_t>(state));
    obs.focus = focus;
    obs.gold = gold;
    obs.flags = obs.me.flags;
    obs.ability_kind[0] = ak0;
    obs.ability_kind[1] = ak1;
    obs.cooldown[0] = cd0;
    obs.cooldown[1] = cd1;
}
EXPORT(mk_obs_unit) void mk_obs_unit(int enemy, int id, int type, int x, int y, float hp, float max_hp, float strength,
                                     int range, int gems, int state) {
    mc::UnitObs* u = nullptr;
    if (enemy && obs.n_enemy < mc::kMaxSide) u = &obs.enemy[obs.n_enemy++];
    if (!enemy && obs.n_ally < mc::kMaxSide) u = &obs.ally[obs.n_ally++];
    if (!u) return;
    *u = mc::UnitObs{}; // every field below; exact stays true (in vision)
    u->id = id;
    u->type = type;
    u->x = x;
    u->y = y;
    u->hp = hp;
    u->max_hp = max_hp;
    u->strength = strength;
    u->range = range;
    u->gems = gems;
    u->flags = mc::flags_from_state(static_cast<std::uint32_t>(state));
}
EXPORT(mk_obs_camp) void mk_obs_camp(int idx, float hp, int awake) {
    if (obs.n_camp >= mc::kMaxCamps) return;
    obs.camp[obs.n_camp++] = mc::CampObs{idx, hp, awake != 0};
}
EXPORT(mk_obs_group) void mk_obs_group(int g, int state, int timer) {
    if (obs.n_group >= mc::kMaxGroups) return;
    obs.group[obs.n_group++] = mc::GroupObs{g, state, timer};
}
// Shared memory simulation: a champion writes its slot at the end of its turn, as the bot does.
EXPORT(mk_shared_reset) void mk_shared_reset() {
    for (auto& t : shared)
        for (auto& b : t) b = 0;
}
EXPORT(mk_write_slot) void mk_write_slot(int team, int slot, int x, int y, int alive) {
    mc::write_slot(shared[team], slot, alive ? mc::encode_slot(x, y) : 0u);
}
EXPORT(mk_shared_snapshot) void mk_shared_snapshot(int team, std::uint32_t lo, std::uint32_t hi) {
    for (int b = 0; b < 4; ++b) {
        shared[team][b] = static_cast<std::uint8_t>(lo >> (8 * b));
        shared[team][b + 4] = static_cast<std::uint8_t>(hi >> (8 * b));
    }
}
// Ally ids by slot (ascending champion id), ids[0..n).
EXPORT(mk_add_remembered) void mk_add_remembered(int team, int n, int id0, int id1, int id2, int id3, int id4, int id5) {
    const int ids[6] = {id0, id1, id2, id3, id4, id5};
    mc::add_remembered_allies(obs, shared[team], ids, n);
}
EXPORT(mk_n_ally) int mk_n_ally() { return obs.n_ally; }

EXPORT(mk_observe) void mk_observe(int team, int slot) {
    mc::finalize_obs(maps[team], obs);
    mc::observe(maps[team], obs, mem[slot]);
}
EXPORT(mk_end_observe) void mk_end_observe(int slot) { mc::end_observe(obs, mem[slot]); }

EXPORT(mk_feat) float* mk_feat() { return feat; }
EXPORT(mk_ibuf) std::int32_t* mk_ibuf() { return ibuf; }

// Candidates: ibuf gets (kind, arg) / (x, y, dash) / (kind, id) per candidate, feat the feature rows.
EXPORT(mk_objectives) int mk_objectives(int team, int slot) {
    const int n = mc::objective_candidates(maps[team], obs, mem[slot], objs, feat);
    for (int i = 0; i < n; ++i) {
        ibuf[2 * i] = objs[i].kind;
        ibuf[2 * i + 1] = objs[i].arg;
    }
    return n;
}
EXPORT(mk_moves) int mk_moves(int team, int slot, int kind, int arg, int dash_ready) {
    const mc::Objective ob{static_cast<std::uint8_t>(kind), arg};
    const int n = mc::move_candidates(maps[team], obs, mem[slot], ob, dash_ready != 0, moves, feat);
    for (int i = 0; i < n; ++i) {
        ibuf[3 * i] = moves[i].x;
        ibuf[3 * i + 1] = moves[i].y;
        ibuf[3 * i + 2] = moves[i].dash;
    }
    return n;
}
EXPORT(mk_targets) int mk_targets(int team, int slot, int kind, int arg, int x, int y) {
    const mc::Objective ob{static_cast<std::uint8_t>(kind), arg};
    const int n = mc::target_candidates(maps[team], obs, mem[slot], ob, x, y, tgts, feat);
    for (int i = 0; i < n; ++i) {
        ibuf[2 * i] = tgts[i].kind;
        ibuf[2 * i + 1] = tgts[i].id;
    }
    return n;
}
// Ability ranges, radii and the walking exclusion for both slots (after mk_obs_self).
EXPORT(mk_obs_abilities) void mk_obs_abilities(float r0, float rad0, int ex0, float r1, float rad1, int ex1) {
    obs.ability_range[0] = r0;
    obs.ability_radius[0] = rad0;
    obs.ability_excl[0] = ex0;
    obs.ability_range[1] = r1;
    obs.ability_radius[1] = rad1;
    obs.ability_excl[1] = ex1;
}
// Cast candidates from (x, y): ibuf gets (slot, target kind, id, x, y) per candidate.
EXPORT(mk_casts) int mk_casts(int team, int slot, int kind, int arg, int x, int y) {
    const mc::Objective ob{static_cast<std::uint8_t>(kind), arg};
    const int n = mc::cast_candidates(maps[team], obs, mem[slot], ob, x, y, casts, feat);
    for (int i = 0; i < n; ++i) {
        ibuf[5 * i] = casts[i].slot;
        ibuf[5 * i + 1] = casts[i].tkind;
        ibuf[5 * i + 2] = casts[i].id;
        ibuf[5 * i + 3] = casts[i].x;
        ibuf[5 * i + 4] = casts[i].y;
    }
    return n;
}
EXPORT(mk_recall) void mk_recall(int team, int slot) { mc::recall_features(maps[team], obs, mem[slot], feat); }
EXPORT(mk_tribute) void mk_tribute(int team, int slot) { mc::tribute_features(maps[team], obs, mem[slot], feat); }
EXPORT(mk_objective_distance) int mk_objective_distance(int team, int kind, int arg, int x, int y) {
    return mc::objective_distance(maps[team], obs, mc::Objective{static_cast<std::uint8_t>(kind), arg}, x, y);
}
EXPORT(mk_group_state) int mk_group_state(int slot, int g) { return mem[slot].g[g].state; }
// Walking distance to the altars (kind 1) or home (kind 2) from (x, y): fields only, no observation needed.
EXPORT(mk_static_distance) int mk_static_distance(int team, int kind, int x, int y) {
    static const mc::Obs none{};
    return mc::objective_distance(maps[team], none, mc::Objective{static_cast<std::uint8_t>(kind), -1}, x, y);
}

// Parity hashes (the bot prints the same, MIMIC_PARITY builds).
EXPORT(mk_hash_obs) std::uint32_t mk_hash_obs() { return mc::hash_obs(obs); }
EXPORT(mk_hash_memory) std::uint32_t mk_hash_memory(int team, int slot) { return mc::hash_memory(maps[team], mem[slot]); }
EXPORT(mk_hash_decisions) std::uint32_t mk_hash_decisions(int team, int slot) {
    return mc::hash_decisions(maps[team], obs, mem[slot]);
}
EXPORT(mk_hash_map) std::uint32_t mk_hash_map(int team) { return mc::hash_map(maps[team]); }
// Part hashes into ibuf: map [4], observation [5].
EXPORT(mk_hash_map_parts) void mk_hash_map_parts(int team) {
    mc::hash_map_parts(maps[team], reinterpret_cast<std::uint32_t*>(ibuf));
}
EXPORT(mk_hash_obs_parts) void mk_hash_obs_parts() { mc::hash_obs_parts(obs, reinterpret_cast<std::uint32_t*>(ibuf)); }
namespace {
char dumpbuf[32768];
}
EXPORT(mk_dump_obs) const char* mk_dump_obs() {
    mc::dump_obs(obs, dumpbuf, sizeof(dumpbuf));
    return dumpbuf;
}
EXPORT(mk_dump_map) const char* mk_dump_map(int team) {
    mc::dump_map(maps[team], dumpbuf, sizeof(dumpbuf));
    return dumpbuf;
}
EXPORT(mk_hash_field) std::uint32_t mk_hash_field(int team, int which) {
    return mc::hash_field(maps[team], mk_field(team, which));
}

// Feature names, comma-separated, for one decision (0 objective, 1 move, 2 target, 3 recall, 4 tribute, 5 cast).
EXPORT(mk_names) const char* mk_names(int which) {
    const char* const* list[] = {mc::kObjNames, mc::kMoveNames, mc::kTgtNames, mc::kRecallNames, mc::kTribNames, mc::kCastNames};
    const int count[] = {mc::NF_OBJ, mc::NF_MOVE, mc::NF_TGT, mc::NF_RECALL, mc::NF_TRIB, mc::NF_CAST};
    names[0] = 0;
    std::size_t at = 0;
    for (int i = 0; i < count[which]; ++i) {
        const std::size_t len = std::strlen(list[which][i]);
        if (at + len + 2 >= sizeof(names)) break;
        if (i) names[at++] = ',';
        std::memcpy(names + at, list[which][i], len);
        at += len;
        names[at] = 0;
    }
    return names;
}
