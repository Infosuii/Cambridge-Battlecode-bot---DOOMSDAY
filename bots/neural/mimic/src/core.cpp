// Mimic core (see core.h): memory, candidate generation and features. No SDK calls.
#include "core.h"
#if defined(__wasm_simd128__)
#include <wasm_simd128.h>
#endif

namespace mc {
namespace {

inline int iabs(int v) { return v < 0 ? -v : v; }
inline int imax(int a, int b) { return a > b ? a : b; }
inline int imin(int a, int b) { return a < b ? a : b; }
inline float fmin2(float a, float b) { return a < b ? a : b; }
inline float fmax2(float a, float b) { return a > b ? a : b; }
inline float clampf(float v, float lo, float hi) { return v < lo ? lo : (v > hi ? hi : v); }
inline int cheb(int ax, int ay, int bx, int by) { return imax(iabs(ax - bx), iabs(ay - by)); }
// ln(1 + x) for x >= 0 without <cmath>: the bot and the extractor must agree bit for bit, so no libm.
float log1p_pos(float x) {
    // Range reduction by powers of two, then a series in t = (y - 1) / (y + 1).
    float y = 1.0f + x;
    int k = 0;
    while (y > 2.0f) { y *= 0.5f; ++k; }
    const float t = (y - 1.0f) / (y + 1.0f), t2 = t * t;
    const float s = 2.0f * t * (1.0f + t2 * (1.0f / 3 + t2 * (1.0f / 5 + t2 * (1.0f / 7 + t2 * (1.0f / 9)))));
    return s + 0.69314718f * static_cast<float>(k);
}

constexpr int kNoDist = 300; // unreachable or unknown: farther than any real walk

// Field value at a tile, or one more than the best neighbour when the tile itself is blocked in the field (standing
// on a dead camp's tile, say).
int fdist(const Map& m, const std::uint16_t* f, int x, int y) {
    const std::uint16_t v = f[m.idx(x, y)];
    if (v != kFar) return v;
    int best = kFar;
    for (int dy = -1; dy <= 1; ++dy)
        for (int dx = -1; dx <= 1; ++dx) {
            const int nx = x + dx, ny = y + dy;
            if ((dx || dy) && m.inside(nx, ny)) {
                const int u = f[m.idx(nx, ny)];
                if (u != kFar && u + 1 < best) best = u + 1;
            }
        }
    return best == kFar ? kNoDist : imin(best, kNoDist);
}
int fcap(int v) { return v == kFar ? kNoDist : imin(v, kNoDist); }

int group_distance(const Map& m, int g, int x, int y) {
    if (m.gfield[g]) return fcap(fdist(m, m.gfield[g], x, y));
    int best = kNoDist;
    const GroupStatic& G = m.groups[g];
    for (int i = G.first; i < G.first + G.n; ++i) best = imin(best, cheb(x, y, m.camps[i].x, m.camps[i].y));
    return best;
}
int altar_distance(const Map& m, int x, int y) {
    if (m.altar_field) return fcap(fdist(m, m.altar_field, x, y));
    int best = kNoDist;
    for (int i = 0; i < m.n_altars; ++i) best = imin(best, cheb(x, y, m.ax[i], m.ay[i]));
    return best;
}
int home_distance(const Map& m, int x, int y) {
    if (m.home_field) return fcap(fdist(m, m.home_field, x, y));
    const int dx = x < m.sx0 ? m.sx0 - x : (x > m.sx1 ? x - m.sx1 : 0);
    const int dy = y < m.sy0 ? m.sy0 - y : (y > m.sy1 ? y - m.sy1 : 0);
    return imax(dx, dy);
}
// How far the enemy spawn is from (x, y): my home distance at the mirrored tile.
int enemy_home_distance(const Map& m, int x, int y) {
    int mx, my;
    m.mirror(x, y, mx, my);
    return home_distance(m, mx, my);
}

const UnitObs* find_enemy(const Obs& o, int id) {
    for (int i = 0; i < o.n_enemy; ++i)
        if (o.enemy[i].id == id) return &o.enemy[i];
    return nullptr;
}

// Chebyshev distance from (x, y) to the nearest visible enemy (99 when none).
int nearest_enemy(const Obs& o, int x, int y) {
    int best = 99;
    for (int i = 0; i < o.n_enemy; ++i) best = imin(best, cheb(x, y, o.enemy[i].x, o.enemy[i].y));
    return best;
}

float hp_frac(const UnitObs& u) { return clampf(u.hp / fmax2(1.0f, u.max_hp), 0.0f, 1.0f); }

bool group_visible(const Obs& o, int g) { return o.gvis[g] != 0; }
bool camp_alive_visible(const Obs& o, int camp) { return o.camp_hp[camp] >= 0; }

} // namespace

void Map::mirror(int x, int y, int& mx, int& my) const {
    mx = (sym == SYM_Y) ? x : w - 1 - x;
    my = (sym == SYM_X) ? y : h - 1 - y;
}

std::uint32_t flags_from_state(std::uint32_t s) {
    std::uint32_t f = 0;
    if (s & (1u << 3)) f |= F_CAN_MOVE;
    if (s & (1u << 4)) f |= F_CAN_ATTACK;
    if (s & (1u << 11)) f |= F_CAN_CAST;
    if (s & (1u << 1)) f |= F_RECALLING;
    if (s & (1u << 2)) f |= F_TRIBUTING;
    if (s & (1u << 12)) f |= F_TELEPORTING;
    return f;
}

void camp_stats(int type, float& max_hp, float& strength, int& range) {
    // wolf, elk, gem cluster, gold cluster, monolith, golem
    static const float hp[6] = {1350, 2400, 120, 120, 20000, 5000}, str[6] = {20, 60, 0, 0, 200, 120};
    static const int rng[6] = {3, 4, 0, 0, 5, 4};
    const int t = (type >= 0 && type < 6) ? type : 0;
    max_hp = hp[t];
    strength = str[t];
    range = rng[t];
}

void reset_obs(Obs& o) {
    o.round = 0;
    o.me = UnitObs{};
    o.focus = 0;
    o.gold = 0;
    o.flags = 0;
    o.ability_kind[0] = o.ability_kind[1] = 0;
    o.cooldown[0] = o.cooldown[1] = 0;
    o.ability_range[0] = o.ability_range[1] = o.ability_radius[0] = o.ability_radius[1] = 0;
    o.ability_excl[0] = o.ability_excl[1] = 0;
    o.n_ally = o.n_enemy = o.n_camp = o.n_group = o.n_awake = 0;
}

void refresh_group_cache(Map& m) {
    for (int g = 0; g < m.n_groups; ++g) {
        const GroupStatic& G = m.groups[g];
        m.gterr[g] = clampf(static_cast<float>(home_distance(m, G.cx, G.cy) - enemy_home_distance(m, G.cx, G.cy)) / 50.0f, -3, 3);
    }
}

void finalize_obs(const Map& m, Obs& o) {
    for (int i = 0; i < m.n_camps; ++i) {
        o.camp_hp[i] = -1;
        o.camp_awake[i] = 0;
    }
    for (int g = 0; g < m.n_groups; ++g) {
        o.gvis[g] = o.gstanding[g] = o.gstate[g] = 0;
        o.gtimer[g] = 0;
    }
    o.n_awake = 0;
    for (int k = 0; k < o.n_camp; ++k) {
        const int c = o.camp[k].idx;
        if (c < 0 || c >= m.n_camps) continue;
        o.camp_hp[c] = o.camp[k].hp;
        o.camp_awake[c] = o.camp[k].awake ? 1 : 0;
        ++o.gstanding[m.camps[c].group];
        if (o.camp[k].awake) o.awake[o.n_awake++] = static_cast<std::int16_t>(c);
    }
    for (int k = 0; k < o.n_group; ++k)
        if (o.group[k].g >= 0 && o.group[k].g < m.n_groups) {
            o.gvis[o.group[k].g] = 1;
            o.gstate[o.group[k].g] = static_cast<std::uint8_t>(o.group[k].state);
            o.gtimer[o.group[k].g] = static_cast<std::int16_t>(o.group[k].timer);
        }
}

void begin_map(Map& m, int w, int h, int sym) {
    for (int d = 0; d <= kNoDist; ++d) m.log1p_d[d] = log1p_pos(static_cast<float>(d));
    m.w = w;
    m.h = h;
    m.sym = sym;
    m.n_camps = m.n_groups = m.n_altars = 0;
    for (int i = 0; i < kMaxTiles; ++i) {
        m.terr[i] = 0;
        m.camp_at[i] = -1;
    }
    for (int g = 0; g < kMaxGroups; ++g) {
        m.groups[g] = GroupStatic{};
        m.gfield[g] = nullptr;
    }
    m.altar_field = m.home_field = nullptr;
}

void add_camp(Map& m, int group, int x, int y, int type, float max_hp, float strength, int range) {
    if (m.n_camps >= kMaxCamps || group < 0 || group >= kMaxGroups) return;
    CampStatic& c = m.camps[m.n_camps];
    c.x = static_cast<std::int16_t>(x);
    c.y = static_cast<std::int16_t>(y);
    c.group = static_cast<std::int16_t>(group);
    c.type = static_cast<std::uint8_t>(type);
    c.range = static_cast<std::uint8_t>(range);
    c.max_hp = max_hp;
    c.strength = strength;
    GroupStatic& G = m.groups[group];
    if (G.n == 0) G.first = m.n_camps;
    ++G.n;
    if (group + 1 > m.n_groups) m.n_groups = group + 1;
    ++m.n_camps;
}

void set_group(Map& m, int g, int gold, int gems, int respawn) {
    if (g < 0 || g >= kMaxGroups) return;
    m.groups[g].gold = gold;
    m.groups[g].gems = gems;
    m.groups[g].respawn = respawn;
    if (g + 1 > m.n_groups) m.n_groups = g + 1;
}

void finish_map(Map& m) {
    m.sx0 = m.w;
    m.sy0 = m.h;
    m.sx1 = -1;
    m.sy1 = -1;
    m.n_altars = 0;
    for (int y = 0; y < m.h; ++y)
        for (int x = 0; x < m.w; ++x) {
            const std::uint8_t t = m.terr[m.idx(x, y)];
            if (t & T_MYSPAWN) {
                m.sx0 = imin(m.sx0, x);
                m.sy0 = imin(m.sy0, y);
                m.sx1 = imax(m.sx1, x);
                m.sy1 = imax(m.sy1, y);
            }
            if ((t & T_ALTAR) && m.n_altars < kMaxAltars) {
                m.ax[m.n_altars] = static_cast<std::int16_t>(x);
                m.ay[m.n_altars] = static_cast<std::int16_t>(y);
                ++m.n_altars;
            }
        }
    for (int i = 0; i < m.n_camps; ++i) {
        const CampStatic& c = m.camps[i];
        if (m.inside(c.x, c.y)) {
            m.terr[m.idx(c.x, c.y)] |= T_CAMP;
            m.camp_at[m.idx(c.x, c.y)] = static_cast<std::int16_t>(i);
        }
    }
    for (int i = 0; i < m.w * m.h; ++i) m.bush_id[i] = -1;
    int clusters = 0;
    static int stack[kMaxTiles];
    for (int i = 0; i < m.n_camps; ++i) {
        const CampStatic& c = m.camps[i];
        m.camp_bush[i] = -1;
        if (!m.inside(c.x, c.y) || !(m.terr[m.idx(c.x, c.y)] & T_BUSH)) continue;
        const int start = m.idx(c.x, c.y);
        if (m.bush_id[start] < 0) {
            const auto id = static_cast<std::int16_t>(clusters++);
            int sp = 0;
            stack[sp++] = start;
            m.bush_id[start] = id;
            while (sp > 0) {
                const int t = stack[--sp], tx = t % m.w, ty = t / m.w;
                for (int dy = -1; dy <= 1; ++dy)
                    for (int dx = -1; dx <= 1; ++dx) {
                        const int nx = tx + dx, ny = ty + dy;
                        if ((!dx && !dy) || !m.inside(nx, ny)) continue;
                        const int j = m.idx(nx, ny);
                        if ((m.terr[j] & T_BUSH) && m.bush_id[j] < 0) {
                            m.bush_id[j] = id;
                            stack[sp++] = j;
                        }
                    }
            }
        }
        m.camp_bush[i] = m.bush_id[start];
    }
    for (int g = 0; g < m.n_groups; ++g) {
        GroupStatic& G = m.groups[g];
        G.hp_total = G.str_total = 0;
        if (G.n == 0) continue;
        float mx = 0, my = 0;
        for (int i = G.first; i < G.first + G.n; ++i) {
            G.hp_total += m.camps[i].max_hp;
            G.str_total += m.camps[i].strength;
            mx += m.camps[i].x;
            my += m.camps[i].y;
        }
        mx /= static_cast<float>(G.n);
        my /= static_cast<float>(G.n);
        float best = 1e9f;
        for (int i = G.first; i < G.first + G.n; ++i) {
            const float dx = m.camps[i].x - mx, dy = m.camps[i].y - my, d2 = dx * dx + dy * dy;
            if (d2 < best) {
                best = d2;
                G.cx = m.camps[i].x;
                G.cy = m.camps[i].y;
            }
        }
    }
    refresh_group_cache(m);
}

void blocked_mask(const Map& m, std::uint8_t* blocked) {
    for (int i = 0; i < m.w * m.h; ++i)
        blocked[i] = (m.terr[i] & (T_WALL | T_HOLE | T_ALTAR | T_ENEMYSPAWN | T_CAMP)) ? 1 : 0;
}
void group_roots(const Map& m, int g, std::uint8_t* roots) {
    for (int i = 0; i < m.w * m.h; ++i) roots[i] = 0;
    const GroupStatic& G = m.groups[g];
    for (int i = G.first; i < G.first + G.n; ++i) roots[m.idx(m.camps[i].x, m.camps[i].y)] = 1;
}
void altar_roots(const Map& m, std::uint8_t* roots) {
    for (int i = 0; i < m.w * m.h; ++i) roots[i] = (m.terr[i] & T_ALTAR) ? 1 : 0;
}
void home_roots(const Map& m, std::uint8_t* roots) {
    for (int i = 0; i < m.w * m.h; ++i) roots[i] = (m.terr[i] & T_MYSPAWN) ? 1 : 0;
}

void bfs(const Map& m, const std::uint8_t* blocked, const std::uint8_t* roots, std::uint16_t* out) {
    static int queue[kMaxTiles];
    const int n = m.w * m.h;
    int head = 0, tail = 0;
    for (int i = 0; i < n; ++i) {
        out[i] = kFar;
        if (roots[i]) {
            out[i] = 0;
            queue[tail++] = i;
        }
    }
    while (head < tail) {
        const int i = queue[head++], x = i % m.w, y = i / m.w;
        const std::uint16_t d = static_cast<std::uint16_t>(out[i] + 1);
        for (int dy = -1; dy <= 1; ++dy)
            for (int dx = -1; dx <= 1; ++dx) {
                const int nx = x + dx, ny = y + dy;
                if ((!dx && !dy) || !m.inside(nx, ny)) continue;
                const int j = m.idx(nx, ny);
                if (!blocked[j] && out[j] == kFar) {
                    out[j] = d;
                    queue[tail++] = j;
                }
            }
    }
}

bool on_my_spawn(const Map& m, int x, int y) { return m.inside(x, y) && (m.terr[m.idx(x, y)] & T_MYSPAWN); }

bool next_to_altar(const Map& m, int x, int y) {
    for (int i = 0; i < m.n_altars; ++i)
        if (cheb(x, y, m.ax[i], m.ay[i]) <= 1) return true;
    return false;
}

std::uint32_t encode_slot(int x, int y) {
    const std::uint32_t cx = static_cast<std::uint32_t>(imin(imax(x, 0), 99) / 4 + 1);
    const std::uint32_t cy = static_cast<std::uint32_t>(imin(imax(y, 0), 99) / 4 + 1);
    return cx | (cy << 5);
}
bool decode_slot(std::uint32_t v, int& x, int& y) {
    const int cx = static_cast<int>(v & 31u), cy = static_cast<int>((v >> 5) & 31u);
    if (!cx || !cy) return false;
    x = (cx - 1) * 4 + 1;
    y = (cy - 1) * 4 + 1;
    return true;
}
std::uint32_t read_slot(const std::uint8_t* mem8, int slot) {
    std::uint64_t all = 0;
    for (int b = 0; b < 8; ++b) all |= static_cast<std::uint64_t>(mem8[b]) << (8 * b);
    return static_cast<std::uint32_t>((all >> (kSlotBits * slot)) & ((1u << kSlotBits) - 1));
}
void write_slot(std::uint8_t* mem8, int slot, std::uint32_t v) {
    std::uint64_t all = 0;
    for (int b = 0; b < 8; ++b) all |= static_cast<std::uint64_t>(mem8[b]) << (8 * b);
    const std::uint64_t mask = static_cast<std::uint64_t>((1u << kSlotBits) - 1) << (kSlotBits * slot);
    all = (all & ~mask) | ((static_cast<std::uint64_t>(v) << (kSlotBits * slot)) & mask);
    for (int b = 0; b < 8; ++b) mem8[b] = static_cast<std::uint8_t>(all >> (8 * b));
}
void add_remembered_allies(Obs& o, const std::uint8_t* mem8, const int* ids, int n_ids) {
    for (int k = 0; k < n_ids && k < kMaxSide; ++k) {
        const int id = ids[k];
        if (id == o.me.id) continue;
        bool seen = false;
        for (int i = 0; i < o.n_ally; ++i) seen |= o.ally[i].id == id;
        int x, y;
        if (seen || o.n_ally >= kMaxSide || !decode_slot(read_slot(mem8, k), x, y)) continue;
        UnitObs& u = o.ally[o.n_ally++];
        u = UnitObs{};
        u.id = id;
        u.x = x;
        u.y = y;
        u.hp = u.max_hp = 1;
        u.exact = false;
    }
}

bool occupied(const Map& m, const Obs& o, int x, int y) {
    if (!m.inside(x, y) || m.solid(x, y)) return true;
    if (o.me.x == x && o.me.y == y) return true;
    for (int i = 0; i < o.n_ally; ++i)
        if (o.ally[i].exact && o.ally[i].x == x && o.ally[i].y == y) return true;
    for (int i = 0; i < o.n_enemy; ++i)
        if (o.enemy[i].x == x && o.enemy[i].y == y) return true;
    const int c = m.camp_at[m.idx(x, y)];
    if (c >= 0) {
        // A camp tile is free only when the camp is known dead: its group is in vision and either has no living
        // camps (reward or respawning), or this camp is not among the visible living ones and could have been seen
        // (a camp inside a bush is hidden from outside, so it may still stand). Out of vision, assume it stands.
        const int g = m.camps[c].group;
        if (!group_visible(o, g) || camp_alive_visible(o, c)) return true;
        if (o.gstate[g] == 1 && m.camp_bush[c] >= 0) return true;
    }
    return false;
}

// ---- Memory ----

void observe(const Map& m, const Obs& o, Memory& mem) {
    float hp_sum[kMaxGroups];
    for (int g = 0; g < m.n_groups; ++g) hp_sum[g] = 0;
    for (int i = 0; i < o.n_camp; ++i) {
        const int c = o.camp[i].idx;
        if (c >= 0 && c < m.n_camps) hp_sum[m.camps[c].group] += o.camp[i].hp;
    }
    for (int i = 0; i < o.n_group; ++i) {
        const GroupObs& go = o.group[i];
        if (go.g < 0 || go.g >= m.n_groups) continue;
        GroupMem& gm = mem.g[go.g];
        gm.seen = o.round;
        if (go.state == 1) {
            gm.state = G_ALIVE;
            gm.hp_left = hp_sum[go.g];
        } else if (go.state == 2) {
            gm.state = G_REWARD;
            gm.hp_left = 0;
        } else if (go.state == 3) {
            gm.state = G_RESPAWN;
            gm.eta = o.round + go.timer;
            gm.hp_left = -1;
        }
    }
    for (int g = 0; g < m.n_groups; ++g) {
        GroupMem& gm = mem.g[g];
        // Out of vision a respawning group is assumed back once its timer has run out. In vision the engine's state
        // stands: a timer held at zero means someone occupies a spawn tile and the group cannot come back.
        if (gm.state == G_RESPAWN && o.round >= gm.eta && !o.gvis[g]) {
            gm.state = G_ALIVE;
            gm.hp_left = -1;
        }
    }
    for (int i = 0; i < o.n_enemy; ++i) {
        const UnitObs& e = o.enemy[i];
        int slot = -1, oldest = 0;
        for (int k = 0; k < kMaxSide; ++k) {
            if (mem.e[k].id == e.id) {
                slot = k;
                break;
            }
            if (mem.e[k].round < mem.e[oldest].round) oldest = k;
        }
        if (slot < 0) slot = oldest;
        mem.e[slot].id = e.id;
        mem.e[slot].x = e.x;
        mem.e[slot].y = e.y;
        mem.e[slot].round = o.round;
        for (int g = 0; g < m.n_groups; ++g)
            if (cheb(e.x, e.y, m.groups[g].cx, m.groups[g].cy) <= 6) mem.g[g].enemy_round = o.round;
    }
}

void end_observe(const Obs& o, Memory& mem) {
    mem.prev_x = o.me.x;
    mem.prev_y = o.me.y;
    mem.last_round = o.round;
}

// ---- Objectives ----

const char* const kObjNames[NF_OBJ] = {
    "farm", "bank", "home", "fight",
    "f_d", "f_logd", "f_near", "f_gems", "f_gold", "f_rate", "f_hpleft", "f_turns", "f_campthreat",
    "f_alive", "f_reward", "f_respawn", "f_wait", "f_unseen", "f_age", "f_enemy_recent", "f_allies_near",
    "f_allies_closer", "f_territory", "f_myhp", "f_hurt_threat", "f_carry", "f_round", "f_partial",
    "f_rel", "f_rank0", "f_rank3", "f_ready_near", "f_ready_rate", "f_crew_turns", "f_redundant",
    "f_capture_covered", "f_solo_threat", "f_ready_rel",
    "b_d", "b_gems", "b_rate", "b_enemies", "b_round", "b_myhp",
    "h_d", "h_hurt", "h_hurt2", "h_gold", "h_gold150", "h_gems", "h_enemies", "h_at", "h_farm_d",
    "x_d", "x_hp", "x_hits", "x_myhp", "x_gems", "x_balance", "x_onspawn", "x_ranged", "x_power", "x_threat",
    "x_channel", "x_depth"};

int objective_distance(const Map& m, const Obs& o, Objective ob, int x, int y) {
    switch (ob.kind) {
    case O_FARM: {
        if (ob.arg < 0 || ob.arg >= m.n_groups) return kNoDist;
        const int base = group_distance(m, ob.arg, x, y);
        if (o.gstate[ob.arg] != G_ALIVE) return base;
        // Static fields root at every spawn tile. After a partial clear a dead root can strand the champion
        // outside attack range of the survivors. Close to the group, use the surviving (or bush-hidden) camps.
        int live = kNoDist;
        const GroupStatic& G = m.groups[ob.arg];
        for (int c = G.first; c < G.first + G.n; ++c)
            if (camp_alive_visible(o, c) || m.camp_bush[c] >= 0)
                live = imin(live, cheb(x, y, m.camps[c].x, m.camps[c].y));
        return live < kNoDist ? imax(base, live) : base;
    }
    case O_BANK: return altar_distance(m, x, y);
    case O_HOME: return home_distance(m, x, y);
    default: {
        const UnitObs* e = find_enemy(o, ob.arg);
        return e ? cheb(x, y, e->x, e->y) : kNoDist;
    }
    }
}

bool at_goal(const Map& m, const Obs& o, const Memory& mem, Objective ob, int x, int y) {
    switch (ob.kind) {
    case O_FARM: {
        if (ob.arg < 0 || ob.arg >= m.n_groups) return false;
        const GroupStatic& G = m.groups[ob.arg];
        if (mem.g[ob.arg].state == G_REWARD) {
            const int c = m.inside(x, y) ? m.camp_at[m.idx(x, y)] : -1;
            return c >= 0 && m.camps[c].group == ob.arg;
        }
        const bool vis = group_visible(o, ob.arg);
        for (int i = G.first; i < G.first + G.n; ++i) {
            if (cheb(x, y, m.camps[i].x, m.camps[i].y) > o.me.range) continue;
            if (camp_alive_visible(o, i)) return true;
            // Out of vision: assume it stands where it spawned, unless a bush hides it (then I must go in).
            if (!vis && m.camp_bush[i] < 0) return true;
        }
        return false;
    }
    case O_BANK: return next_to_altar(m, x, y);
    case O_HOME: return on_my_spawn(m, x, y);
    default: {
        const UnitObs* e = find_enemy(o, ob.arg);
        return e && cheb(x, y, e->x, e->y) <= o.me.range;
    }
    }
}

int objective_candidates(const Map& m, const Obs& o, const Memory& mem, Objective* out, float* feat) {
    const float hp = hp_frac(o.me), hurt = 1.0f - hp, dmg = fmax2(1.0f, o.me.strength), myhp = fmax2(1.0f, o.me.max_hp);
    const float round = static_cast<float>(o.round) / 2000.0f, carry = static_cast<float>(o.me.gems) / 50.0f;
    const float enemies = fmin2(static_cast<float>(o.n_enemy), 3.0f) / 3.0f;
    // Distances first: the nearest available group (standing, reward waiting, or back by the time I arrive) sets the
    // scale for every group's relative distance and rank.
    int dist[kMaxGroups];
    bool avail[kMaxGroups];
    int dmin = kNoDist;
    // Histograms over distance (0 .. kNoDist): of all groups (the candidate cut below) and of the available ones
    // (ranks), so neither needs a pairwise pass over the groups.
    static int all_at[kNoDist + 2], avail_below[kNoDist + 2];
    for (int d = 0; d <= kNoDist + 1; ++d) all_at[d] = avail_below[d] = 0;
    for (int g = 0; g < m.n_groups; ++g) {
        dist[g] = m.groups[g].n ? group_distance(m, g, o.me.x, o.me.y) : kNoDist;
        const GroupMem& gm = mem.g[g];
        avail[g] = dist[g] < kNoDist && (gm.state != G_RESPAWN || gm.eta - o.round <= dist[g]);
        if (avail[g]) dmin = imin(dmin, dist[g]);
        if (m.groups[g].n) ++all_at[dist[g]];
        if (avail[g]) ++avail_below[dist[g] + 1];
    }
    for (int d = 1; d <= kNoDist + 1; ++d) avail_below[d] += avail_below[d - 1]; // now: available groups nearer than d
    // Candidates: the kFarmCands nearest groups (the top teams' choice is among them 99.8% of the time); at the cut
    // distance, groups in index order.
    int cut = kNoDist, room = kFarmCands;
    for (int d = 0, seen = 0; d <= kNoDist; ++d) {
        if (seen + all_at[d] >= kFarmCands) {
            cut = d;
            room = kFarmCands - seen;
            break;
        }
        seen += all_at[d];
    }
    int n = 0;
    auto row = [&](std::uint8_t kind, int arg) -> float* {
        out[n].kind = kind;
        out[n].arg = arg;
        float* f = feat + n * NF_OBJ;
        for (int j = 0; j < NF_OBJ; ++j) f[j] = 0;
        f[kind] = 1;
        ++n;
        return f;
    };
    for (int g = 0; g < m.n_groups && n < kMaxObj; ++g) {
        const GroupStatic& G = m.groups[g];
        if (G.n == 0) continue;
        const int d = dist[g];
        if (d >= kNoDist && m.gfield[g]) continue; // unreachable
        if (d > cut) continue;
        if (d == cut) {
            if (room <= 0) continue;
            --room;
        }
        const GroupMem& gm = mem.g[g];
        // A known empty group is not a useful job until it is close to coming back. The unconstrained logit
        // otherwise repeatedly chooses its nearest dead root, even with a long respawn timer.
        if (gm.state == G_RESPAWN && gm.eta - o.round > d + 5) continue;
        if (gm.state == G_REWARD) {
            // One capturer is enough. Give the reward region to the nearest visible ally, breaking equal
            // distances by champion id. A champion already on the region has distance zero and keeps it.
            // Only exact allies participate: coarse shared positions cannot establish capture ownership.
            bool delegated = false;
            for (int i = 0; i < o.n_ally && !delegated; ++i) {
                const UnitObs& a = o.ally[i];
                if (!a.exact) continue;
                const int da = group_distance(m, g, a.x, a.y);
                delegated = da < d || (da == d && a.id < o.me.id);
            }
            if (delegated) continue;
        }
        float* f = row(O_FARM, g);
        const float hp_left = gm.state == G_REWARD ? 0.0f : (gm.state == G_ALIVE && gm.hp_left >= 0 ? gm.hp_left : G.hp_total);
        f[OF_D] = clampf(static_cast<float>(d) / 50.0f, 0, 6);
        f[OF_LOGD] = m.log1p_d[imin(imax(d, 0), kNoDist)] / 4.0f;
        f[OF_NEAR] = d <= 4 ? 1.0f : 0.0f;
        f[OF_GEMS] = static_cast<float>(G.gems) / 50.0f;
        f[OF_GOLD] = static_cast<float>(G.gold) / 100.0f;
        f[OF_RATE] = (static_cast<float>(G.gems) + static_cast<float>(G.gold) / 4.0f) / (static_cast<float>(d) + 10.0f) / 2.0f;
        f[OF_HPLEFT] = hp_left / 2000.0f;
        f[OF_TURNS] = clampf(hp_left / dmg / 100.0f, 0, 5);
        f[OF_CAMPTHREAT] = clampf(G.str_total / myhp, 0, 3);
        f[OF_ALIVE] = gm.state == G_ALIVE ? 1.0f : 0.0f;
        f[OF_REWARD] = gm.state == G_REWARD ? 1.0f : 0.0f;
        f[OF_RESPAWN] = gm.state == G_RESPAWN ? 1.0f : 0.0f;
        f[OF_WAIT] = gm.state == G_RESPAWN ? clampf(static_cast<float>(gm.eta - o.round - d), 0, 100) / 50.0f : 0.0f;
        f[OF_UNSEEN] = gm.seen < 0 ? 1.0f : 0.0f;
        f[OF_AGE] = gm.seen < 0 ? 1.0f : fmin2(static_cast<float>(o.round - gm.seen), 300.0f) / 300.0f;
        f[OF_ENEMY_RECENT] = (o.round - gm.enemy_round) <= 20 ? 1.0f : 0.0f;
        int near = 0, closer = 0, covered = 0;
        float crew_damage = dmg;
        const int mine = cheb(o.me.x, o.me.y, G.cx, G.cy);
        for (int i = 0; i < o.n_ally; ++i) {
            const int da = cheb(o.ally[i].x, o.ally[i].y, G.cx, G.cy);
            near += da <= 6;
            closer += da < mine;
            if (da <= 6 && o.ally[i].exact) crew_damage += fmax2(0, o.ally[i].strength);
            if (gm.state == G_REWARD && o.ally[i].exact && m.inside(o.ally[i].x, o.ally[i].y)) {
                const int c = m.camp_at[m.idx(o.ally[i].x, o.ally[i].y)];
                covered |= c >= 0 && m.camps[c].group == g;
            }
        }
        f[OF_ALLIES_NEAR] = static_cast<float>(imin(near, 3)) / 3.0f;
        f[OF_ALLIES_CLOSER] = static_cast<float>(imin(closer, 3)) / 3.0f;
        f[OF_TERRITORY] = m.gterr[g];
        f[OF_MYHP] = hp;
        f[OF_HURT_THREAT] = hurt * f[OF_CAMPTHREAT];
        f[OF_CARRY] = carry;
        f[OF_READY_NEAR] = avail[g] && d <= 4;
        f[OF_READY_RATE] = avail[g] ? f[OF_RATE] : 0;
        f[OF_CREW_TURNS] = clampf(hp_left / crew_damage / 100.0f, 0, 5);
        f[OF_REDUNDANT] = static_cast<float>(imin(near, 3)) * 300.0f / (hp_left + 300.0f);
        f[OF_CAPTURE_COVERED] = covered;
        f[OF_SOLO_THREAT] = clampf(G.str_total / fmax2(1, o.me.hp) / static_cast<float>(near + 1), 0, 3);
        f[OF_READY_REL] = avail[g] && dmin < kNoDist ? clampf(static_cast<float>(d - dmin) / 20.0f, 0, 5) : 0;
        f[OF_ROUND] = round;
        f[OF_PARTIAL] = (gm.state == G_ALIVE && gm.hp_left >= 0 && gm.hp_left < 0.95f * G.hp_total) ? 1.0f : 0.0f;
        f[OF_REL] = dmin < kNoDist ? clampf(static_cast<float>(d - dmin) / 20.0f, 0, 5) : 0.0f;
        if (avail[g]) {
            const int rank = avail_below[d];
            f[OF_RANK0] = rank == 0 ? 1.0f : 0.0f;
            f[OF_RANK3] = rank < 3 ? 1.0f : 0.0f;
        }
    }
    if (o.me.gems > 0 && m.n_altars > 0 && n < kMaxObj) {
        const int d = altar_distance(m, o.me.x, o.me.y);
        if (d < kNoDist || !m.altar_field) {
            float* f = row(O_BANK, -1);
            f[OB_D] = clampf(static_cast<float>(d) / 50.0f, 0, 6);
            f[OB_GEMS] = carry;
            f[OB_RATE] = static_cast<float>(o.me.gems) / (static_cast<float>(d) + 10.0f) / 2.0f;
            f[OB_ENEMIES] = enemies;
            f[OB_ROUND] = round;
            f[OB_MYHP] = hp;
        }
    }
    if (n < kMaxObj) {
        const int d = home_distance(m, o.me.x, o.me.y);
        float* f = row(O_HOME, -1);
        f[OH_D] = clampf(static_cast<float>(d) / 50.0f, 0, 6);
        f[OH_HURT] = hurt;
        f[OH_HURT2] = hurt * hurt;
        f[OH_GOLD] = static_cast<float>(imin(o.gold, 600)) / 150.0f;
        f[OH_GOLD150] = o.gold >= 150 ? 1.0f : 0.0f;
        f[OH_GEMS] = carry;
        f[OH_ENEMIES] = enemies;
        f[OH_AT] = d == 0 ? 1.0f : 0.0f;
        f[OH_FARM_D] = clampf(static_cast<float>(dmin) / 50.0f, 0, 6);
    }
    for (int i = 0; i < o.n_enemy && n < kMaxObj; ++i) {
        const UnitObs& e = o.enemy[i];
        float* f = row(O_FIGHT, e.id);
        const int d = cheb(o.me.x, o.me.y, e.x, e.y);
        int friends = 1, foes = 0;
        for (int k = 0; k < o.n_ally; ++k) friends += cheb(o.ally[k].x, o.ally[k].y, e.x, e.y) <= 6;
        for (int k = 0; k < o.n_enemy; ++k) foes += cheb(o.enemy[k].x, o.enemy[k].y, e.x, e.y) <= 6;
        const float mine = o.me.hp * fmax2(1.0f, o.me.strength), theirs = fmax2(1.0f, e.hp) * fmax2(1.0f, e.strength);
        f[OX_D] = static_cast<float>(d) / 10.0f;
        f[OX_HP] = hp_frac(e);
        f[OX_HITS] = clampf(e.hp / dmg / 20.0f, 0, 3);
        f[OX_MYHP] = hp;
        f[OX_GEMS] = static_cast<float>(e.gems) / 50.0f;
        f[OX_BALANCE] = clampf(static_cast<float>(friends - foes) / 3.0f, -2, 2);
        int ex, ey;
        m.mirror(e.x, e.y, ex, ey);
        f[OX_ONSPAWN] = on_my_spawn(m, ex, ey) ? 1.0f : 0.0f; // the mirror of their spawn is mine
        f[OX_RANGED] = ranged_hero(e.type) ? 1.0f : 0.0f;
        f[OX_POWER] = clampf((mine - theirs) / (mine + theirs), -1, 1);
        f[OX_THREAT] = clampf(e.strength / myhp * 10.0f, 0, 3);
        f[OX_CHANNEL] = (e.flags & (F_RECALLING | F_TRIBUTING)) ? 1.0f : 0.0f;
        f[OX_DEPTH] = clampf(static_cast<float>(home_distance(m, e.x, e.y)) / 50.0f, 0, 6);
    }
    return n;
}

// ---- Movement ----

const char* const kMoveNames[NF_MOVE] = {
    "stay", "dash", "dd", "closer", "farther", "goal", "goal_stay", "threat_n", "threat_w", "hit_n", "near_enemy",
    "can_hit", "adj_enemy", "camp_threat", "allies2", "allies5", "spawn", "bush", "hurt_threat", "hurt_dd",
    "hp_can_hit", "fight_dd", "farm_dd", "bank_dd", "home_dd", "fight_goal", "d_near", "hurt_d_near", "back",
    "reward_tile", "target_bush", "blocks_respawn", "capture_stay", "farm_wait", "camp_damage", "hurt_camp"};

int move_candidates(const Map& m, const Obs& o, const Memory& mem, Objective ob, bool dash_ready, MoveCand* out,
                    float* feat) {
    int n = 0;
    out[n++] = MoveCand{o.me.x, o.me.y, false};
    for (int dy = -1; dy <= 1; ++dy)
        for (int dx = -1; dx <= 1; ++dx) {
            const int x = o.me.x + dx, y = o.me.y + dy;
            if ((dx || dy) && !occupied(m, o, x, y)) out[n++] = MoveCand{x, y, false};
        }
    if (dash_ready)
        for (int dy = -2; dy <= 2; ++dy)
            for (int dx = -2; dx <= 2; ++dx) {
                if (imax(iabs(dx), iabs(dy)) != 2 || n >= kMaxMoves) continue;
                const int x = o.me.x + dx, y = o.me.y + dy;
                if (occupied(m, o, x, y)) continue;
                // Some tile in between must not be a wall or an altar (holes can be crossed).
                const int sx = dx > 0 ? 1 : (dx < 0 ? -1 : 0), sy = dy > 0 ? 1 : (dy < 0 ? -1 : 0);
                bool path = false;
                const int mids[2][2] = {{sx, sy}, {iabs(dx) == 2 ? sx : 0, iabs(dy) == 2 ? sy : 0}};
                for (const auto& mid : mids) {
                    const int mx = o.me.x + mid[0], my = o.me.y + mid[1];
                    if ((mid[0] || mid[1]) && m.inside(mx, my) && !(m.terr[m.idx(mx, my)] & (T_WALL | T_ALTAR))) path = true;
                }
                if (path) out[n++] = MoveCand{x, y, true};
            }
    const float hp = hp_frac(o.me), hurt = 1.0f - hp, myhp = fmax2(1.0f, o.me.hp);
    // A farm objective: its camps near me (the only ones in reach of a candidate tile) and the bush clusters that
    // hide any of its camps.
    const bool farm_goal = ob.kind == O_FARM && ob.arg >= 0 && ob.arg < m.n_groups;
    const bool reward = farm_goal && mem.g[ob.arg].state == G_REWARD, goal_vis = farm_goal && group_visible(o, ob.arg);
    int goal_camps[kMaxCamps], n_goal_camps = 0, obj_bush[kMaxCamps], n_obj_bush = 0;
    if (farm_goal) {
        const GroupStatic& G = m.groups[ob.arg];
        for (int k = G.first; k < G.first + G.n; ++k) {
            if (cheb(o.me.x, o.me.y, m.camps[k].x, m.camps[k].y) <= o.me.range + 2) goal_camps[n_goal_camps++] = k;
            const int b = m.camp_bush[k];
            bool known = b < 0;
            for (int j = 0; j < n_obj_bush && !known; ++j) known = obj_bush[j] == b;
            if (!known) obj_bush[n_obj_bush++] = b;
        }
    }
    // Awake camps that could reach any candidate tile (all lie within 2 of me): the only ones the per-tile count needs.
    int near_awake[kMaxCamps], n_near_awake = 0;
    for (int k = 0; k < o.n_awake; ++k) {
        const CampStatic& cs = m.camps[o.awake[k]];
        if (cheb(o.me.x, o.me.y, cs.x, cs.y) <= cs.range + 2) near_awake[n_near_awake++] = o.awake[k];
    }
    const int d0 = objective_distance(m, o, ob, o.me.x, o.me.y), near0 = nearest_enemy(o, o.me.x, o.me.y);
    const float fight = ob.kind == O_FIGHT, farm = ob.kind == O_FARM, bank = ob.kind == O_BANK, home = ob.kind == O_HOME;
    for (int i = 0; i < n; ++i) {
        const int x = out[i].x, y = out[i].y;
        float* f = feat + i * NF_MOVE;
        for (int j = 0; j < NF_MOVE; ++j) f[j] = 0;
        const bool stay = i == 0;
        const int d = objective_distance(m, o, ob, x, y);
        const float dd = clampf(static_cast<float>(d - d0), -3, 3) / 3.0f;
        bool goal;
        if (farm_goal) {
            // at_goal() for a farm objective, over the objective's camps near me only (the same answer: a camp in
            // reach of a tile within 2 of me is within range + 2 of me).
            goal = false;
            if (reward) {
                const int c = m.camp_at[m.idx(x, y)];
                goal = c >= 0 && m.camps[c].group == ob.arg;
            } else
                for (int k = 0; k < n_goal_camps && !goal; ++k) {
                    const int i = goal_camps[k];
                    if (cheb(x, y, m.camps[i].x, m.camps[i].y) > o.me.range) continue;
                    goal = camp_alive_visible(o, i) || (!goal_vis && m.camp_bush[i] < 0);
                }
        } else
            goal = at_goal(m, o, mem, ob, x, y);
        int threat_n = 0, hit_n = 0, can_hit = 0, adj = 0;
        float threat_w = 0;
        for (int k = 0; k < o.n_enemy; ++k) {
            const UnitObs& e = o.enemy[k];
            const int de = cheb(x, y, e.x, e.y);
            if (de <= e.range + 1) {
                ++threat_n;
                threat_w += e.strength;
            }
            hit_n += de <= e.range;
            can_hit |= de <= o.me.range;
            adj |= de <= 1;
        }
        int camp_threat = 0;
        float camp_damage = 0;
        for (int k = 0; k < n_near_awake; ++k) {
            const CampStatic& cs = m.camps[near_awake[k]];
            if (cheb(x, y, cs.x, cs.y) <= cs.range) { ++camp_threat; camp_damage += cs.strength; }
        }
        int allies2 = 0, allies5 = 0;
        for (int k = 0; k < o.n_ally; ++k) {
            const int da = cheb(x, y, o.ally[k].x, o.ally[k].y);
            allies2 += da <= 2;
            allies5 += da <= 5;
        }
        const int near = nearest_enemy(o, x, y);
        const float d_near = o.n_enemy ? clampf(static_cast<float>(near - near0), -3, 3) / 3.0f : 0.0f;
        f[0] = stay;
        f[1] = out[i].dash;
        f[2] = dd;
        f[3] = d < d0;
        f[4] = d > d0;
        f[5] = goal;
        f[6] = goal && stay;
        f[7] = static_cast<float>(imin(threat_n, 3)) / 3.0f;
        f[8] = clampf(threat_w / myhp * 5.0f, 0, 3);
        f[9] = static_cast<float>(imin(hit_n, 3)) / 3.0f;
        f[10] = static_cast<float>(imin(near, 10)) / 10.0f;
        f[11] = can_hit;
        f[12] = adj;
        f[13] = static_cast<float>(imin(camp_threat, 3)) / 3.0f;
        f[14] = static_cast<float>(imin(allies2, 3)) / 3.0f;
        f[15] = static_cast<float>(imin(allies5, 3)) / 3.0f;
        f[16] = on_my_spawn(m, x, y);
        f[17] = (m.terr[m.idx(x, y)] & T_BUSH) ? 1.0f : 0.0f;
        f[18] = hurt * f[7];
        f[19] = hurt * dd;
        f[20] = hp * f[11];
        f[21] = fight * dd;
        f[22] = farm * dd;
        f[23] = bank * dd;
        f[24] = home * dd;
        f[25] = fight * goal;
        f[26] = d_near;
        f[27] = hurt * d_near;
        f[28] = (!stay && x == mem.prev_x && y == mem.prev_y) ? 1.0f : 0.0f;
        const int c = m.camp_at[m.idx(x, y)];
        f[29] = (c >= 0 && mem.g[m.camps[c].group].state == G_REWARD) ? 1.0f : 0.0f;
        f[30] = 0;
        const int bid = m.bush_id[m.idx(x, y)];
        if (farm_goal && bid >= 0)
            for (int k = 0; k < n_obj_bush; ++k) f[30] = obj_bush[k] == bid ? 1.0f : f[30];
        // Standing on a spawn tile of a group that is due back holds the whole group back.
        f[31] = 0;
        if (c >= 0) {
            const int g = m.camps[c].group;
            const bool due = o.gvis[g] ? (o.gstate[g] == 3 && o.gtimer[g] <= 1)
                                       : (mem.g[g].state == G_RESPAWN && mem.g[g].eta - o.round <= 1);
            f[31] = due ? 1.0f : 0.0f;
        }
        f[32] = reward && goal && stay;
        f[33] = farm_goal && mem.g[ob.arg].state == G_RESPAWN && d <= 1;
        f[34] = clampf(camp_damage / myhp * 10.0f, 0, 3);
        f[35] = hurt * f[34];
    }
    return n;
}

// ---- Basic attack ----

const char* const kTgtNames[NF_TGT] = {
    "none", "champion", "camp", "hp", "hits", "kill", "objective", "threat", "ranged", "gems", "allies_adj",
    "awake", "none_hp", "none_threat", "none_ranged", "lowest", "closest", "channel", "camp_last"};

int target_candidates(const Map& m, const Obs& o, const Memory& mem, Objective ob, int x, int y, TargetCand* out,
                      float* feat) {
    (void)mem;
    int n = 0;
    out[n++] = TargetCand{0, -1};
    for (int i = 0; i < o.n_enemy && n < kMaxTargets; ++i)
        if (cheb(x, y, o.enemy[i].x, o.enemy[i].y) <= o.me.range) out[n++] = TargetCand{1, o.enemy[i].id};
    for (int i = 0; i < o.n_camp && n < kMaxTargets; ++i) {
        const CampStatic& cs = m.camps[o.camp[i].idx];
        if (cheb(x, y, cs.x, cs.y) <= o.me.range) out[n++] = TargetCand{2, o.camp[i].idx};
    }
    const float hp = hp_frac(o.me), dmg = fmax2(1.0f, o.me.strength), myhp = fmax2(1.0f, o.me.max_hp);
    int threat_n = 0;
    for (int k = 0; k < o.n_enemy; ++k) threat_n += cheb(x, y, o.enemy[k].x, o.enemy[k].y) <= o.enemy[k].range + 1;
    // Among champion candidates: the lowest health fraction and the closest.
    float low = 2.0f;
    int close = 99;
    for (int i = 1; i < n; ++i)
        if (out[i].kind == 1) {
            const UnitObs* e = find_enemy(o, out[i].id);
            low = fmin2(low, hp_frac(*e));
            close = imin(close, cheb(x, y, e->x, e->y));
        }
    // Camps of the same group still standing (the last one completes the clear).
    for (int i = 0; i < n; ++i) {
        float* f = feat + i * NF_TGT;
        for (int j = 0; j < NF_TGT; ++j) f[j] = 0;
        if (out[i].kind == 0) {
            f[0] = 1;
            f[12] = hp;
            f[13] = static_cast<float>(imin(threat_n, 3)) / 3.0f;
            f[14] = ranged_hero(o.me.type);
            continue;
        }
        float thp, tmax, tstr;
        int tx, ty;
        if (out[i].kind == 1) {
            const UnitObs* e = find_enemy(o, out[i].id);
            thp = e->hp;
            tmax = e->max_hp;
            tstr = e->strength;
            tx = e->x;
            ty = e->y;
            f[1] = 1;
            f[6] = (ob.kind == O_FIGHT && ob.arg == e->id) ? 1.0f : 0.0f;
            f[8] = ranged_hero(e->type);
            f[9] = static_cast<float>(e->gems) / 50.0f;
            f[15] = hp_frac(*e) <= low;
            f[16] = cheb(x, y, e->x, e->y) <= close;
            f[17] = (e->flags & (F_RECALLING | F_TRIBUTING)) ? 1.0f : 0.0f;
        } else {
            const CampStatic& cs = m.camps[out[i].id];
            thp = o.camp_hp[out[i].id];
            tmax = cs.max_hp;
            tstr = cs.strength;
            tx = cs.x;
            ty = cs.y;
            f[2] = 1;
            f[6] = (ob.kind == O_FARM && ob.arg == cs.group) ? 1.0f : 0.0f;
            f[11] = o.camp_awake[out[i].id];
            f[18] = o.gstanding[cs.group] == 1;
        }
        int adj = 0;
        for (int k = 0; k < o.n_ally; ++k) adj += cheb(o.ally[k].x, o.ally[k].y, tx, ty) <= 1;
        f[3] = clampf(thp / fmax2(1.0f, tmax), 0, 1);
        f[4] = clampf(thp / dmg / 10.0f, 0, 3);
        f[5] = thp <= dmg;
        f[7] = clampf(tstr / myhp * 10.0f, 0, 3);
        f[10] = static_cast<float>(imin(adj, 3)) / 3.0f;
    }
    return n;
}

// ---- Spells ----

const char* const kCastNames[NF_CAST] = {
    "none", "damage", "aoe", "cc", "heal", "shield", "reset", "t_champion", "t_camp", "t_ally", "t_hp", "t_hits",
    "t_objective", "enemies4", "allies4", "myhp", "enemy_in_reach", "camp_hits", "excl_far", "aoe_champs", "aoe_camps",
    "t_channel", "none_enemies", "none_myhp"};

int cast_candidates(const Map& m, const Obs& o, const Memory& mem, Objective ob, int x, int y, CastCand* out,
                    float* feat) {
    (void)mem;
    int n = 0;
    out[n++] = CastCand{};
    const bool can = (o.flags & F_CAN_CAST) != 0;
    for (int s = 0; s < 2 && can; ++s) {
        const int kind = o.ability_kind[s];
        if (kind == 0 || kind == 6 || o.cooldown[s] > 0) continue; // none, dash (the move model's), cooling down
        const int range = static_cast<int>(o.ability_range[s]);
        auto add = [&](int tkind, int id, int tx, int ty) {
            if (n >= kMaxCasts) return;
            CastCand& c = out[n++];
            c.slot = s;
            c.kind = kind;
            c.tkind = tkind;
            c.id = id;
            c.x = tx;
            c.y = ty;
        };
        if (kind == 7 || kind == 1) { // shield, attack reset: on myself
            add(4, o.me.id, x, y);
            continue;
        }
        if (kind == 5) { // heal: another allied champion in vision
            for (int k = 0; k < o.n_ally; ++k)
                if (o.ally[k].exact && cheb(x, y, o.ally[k].x, o.ally[k].y) <= range) add(3, o.ally[k].id, o.ally[k].x, o.ally[k].y);
            continue;
        }
        // damage (2), area damage (3), stun (4): enemy champions and camps in range
        for (int k = 0; k < o.n_enemy; ++k)
            if (cheb(x, y, o.enemy[k].x, o.enemy[k].y) <= range) add(1, o.enemy[k].id, o.enemy[k].x, o.enemy[k].y);
        for (int k = 0; k < o.n_camp; ++k) {
            const CampStatic& cs = m.camps[o.camp[k].idx];
            if (cheb(x, y, cs.x, cs.y) <= range) add(2, o.camp[k].idx, cs.x, cs.y);
        }
    }
    const float hp = hp_frac(o.me), dmg = fmax2(1.0f, o.me.strength);
    int enemies4 = 0, allies4 = 0, in_reach = 0, camp_hits = 0;
    for (int k = 0; k < o.n_enemy; ++k) {
        const int d = cheb(x, y, o.enemy[k].x, o.enemy[k].y);
        enemies4 += d <= 4;
        in_reach |= d <= o.me.range;
    }
    for (int k = 0; k < o.n_ally; ++k) allies4 += cheb(x, y, o.ally[k].x, o.ally[k].y) <= 4;
    for (int k = 0; k < o.n_awake; ++k) {
        const CampStatic& cs = m.camps[o.awake[k]];
        camp_hits |= cheb(x, y, cs.x, cs.y) <= cs.range;
    }
    const bool far = objective_distance(m, o, ob, x, y) > o.me.range;
    for (int i = 0; i < n; ++i) {
        float* f = feat + i * NF_CAST;
        for (int j = 0; j < NF_CAST; ++j) f[j] = 0;
        const CastCand& c = out[i];
        if (c.slot < 0) {
            f[0] = 1;
            f[22] = static_cast<float>(imin(enemies4, 3)) / 3.0f;
            f[23] = hp;
            continue;
        }
        const int kf[8] = {0, 6, 1, 2, 3, 4, 0, 5}; // ability kind -> feature: reset 6, damage 1, aoe 2, cc 3, heal 4, shield 5
        f[kf[c.kind]] = 1;
        f[13] = static_cast<float>(imin(enemies4, 3)) / 3.0f;
        f[14] = static_cast<float>(imin(allies4, 3)) / 3.0f;
        f[15] = hp;
        f[16] = in_reach;
        f[17] = camp_hits;
        f[18] = (o.ability_excl[c.slot] && far) ? 1.0f : 0.0f;
        float thp = 0, tmax = 1;
        if (c.tkind == 1) {
            const UnitObs* e = find_enemy(o, c.id);
            thp = e->hp;
            tmax = e->max_hp;
            f[7] = 1;
            f[12] = (ob.kind == O_FIGHT && ob.arg == c.id) ? 1.0f : 0.0f;
            f[21] = (e->flags & (F_RECALLING | F_TRIBUTING)) ? 1.0f : 0.0f;
        } else if (c.tkind == 2) {
            thp = o.camp_hp[c.id];
            tmax = m.camps[c.id].max_hp;
            f[8] = 1;
            f[12] = (ob.kind == O_FARM && ob.arg == m.camps[c.id].group) ? 1.0f : 0.0f;
        } else if (c.tkind == 3) {
            for (int k = 0; k < o.n_ally; ++k)
                if (o.ally[k].id == c.id) {
                    thp = o.ally[k].hp;
                    tmax = o.ally[k].max_hp;
                }
            f[9] = 1;
        } else {
            thp = o.me.hp;
            tmax = o.me.max_hp;
        }
        f[10] = clampf(thp / fmax2(1.0f, tmax), 0, 1);
        f[11] = clampf(thp / dmg / 10.0f, 0, 3);
        if (c.kind == 3) {
            const int r = static_cast<int>(o.ability_radius[c.slot]);
            int champs = 0, campsn = 0;
            for (int k = 0; k < o.n_enemy; ++k) champs += cheb(c.x, c.y, o.enemy[k].x, o.enemy[k].y) <= r;
            for (int k = 0; k < o.n_camp; ++k) {
                const CampStatic& cs = m.camps[o.camp[k].idx];
                campsn += cheb(c.x, c.y, cs.x, cs.y) <= r;
            }
            f[19] = static_cast<float>(imin(champs, 3)) / 3.0f;
            f[20] = static_cast<float>(imin(campsn, 3)) / 3.0f;
        }
    }
    return n;
}

// ---- Channels ----

const char* const kRecallNames[NF_RECALL] = {"bias", "hp", "hurt2", "d_home", "gold", "gems", "enemies", "near_enemy",
                                             "round", "ranged"};

void recall_features(const Map& m, const Obs& o, const Memory& mem, float* f) {
    (void)mem;
    const float hp = hp_frac(o.me);
    f[0] = 1;
    f[1] = hp;
    f[2] = (1 - hp) * (1 - hp);
    f[3] = clampf(static_cast<float>(home_distance(m, o.me.x, o.me.y)) / 50.0f, 0, 6);
    f[4] = static_cast<float>(imin(o.gold, 600)) / 150.0f;
    f[5] = static_cast<float>(o.me.gems) / 50.0f;
    f[6] = static_cast<float>(imin(o.n_enemy, 3)) / 3.0f;
    f[7] = static_cast<float>(imin(nearest_enemy(o, o.me.x, o.me.y), 10)) / 10.0f;
    f[8] = static_cast<float>(o.round) / 2000.0f;
    f[9] = ranged_hero(o.me.type);
}

const char* const kTribNames[NF_TRIB] = {"bias", "gems", "enemies", "hp", "near_enemy", "round"};

void tribute_features(const Map& m, const Obs& o, const Memory& mem, float* f) {
    (void)m;
    (void)mem;
    f[0] = 1;
    f[1] = static_cast<float>(o.me.gems) / 50.0f;
    f[2] = static_cast<float>(imin(o.n_enemy, 3)) / 3.0f;
    f[3] = hp_frac(o.me);
    f[4] = static_cast<float>(imin(nearest_enemy(o, o.me.x, o.me.y), 10)) / 10.0f;
    f[5] = static_cast<float>(o.round) / 2000.0f;
}

namespace {
struct Fnv {
    std::uint32_t h = 2166136261u;
    void u(std::uint32_t v) {
        for (int b = 0; b < 4; ++b) {
            h ^= (v >> (8 * b)) & 0xFFu;
            h *= 16777619u;
        }
    }
    void i(int v) { u(static_cast<std::uint32_t>(v)); }
    void f(float v) {
        std::uint32_t bits;
        static_assert(sizeof(bits) == sizeof(v));
        __builtin_memcpy(&bits, &v, sizeof(bits));
        u(bits);
    }
    void unit(const UnitObs& a) {
        i(a.id); i(a.type); i(a.x); i(a.y); i(a.range); i(a.gems); f(a.hp); f(a.max_hp); f(a.strength);
        u(a.flags); i(a.exact ? 1 : 0);
    }
};
} // namespace

std::uint32_t hash_obs(const Obs& o) {
    Fnv z;
    z.i(o.round);
    z.unit(o.me);
    z.f(o.focus);
    z.i(o.gold);
    z.u(o.flags);
    for (int s = 0; s < 2; ++s) {
        z.i(o.ability_kind[s]);
        z.i(o.cooldown[s]);
        z.f(o.ability_range[s]);
        z.f(o.ability_radius[s]);
        z.i(o.ability_excl[s]);
    }
    z.i(o.n_ally);
    for (int k = 0; k < o.n_ally; ++k) z.unit(o.ally[k]);
    z.i(o.n_enemy);
    for (int k = 0; k < o.n_enemy; ++k) z.unit(o.enemy[k]);
    z.i(o.n_camp);
    for (int k = 0; k < o.n_camp; ++k) {
        z.i(o.camp[k].idx);
        z.f(o.camp[k].hp);
        z.i(o.camp[k].awake ? 1 : 0);
    }
    z.i(o.n_group);
    for (int k = 0; k < o.n_group; ++k) {
        z.i(o.group[k].g);
        z.i(o.group[k].state);
        z.i(o.group[k].timer);
    }
    return z.h;
}

namespace {
struct Text {
    char* p;
    int cap, n = 0;
    void put(const char* s) {
        while (*s && n + 1 < cap) p[n++] = *s++;
        p[n] = 0;
    }
    void num(long long v) {
        char b[24];
        int k = 0;
        const bool neg = v < 0;
        unsigned long long u = neg ? static_cast<unsigned long long>(-v) : static_cast<unsigned long long>(v);
        do {
            b[k++] = static_cast<char>('0' + u % 10);
            u /= 10;
        } while (u);
        if (neg) b[k++] = '-';
        char r[24];
        for (int i = 0; i < k; ++i) r[i] = b[k - 1 - i];
        r[k] = 0;
        put(r);
    }
    void fl(float v) { num(static_cast<long long>(v * 1000.0f)); } // milli-units: enough to spot a difference
    void sep() { put(","); }
};
} // namespace

int dump_obs(const Obs& o, char* buf, int cap) {
    Text t{buf, cap};
    auto unit = [&](const UnitObs& u) {
        t.put("["); t.num(u.id); t.sep(); t.num(u.type); t.sep(); t.num(u.x); t.sep(); t.num(u.y); t.sep();
        t.num(u.range); t.sep(); t.num(u.gems); t.sep(); t.fl(u.hp); t.sep(); t.fl(u.max_hp); t.sep(); t.fl(u.strength);
        t.sep(); t.num(u.flags); t.sep(); t.num(u.exact ? 1 : 0); t.put("]");
    };
    t.put("r"); t.num(o.round); t.put(" me"); unit(o.me); t.put(" f"); t.fl(o.focus); t.put(" g"); t.num(o.gold);
    t.put(" fl"); t.num(o.flags); t.put(" ab"); t.num(o.ability_kind[0]); t.sep(); t.num(o.ability_kind[1]);
    t.put(" cd"); t.num(o.cooldown[0]); t.sep(); t.num(o.cooldown[1]);
    t.put(" A"); for (int k = 0; k < o.n_ally; ++k) unit(o.ally[k]);
    t.put(" E"); for (int k = 0; k < o.n_enemy; ++k) unit(o.enemy[k]);
    t.put(" C"); for (int k = 0; k < o.n_camp; ++k) { t.put("["); t.num(o.camp[k].idx); t.sep(); t.fl(o.camp[k].hp); t.sep(); t.num(o.camp[k].awake); t.put("]"); }
    t.put(" G"); for (int k = 0; k < o.n_group; ++k) { t.put("["); t.num(o.group[k].g); t.sep(); t.num(o.group[k].state); t.sep(); t.num(o.group[k].timer); t.put("]"); }
    return t.n;
}

int dump_map(const Map& m, char* buf, int cap) {
    Text t{buf, cap};
    t.put("C");
    for (int i = 0; i < m.n_camps; ++i) {
        const CampStatic& c = m.camps[i];
        t.put("["); t.num(c.x); t.sep(); t.num(c.y); t.sep(); t.num(c.group); t.sep(); t.num(c.type); t.sep();
        t.num(c.range); t.sep(); t.fl(c.max_hp); t.sep(); t.fl(c.strength); t.put("]");
    }
    t.put(" G");
    for (int g = 0; g < m.n_groups; ++g) {
        const GroupStatic& G = m.groups[g];
        t.put("["); t.num(G.gold); t.sep(); t.num(G.gems); t.sep(); t.num(G.respawn); t.sep(); t.num(G.n); t.sep();
        t.num(G.first); t.sep(); t.num(G.cx); t.sep(); t.num(G.cy); t.put("]");
    }
    return t.n;
}

void hash_obs_parts(const Obs& o, std::uint32_t* out) {
    Fnv a, b, c, d, e;
    a.i(o.round);
    a.unit(o.me);
    a.f(o.focus);
    a.i(o.gold);
    a.u(o.flags);
    for (int s = 0; s < 2; ++s) {
        a.i(o.ability_kind[s]);
        a.i(o.cooldown[s]);
        a.f(o.ability_range[s]);
        a.f(o.ability_radius[s]);
        a.i(o.ability_excl[s]);
    }
    b.i(o.n_ally);
    for (int k = 0; k < o.n_ally; ++k) b.unit(o.ally[k]);
    c.i(o.n_enemy);
    for (int k = 0; k < o.n_enemy; ++k) c.unit(o.enemy[k]);
    d.i(o.n_camp);
    for (int k = 0; k < o.n_camp; ++k) {
        d.i(o.camp[k].idx);
        d.f(o.camp[k].hp);
        d.i(o.camp[k].awake ? 1 : 0);
    }
    e.i(o.n_group);
    for (int k = 0; k < o.n_group; ++k) {
        e.i(o.group[k].g);
        e.i(o.group[k].state);
        e.i(o.group[k].timer);
    }
    out[0] = a.h;
    out[1] = b.h;
    out[2] = c.h;
    out[3] = d.h;
    out[4] = e.h;
}

void hash_map_parts(const Map& m, std::uint32_t* out) {
    Fnv a, b, c, d;
    a.i(m.w); a.i(m.h); a.i(m.sym);
    for (int i = 0; i < m.w * m.h; ++i) a.u(m.terr[i]);
    b.i(m.n_camps);
    for (int i = 0; i < m.n_camps; ++i) {
        const CampStatic& cs = m.camps[i];
        b.i(cs.x); b.i(cs.y); b.i(cs.group); b.i(cs.type);
    }
    c.i(m.n_groups);
    for (int g = 0; g < m.n_groups; ++g) {
        const GroupStatic& G = m.groups[g];
        c.i(G.gold); c.i(G.gems); c.i(G.respawn); c.i(G.n); c.i(G.first);
    }
    d.i(m.n_altars);
    d.i(m.sx0); d.i(m.sy0); d.i(m.sx1); d.i(m.sy1);
    out[0] = a.h;
    out[1] = b.h;
    out[2] = c.h;
    out[3] = d.h;
}

std::uint32_t hash_memory(const Map& m, const Memory& mem) {
    Fnv z;
    for (int g = 0; g < m.n_groups; ++g) {
        z.i(mem.g[g].state);
        z.i(mem.g[g].seen);
        z.i(mem.g[g].eta);
        z.f(mem.g[g].hp_left);
        z.i(mem.g[g].enemy_round);
    }
    for (const auto& e : mem.e) {
        z.i(e.id);
        z.i(e.x);
        z.i(e.y);
        z.i(e.round);
    }
    z.i(mem.prev_x);
    z.i(mem.prev_y);
    return z.h;
}

std::uint32_t hash_decisions(const Map& m, const Obs& o, const Memory& mem) {
    static float feat[kMaxObj * NF_OBJ];
    static Objective obj[kMaxObj];
    static MoveCand mv[kMaxMoves];
    static TargetCand tg[kMaxTargets];
    Fnv z;
    const int n = objective_candidates(m, o, mem, obj, feat);
    z.i(n);
    for (int i = 0; i < n; ++i) {
        z.i(obj[i].kind);
        z.i(obj[i].arg);
    }
    for (int i = 0; i < n * NF_OBJ; ++i) z.f(feat[i]);
    const Objective home{O_HOME, -1};
    const int nm = move_candidates(m, o, mem, home, true, mv, feat);
    z.i(nm);
    for (int i = 0; i < nm; ++i) {
        z.i(mv[i].x);
        z.i(mv[i].y);
        z.i(mv[i].dash ? 1 : 0);
    }
    for (int i = 0; i < nm * NF_MOVE; ++i) z.f(feat[i]);
    const int nt = target_candidates(m, o, mem, home, o.me.x, o.me.y, tg, feat);
    z.i(nt);
    for (int i = 0; i < nt; ++i) {
        z.i(tg[i].kind);
        z.i(tg[i].id);
    }
    for (int i = 0; i < nt * NF_TGT; ++i) z.f(feat[i]);
    static CastCand cc[kMaxCasts];
    const int nc = cast_candidates(m, o, mem, home, o.me.x, o.me.y, cc, feat);
    z.i(nc);
    for (int i = 0; i < nc; ++i) {
        z.i(cc[i].slot);
        z.i(cc[i].tkind);
        z.i(cc[i].id);
    }
    for (int i = 0; i < nc * NF_CAST; ++i) z.f(feat[i]);
    recall_features(m, o, mem, feat);
    for (int i = 0; i < NF_RECALL; ++i) z.f(feat[i]);
    return z.h;
}

std::uint32_t hash_field(const Map& m, const std::uint16_t* f) {
    Fnv z;
    for (int i = 0; i < m.w * m.h; ++i) z.u(f[i]);
    return z.h;
}

std::uint32_t hash_map(const Map& m) {
    Fnv z;
    z.i(m.w); z.i(m.h); z.i(m.sym);
    for (int i = 0; i < m.w * m.h; ++i) z.u(m.terr[i]);
    z.i(m.n_camps);
    for (int i = 0; i < m.n_camps; ++i) {
        const CampStatic& c = m.camps[i];
        z.i(c.x); z.i(c.y); z.i(c.group); z.i(c.type); z.i(c.range); z.f(c.max_hp); z.f(c.strength);
    }
    z.i(m.n_groups);
    for (int g = 0; g < m.n_groups; ++g) {
        const GroupStatic& G = m.groups[g];
        z.i(G.gold); z.i(G.gems); z.i(G.respawn); z.i(G.n); z.i(G.first); z.i(G.cx); z.i(G.cy);
    }
    z.i(m.n_altars);
    z.i(m.sx0); z.i(m.sy0); z.i(m.sx1); z.i(m.sy1);
    return z.h;
}

void score(const float* w, const float* feat, int n, int nf, float* out) {
    // Four interleaved partial sums (the compiler maps them onto one f32x4 lane each): about a quarter of the fuel of
    // a plain loop. Training sums in another order; only the bot and the extractor must agree, and both run this.
    for (int i = 0; i < n; ++i) {
        const float* f = feat + i * nf;
#if defined(__wasm_simd128__)
        v128_t sum = wasm_f32x4_splat(0);
        int j = 0;
        for (; j + 4 <= nf; j += 4)
            sum = wasm_f32x4_add(sum, wasm_f32x4_mul(wasm_v128_load(w + j), wasm_v128_load(f + j)));
        float a0 = wasm_f32x4_extract_lane(sum, 0), a1 = wasm_f32x4_extract_lane(sum, 1);
        const float a2 = wasm_f32x4_extract_lane(sum, 2), a3 = wasm_f32x4_extract_lane(sum, 3);
#else
        float a0 = 0, a1 = 0, a2 = 0, a3 = 0;
        int j = 0;
        for (; j + 4 <= nf; j += 4) {
            a0 += w[j] * f[j];
            a1 += w[j + 1] * f[j + 1];
            a2 += w[j + 2] * f[j + 2];
            a3 += w[j + 3] * f[j + 3];
        }
#endif
        for (; j < nf; ++j) a0 += w[j] * f[j];
        out[i] = (a0 + a1) + (a2 + a3);
    }
}

void score_objectives(const float* w, const float* feat, const Objective* obj, int n, float* out) {
    // A candidate's features are zero outside its own kind's block, so only that block is summed (the other terms
    // are exact zeros).
    static const int lo[4] = {OF_D, OB_D, OH_D, OX_D}, hi[4] = {OB_D, OH_D, OX_D, NF_OBJ};
    for (int i = 0; i < n; ++i) {
        const float* f = feat + i * NF_OBJ;
        const int k = obj[i].kind;
#if defined(__wasm_simd128__)
        v128_t sum = wasm_f32x4_make(w[k] * f[k], 0, 0, 0);
        int j = lo[k];
        for (; j + 4 <= hi[k]; j += 4)
            sum = wasm_f32x4_add(sum, wasm_f32x4_mul(wasm_v128_load(w + j), wasm_v128_load(f + j)));
        float a0 = wasm_f32x4_extract_lane(sum, 0), a1 = wasm_f32x4_extract_lane(sum, 1);
        const float a2 = wasm_f32x4_extract_lane(sum, 2), a3 = wasm_f32x4_extract_lane(sum, 3);
#else
        float a0 = w[k] * f[k], a1 = 0, a2 = 0, a3 = 0;
        int j = lo[k];
        for (; j + 4 <= hi[k]; j += 4) {
            a0 += w[j] * f[j];
            a1 += w[j + 1] * f[j + 1];
            a2 += w[j + 2] * f[j + 2];
            a3 += w[j + 3] * f[j + 3];
        }
#endif
        for (; j < hi[k]; ++j) a0 += w[j] * f[j];
        out[i] = (a0 + a1) + (a2 + a3);
    }
}

int argmax(const float* s, int n) {
    int best = 0;
    for (int i = 1; i < n; ++i)
        if (s[i] > s[best]) best = i;
    return best;
}

} // namespace mc
