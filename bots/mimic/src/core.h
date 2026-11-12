// Mimic core: the decision features and scoring shared, byte for byte, by the bot and by the offline replay extractor.
//
// Nothing in this file or core.cpp touches the SDK. The bot (bot.cpp) fills an Obs from SDK calls; the extractor
// (tools/mimic/extract.mjs, through tools/mimic/kernel.cpp compiled to wasm) fills the same Obs from a replay's
// per-champion view. Both then call the same functions, so a model fitted on replay rows sees exactly the inputs the
// bot computes at runtime (tools/mimic/parity.py checks this on local games).
//
// Coordinates are tiles; distances are Chebyshev unless a distance field is named. Teams are relative: "my" side is the
// observing champion's.
#pragma once
#include <cstdint>

namespace mc {

constexpr int kMaxW = 100, kMaxH = 100, kMaxTiles = kMaxW * kMaxH;
constexpr int kMaxCamps = 200, kMaxGroups = 96, kMaxAltars = 16, kMaxSide = 6, kMaxSeen = 8;
constexpr int kFarmCands = 20; // farm candidates per turn: the nearest groups
constexpr int kMaxObj = kMaxGroups + 3 + kMaxSeen, kMaxMoves = 25, kMaxTargets = 24;
constexpr std::uint16_t kFar = 0xFFFF;

// Champion types (bc::champion_type order) and the ranged ones.
enum Hero : int { RYTH, VESPER, VENDETTA, CASSI, ISSAC, STELLAR, PRISM, MARCELLA, WILLOW, REN, VARG, TAVI, HEART, kHeroes };
inline bool ranged_hero(int t) { return t == VESPER || t == CASSI || t == STELLAR || t == PRISM || t == WILLOW || t == TAVI; }

enum Terrain : std::uint8_t { T_WALL = 1, T_HOLE = 2, T_ALTAR = 4, T_BUSH = 8, T_MYSPAWN = 16, T_ENEMYSPAWN = 32, T_CAMP = 64 };
// Map symmetry (bc::symmetry order): reflect x, reflect y, rotate 180.
enum Sym : int { SYM_X = 0, SYM_Y = 1, SYM_ROT = 2 };

struct CampStatic {
    std::int16_t x, y, group;
    std::uint8_t type, range;
    float max_hp, strength;
};

struct GroupStatic {
    int gold = 0, gems = 0, respawn = 0;
    int n = 0;          // member camps: camps[first .. first + n)
    int first = 0;
    float hp_total = 0, str_total = 0;
    std::int16_t cx = 0, cy = 0; // member closest to the members' mean
};

// Static map knowledge for one team. Distance fields are owned by the host (SDK fields in the bot, kernel BFS offline)
// and only pointed to here; a null field falls back to Chebyshev distance.
struct Map {
    int w = 0, h = 0, sym = 0;
    std::uint8_t terr[kMaxTiles];
    std::int16_t camp_at[kMaxTiles];
    // Bush clusters (8-connected) that hold a camp: from outside nobody sees in, so their camps are hidden until
    // one stands in the same cluster. bush_id is the cluster per tile (-1: no such cluster).
    std::int16_t bush_id[kMaxTiles];
    int n_camps = 0, n_groups = 0, n_altars = 0;
    CampStatic camps[kMaxCamps];
    std::int16_t camp_bush[kMaxCamps]; // the camp tile's bush cluster, -1 when not in a bush
    GroupStatic groups[kMaxGroups];
    std::int16_t ax[kMaxAltars], ay[kMaxAltars];
    int sx0 = 0, sy0 = 0, sx1 = 0, sy1 = 0; // my spawn bounding box (inclusive)
    float log1p_d[301]; // ln(1 + d), d = 0 .. 300 (the core's own series, identical in both hosts)
    float gterr[kMaxGroups]; // per group: (my spawn distance - enemy spawn distance) / 50 at its centre (refresh_group_cache)
    const std::uint16_t* gfield[kMaxGroups];
    const std::uint16_t* altar_field = nullptr;
    const std::uint16_t* home_field = nullptr;

    int idx(int x, int y) const { return y * w + x; }
    bool inside(int x, int y) const { return x >= 0 && y >= 0 && x < w && y < h; }
    // Tiles nobody of my team can stand on: walls, holes, altars, the enemy spawn.
    bool solid(int x, int y) const { return (terr[idx(x, y)] & (T_WALL | T_HOLE | T_ALTAR | T_ENEMYSPAWN)) != 0; }
    void mirror(int x, int y, int& mx, int& my) const;
};

// Camp stats by bc::camp_type (the rules' table), used by both hosts so the features cannot drift apart.
void camp_stats(int type, float& max_hp, float& strength, int& range);

// Host setup, in this order: begin_map, terrain (terr[] flags without T_CAMP), add_camp for every camp grouped by
// group (all camps of group 0 first, ...), set_group, finish_map.
void begin_map(Map& m, int w, int h, int sym);
void add_camp(Map& m, int group, int x, int y, int type, float max_hp, float strength, int range);
void set_group(Map& m, int g, int gold, int gems, int respawn);
void finish_map(Map& m);

// Field definitions shared by the bot (bc::distance_field) and the offline BFS: 8-connected unit steps; blocked tiles
// are walls, holes, altars, the enemy spawn and every camp tile; the roots are the target tiles (a group's camp tiles,
// the altars, or my spawn), which are entered at distance 0 even when blocked. Blocked tiles other than roots read kFar.
void blocked_mask(const Map& m, std::uint8_t* blocked);                      // 1 per blocked tile, w*h bytes
void group_roots(const Map& m, int g, std::uint8_t* roots);                  // w*h bytes
void altar_roots(const Map& m, std::uint8_t* roots);
void home_roots(const Map& m, std::uint8_t* roots);
void bfs(const Map& m, const std::uint8_t* blocked, const std::uint8_t* roots, std::uint16_t* out); // offline only

// ---- Observation (one champion's view at the start of its turn) ----

enum SelfFlags : std::uint32_t { F_CAN_MOVE = 1, F_CAN_ATTACK = 2, F_CAN_CAST = 4, F_RECALLING = 8, F_TRIBUTING = 16,
    F_TELEPORTING = 32, F_STUNNED = 64 };
// From the engine's champion state bits (bc::champion_state: alive 0, recalling 1, submitting 2, can_move 3,
// can_attack 4, can_cast 11, teleporting 12), which both hosts read with the same call.
std::uint32_t flags_from_state(std::uint32_t state);

struct UnitObs {
    int id = -1, type = 0, x = 0, y = 0, range = 1, gems = 0;
    float hp = 0, max_hp = 1, strength = 0;
    std::uint32_t flags = 0; // SelfFlags subset: F_RECALLING, F_TRIBUTING
    bool exact = true;       // in vision; false: an ally known only from shared memory (coarse tile, no stats)
};

// Shared memory (8 bytes, the whole team): one 10-bit slot per allied champion, slot = the champion's rank among
// the allied champion ids (ascending). A slot holds the champion's tile at the end of its last turn, coarse
// (4x4 cells, the cell's corner + 1), or 0 when it was dead then or has not written yet.
constexpr int kSlotBits = 10;
std::uint32_t encode_slot(int x, int y);           // alive at (x, y)
bool decode_slot(std::uint32_t v, int& x, int& y); // false: empty
std::uint32_t read_slot(const std::uint8_t* mem8, int slot);
void write_slot(std::uint8_t* mem8, int slot, std::uint32_t v);

struct CampObs {
    int idx = 0; // into Map::camps
    float hp = 0;
    bool awake = false;
};

struct GroupObs {
    int g = 0;
    int state = 0; // 1 alive, 2 reward available, 3 respawning
    int timer = 0; // rounds until respawn (state 3)
};

struct Obs {
    int round = 0;
    UnitObs me;
    float focus = 0;
    int gold = 0;
    std::uint32_t flags = 0;
    int ability_kind[2] = {0, 0}; // bc::ability_kind values; 0 none
    int cooldown[2] = {0, 0};     // owner turn ends until ready (0 ready)
    float ability_range[2] = {0, 0}, ability_radius[2] = {0, 0}; // cast range, area radius (aoe, dash)
    int ability_excl[2] = {0, 0}; // 1: excludes walking this turn
    int n_ally = 0, n_enemy = 0, n_camp = 0, n_group = 0;
    UnitObs ally[kMaxSide];  // other allied champions that are alive
    UnitObs enemy[kMaxSide]; // visible enemy champions that are alive
    CampObs camp[kMaxCamps]; // visible living camps
    GroupObs group[kMaxGroups]; // groups in vision

    // Derived by finalize_obs (both hosts call it after filling the lists above).
    float camp_hp[kMaxCamps];         // visible living camp's health, -1 otherwise
    std::uint8_t camp_awake[kMaxCamps];
    std::uint8_t gvis[kMaxGroups];    // group in vision
    std::uint8_t gstanding[kMaxGroups]; // visible living camps per group
    std::uint8_t gstate[kMaxGroups];    // the group's state in this view (0: not in vision)
    std::int16_t gtimer[kMaxGroups];    // its respawn timer in this view (state 3)
    int n_awake = 0;
    std::int16_t awake[kMaxCamps];    // indices of visible awake camps
};
void reset_obs(Obs& o);                  // clear counters before filling (cheap: no full re-initialisation)
void finalize_obs(const Map& m, Obs& o); // call after filling the lists, before observe()
void refresh_group_cache(Map& m);        // after finish_map, and again whenever the home field arrives

// Allies out of my vision, from shared memory: append to o.ally (exact = false). ids[k] is the champion in slot k,
// n_ids the number of allied champions; visible allies (already in o.ally) and I are skipped.
void add_remembered_allies(Obs& o, const std::uint8_t* mem8, const int* ids, int n_ids);

// ---- Memory (one champion's, carried across its turns) ----

enum GroupState : std::int8_t { G_UNSEEN = 0, G_ALIVE = 1, G_REWARD = 2, G_RESPAWN = 3 };

struct GroupMem {
    std::int8_t state = G_UNSEEN;
    int seen = -1;           // last round in vision
    int eta = 0;             // expected respawn round (G_RESPAWN)
    float hp_left = -1;      // living camps' health when last seen alive (-1 unknown: full)
    int enemy_round = -1000; // last round a visible enemy stood within 6 of the group's centre
};

struct EnemyMem {
    int id = -1, x = 0, y = 0, round = -1000;
};

struct Memory {
    GroupMem g[kMaxGroups];
    EnemyMem e[kMaxSide];
    int prev_x = -1, prev_y = -1; // my tile at the start of my previous turn
    int last_round = -1;
};

void observe(const Map& m, const Obs& o, Memory& mem); // fold this turn's view into memory (call once per turn, first)
void end_observe(const Obs& o, Memory& mem);           // after all features of the turn: remember my tile

// ---- Decisions ----

enum ObjKind : std::uint8_t { O_FARM = 0, O_BANK = 1, O_HOME = 2, O_FIGHT = 3 };
struct Objective {
    std::uint8_t kind = O_HOME;
    int arg = -1; // group (farm) or enemy champion id (fight)
};

// Objective features: the kind flags, then one block per kind (zero outside the candidate's own block).
enum ObjFeature : int {
    OF_D = 4, OF_LOGD, OF_NEAR, OF_GEMS, OF_GOLD, OF_RATE, OF_HPLEFT, OF_TURNS, OF_CAMPTHREAT, OF_ALIVE, OF_REWARD,
    OF_RESPAWN, OF_WAIT, OF_UNSEEN, OF_AGE, OF_ENEMY_RECENT, OF_ALLIES_NEAR, OF_ALLIES_CLOSER, OF_TERRITORY, OF_MYHP,
    OF_HURT_THREAT, OF_CARRY, OF_ROUND, OF_PARTIAL, OF_REL, OF_RANK0, OF_RANK3,
    OF_READY_NEAR, OF_READY_RATE, OF_CREW_TURNS, OF_REDUNDANT, OF_CAPTURE_COVERED, OF_SOLO_THREAT, OF_READY_REL,
    OB_D, OB_GEMS, OB_RATE, OB_ENEMIES, OB_ROUND, OB_MYHP,
    OH_D, OH_HURT, OH_HURT2, OH_GOLD, OH_GOLD150, OH_GEMS, OH_ENEMIES, OH_AT, OH_FARM_D,
    OX_D, OX_HP, OX_HITS, OX_MYHP, OX_GEMS, OX_BALANCE, OX_ONSPAWN, OX_RANGED, OX_POWER, OX_THREAT, OX_CHANNEL, OX_DEPTH,
    OBJ_FEATURES
};
constexpr int NF_OBJ = OBJ_FEATURES, NF_MOVE = 36, NF_TGT = 19, NF_RECALL = 10, NF_TRIB = 6, NF_CAST = 24;
constexpr int kMaxCasts = 32;
static_assert(NF_OBJ == 65, "objective feature count");

// Objective candidates: the kFarmCands nearest groups (farm), the altars (bank, when carrying gems), home, every
// visible enemy (fight).
int objective_candidates(const Map& m, const Obs& o, const Memory& mem, Objective* out, float* feat);

// Distance from (x, y) to an objective, in steps (fields where built).
int objective_distance(const Map& m, const Obs& o, Objective ob, int x, int y);
bool at_goal(const Map& m, const Obs& o, const Memory& mem, Objective ob, int x, int y);

struct MoveCand {
    int x, y;
    bool dash;
};
// Walk tiles (8 neighbours that are free), staying put, and with `dash_ready` the free tiles within 2 that a dash
// can land on (no wall in between). Index 0 is always staying put.
int move_candidates(const Map& m, const Obs& o, const Memory& mem, Objective ob, bool dash_ready, MoveCand* out,
                    float* feat);

struct TargetCand {
    int kind; // 0 none, 1 champion, 2 camp
    int id;   // champion id or camp index
};
// Basic-attack targets within my attack range of (x, y) (my position, or where I stand after moving). Index 0 is no
// attack.
int target_candidates(const Map& m, const Obs& o, const Memory& mem, Objective ob, int x, int y, TargetCand* out,
                      float* feat);

// Spells (every ability but the dash, which the move model chooses): index 0 casts nothing; then each ready slot on
// each legal target from (x, y): damage and stun on visible enemy champions and camps in range, area damage on the
// tile of an enemy champion or camp in range, heals on visible allies in range, shield and attack reset on myself.
struct CastCand {
    int slot = -1, kind = 0;
    int tkind = 0; // 0 none, 1 enemy champion, 2 camp, 3 ally, 4 self
    int id = -1;   // champion id or camp index
    int x = 0, y = 0; // the target tile
};
int cast_candidates(const Map& m, const Obs& o, const Memory& mem, Objective ob, int x, int y, CastCand* out, float* feat);

void recall_features(const Map& m, const Obs& o, const Memory& mem, float* feat);
void tribute_features(const Map& m, const Obs& o, const Memory& mem, float* feat);

bool on_my_spawn(const Map& m, int x, int y);
bool next_to_altar(const Map& m, int x, int y);
bool occupied(const Map& m, const Obs& o, int x, int y); // a visible unit, a living camp or terrain blocks the tile

// Parity checks (tools/mimic/parity.py): FNV-1a over every observation field, the memory's group states, and the
// candidate lists with their features for a fixed objective (home), so bot and extractor can be compared turn by turn.
std::uint32_t hash_obs(const Obs& o);
std::uint32_t hash_memory(const Map& m, const Memory& mem);
std::uint32_t hash_decisions(const Map& m, const Obs& o, const Memory& mem); // objectives, moves (home), targets, recall
std::uint32_t hash_field(const Map& m, const std::uint16_t* f);
std::uint32_t hash_map(const Map& m); // terrain, camps, groups, altars, spawn box
void hash_obs_parts(const Obs& o, std::uint32_t* out); // [5]: me and scalars, allies, enemies, camps, groups
void hash_map_parts(const Map& m, std::uint32_t* out); // [4]: terrain, camps, groups, altars and spawn box
// Readable dumps for chasing a parity mismatch (returns the length written, NUL-terminated).
int dump_obs(const Obs& o, char* buf, int cap);
int dump_map(const Map& m, char* buf, int cap);

// Linear scores over a candidate feature matrix: out[i] = w . feat[i].
void score(const float* w, const float* feat, int n, int nf, float* out);
// The same for objective candidates, summing only each candidate's own feature block (kind flag + its features).
void score_objectives(const float* w, const float* feat, const Objective* obj, int n, float* out);
int argmax(const float* s, int n);

// Feature names for documentation and training (index order); a null-terminated list per decision.
extern const char* const kObjNames[NF_OBJ];
extern const char* const kMoveNames[NF_MOVE];
extern const char* const kTgtNames[NF_TGT];
extern const char* const kRecallNames[NF_RECALL];
extern const char* const kTribNames[NF_TRIB];
extern const char* const kCastNames[NF_CAST];

} // namespace mc
