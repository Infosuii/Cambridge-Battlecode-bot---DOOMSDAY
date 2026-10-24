// Teacher interface (Agent A): read-only access to the original bot's already-computed decisions and candidates.
//
// Two parts:
//  1. Direct accessors for Bot state the teacher keeps in members (round, carried gems, target_group, flags, World ...).
//     They are plain reads through the `friend struct nn_teacher_access` declaration in bot.h; no capture needed.
//  2. Captures of values that exist only as locals inside the original decision functions (score_groups top-K,
//     tribute verdict, fight verdict, behaviour-chain branch, next purchase, movement steps, spell choice, ward tile,
//     draft scores). The capture calls live in bot.cpp / tsearch.cpp / draft.cpp (agents/A/patches/03_teacher_capture.diff)
//     and are compile-time gated: `if constexpr (nnt::kObjective) ...`. With every head `off` (profiles release /
//     teacher_exact) the gates are false, no capture code is generated and the original translation units compile to
//     the identical Wasm code section (verified: agents/A/REPORT.md).
//
// Rules (CONTRACTS.md 3): constant-initialised PODs only (no dynamic initialisers), bounded buffers, no heap, no SDK
// calls in captures (they copy values the teacher already computed). Each champion runs its own Wasm instance, so one
// buffer per process is one buffer per champion. A capture is valid for the turn whose `round` it carries; accessors
// return nullptr when the teacher did not evaluate that decision this turn.
//
// Candidate convention for heads (CONTRACTS 3.2): candidate 0 is the teacher's choice. Captures already order their
// candidate arrays that way (Objective::cand[0] is the group score_groups returned, Draft keeps the teacher index).
#pragma once
#include <cstdint>

#include "bot.h"
#include "nn_config.h"

namespace nnt {

constexpr bool on(nncfg::H h) { return nncfg::mode(h) != nncfg::Mode::off; }
using H = nncfg::H;

// Capture switches: a capture is compiled only when a head that consumes it is not `off`.
inline constexpr bool kObjective = on(H::objective) || on(H::strategy) || on(H::role) || on(H::value);
inline constexpr bool kBank = on(H::bank) || on(H::strategy) || on(H::value);
inline constexpr bool kFight = on(H::engage) || on(H::combat) || on(H::move) || on(H::strategy);
inline constexpr bool kChain = on(H::strategy) || on(H::role) || on(H::bank) || on(H::value);
inline constexpr bool kShop = on(H::shop);
inline constexpr bool kMove = on(H::move);
inline constexpr bool kCast = on(H::combat);
inline constexpr bool kWard = on(H::ward);
inline constexpr bool kDraft = on(H::draft_pick);
inline constexpr bool kAny = kObjective || kBank || kFight || kChain || kShop || kMove || kCast || kWard || kDraft;

inline constexpr int kMaxGroups = 8;  // == score_groups `RouteCand top[8]`
inline constexpr int kMaxEnemies = 8; // enemies scored by handle_enemies' target loop (bounded copy)
inline constexpr int kMaxSteps = 8;   // follow_field / retreat_from neighbour candidates
inline constexpr int kMaxDraft = 12;  // champion_draft values

// play_turn behaviour chain branch actually taken this turn (after the fact; the teacher's chain decides by acting).
// Turns that return before the chain (channel kept, lab what-ifs) leave no capture: turn() returns nullptr.
enum class Chain : std::uint8_t {
    none = 0,
    dead,        // dead turn: shop, claim dead, fields
    enemy,       // handle_enemies() acted
    tribute_win, // win_now() && tribute_if_needed()
    home,        // go_home_if_needed()
    hunt,        // hunt()
    tribute,     // tribute_if_needed()
    farm,        // farm() returned true
    nofarm,      // farm() returned false
};

struct GroupCand {
    std::int32_t gi = -1, need = 1; // group index (World::groups), champions needed
    float value = 0, cost = 0, score = 0;
    std::int32_t finish = 0; // turns until free again (walk + wait + kill + capture)
};
// score_groups: the route search's first-target candidates (top-K by hand score) and the final teacher choice.
struct Objective {
    std::int32_t round = -1, calls = 0;  // calls: score_groups invocations this round (farm may call it 2-3 times)
    std::int32_t n = 0;                  // candidates in cand[] (cand[0] = teacher choice when teacher_in_top)
    std::int32_t teacher = -1, teacher_need = 1; // score_groups' return value and best_need
    float teacher_score = 0;
    std::int32_t participants_hint = 1;
    std::uint8_t teacher_in_top = 0;     // the returned group is one of the scored top-K (else cand[0] = teacher alone)
    std::uint8_t route_changed = 0;      // route_search picked a first target other than the best single score
    GroupCand cand[kMaxGroups]{};
};
// tribute_if_needed: the bank verdict and every input term (after the bag/altar checks, before the walk/submit).
struct Bank {
    std::int32_t round = -1, calls = 0;
    std::int32_t gems = 0, dist = -1, carry = 0, near_dist = 0; // dist to the altar ring (safe field when used)
    std::uint8_t go = 0, force = 0, wins = 0, late = 0, end_bank = 0, rhythm = 0, edge = 0, threatened = 0, use_safe = 0;
};
struct EnemyCand {
    std::uint32_t id = 0;
    float key = 0, ttk = 0, worth = 0; // teacher target key = ttk / worth (lowest wins)
    std::int32_t dist = 0;
};
// handle_enemies: target scoring, the formula verdict, the search / team verdicts and the final flags.
struct Fight {
    std::int32_t round = -1;
    std::int32_t n = 0;
    EnemyCand cand[kMaxEnemies]{};
    std::uint32_t formula_target_id = 0; // handle_enemies' own target (argmin key), 0 = none
    std::uint32_t target_id = 0;         // final target after a team order, 0 = none
    std::int32_t nearest_d = 99;
    float target_ttk = 0, ttd = 0, threat_on_me = 0, risk = 1;
    std::uint8_t formula_winning = 0, formula_in_danger = 0; // before team / search verdicts
    std::int8_t td_verdict = 2;                              // tactical_decide: +1 fight, -1 run, 0 none, 2 not run
    float td_fight = 0, td_run = 0, td_margin = 0;           // tactical_decide playout means (valid when td_ran)
    std::uint8_t td_ran = 0;
    std::int8_t tfc_order = -1;                              // team order: 1 engage, 2 retreat, 0 none, -1 not consulted
    std::uint8_t winning = 0, in_danger = 0;                 // final flags the flee / engage code acts on
};
struct Turn {
    std::int32_t round = -1;
    Chain chain = Chain::none;
};
// shop(): the teacher's first purchase this call (computed before buying; the purchase itself is unchanged).
struct Shop {
    std::int32_t round = -1;
    std::int32_t gold = 0;
    std::uint8_t lock = 0;           // an altar lock will be bought first
    std::int32_t step = -1;          // build_for index of the first step with want > 0 (-1 = save)
    std::uint32_t item = 0;          // bc::item_type value
    std::int32_t want = 0;           // shards of that step
};
// follow_field: downhill neighbour steps in the teacher's order (cand[0] tried first).
struct Move {
    std::int32_t round = -1, calls = 0;
    std::int32_t n = 0;
    std::int16_t x[kMaxSteps]{}, y[kMaxSteps]{};
    std::int32_t score[kMaxSteps]{};
    std::uint8_t combat = 0; // Bot::combat_move at the call
};
// cast_on_enemy: chosen slot and value, striking-dash alternative.
struct Cast {
    std::int32_t round = -1;
    std::uint32_t target_id = 0;
    std::int32_t slot = -1, dash_slot = -1;
    float value = 0;
    std::int16_t aim_x = -1, aim_y = -1;
};
struct Ward {
    std::int32_t round = -1;
    std::int16_t x = -1, y = -1; // ward_ahead's chosen tile (-1: none)
    std::int32_t key = 0;
};
// ml_draft_pick: net score of every free champion and the pick.
struct Draft {
    std::int32_t picks_made = 0, teacher = -1;
    std::uint8_t legal[kMaxDraft]{};
    float z[kMaxDraft]{};
};

inline Objective g_objective{};
inline Bank g_bank{};
inline Fight g_fight{};
inline Turn g_turn{};
inline Shop g_shop{};
inline Move g_move{};
inline Cast g_cast{};
inline Ward g_ward{};
inline Draft g_draft{};

const char* chain_name(Chain c); // nn_teacher.cpp (logging / tests)

} // namespace nnt

struct nn_teacher_access {
    // ------------------------------------------------------------------ direct teacher state (no capture)
    static int round(const Bot& b) { return b.round; }
    static int slot(const Bot& b) { return b.slot; }
    static int team_size(const Bot& b) { return b.team_size; }
    static bool inited(const Bot& b) { return b.inited; }
    static bc::champion_type type(const Bot& b) { return b.type; }
    static vec2 pos(const Bot& b) { return b.pos; }
    static float hp(const Bot& b) { return b.hp; }
    static float max_hp(const Bot& b) { return b.max_hp; }
    static int gems(const Bot& b) { return b.gems; }
    static int gold(const Bot& b) { return b.gold; }
    static int range(const Bot& b) { return b.range; }
    static bool melee(const Bot& b) { return b.melee; }
    static int cooldown(const Bot& b, int s) { return b.cooldown[static_cast<std::size_t>(s & 1)]; }
    static const Spell& spell(const Bot& b, int s) { return b.spells[static_cast<std::size_t>(s & 1)]; }
    static bool spell_ready(const Bot& b, int s) { return b.spell_ready(s & 1); }
    static bool cast_done(const Bot& b) { return b.cast_done; }
    static bool walked(const Bot& b) { return b.walked; }
    static int ally_score(const Bot& b) { return b.ally_score; }
    static int enemy_score(const Bot& b) { return b.enemy_score; }
    static int target_group(const Bot& b) { return b.target_group; } // committed objective (kClaimDead when dead)
    static bool heading_home(const Bot& b) { return b.heading_home; }
    static bool force_tribute(const Bot& b) { return b.force_tribute; }
    static bool win_now(const Bot& b) { return b.win_now(); }
    static int tribute_carry() { return tune::kTributeCarry; } // after brain/knob adjustments of this turn
    static float retreat_hp() { return tune::kRetreatHp; }
    static float aggression() { return tune::kAggression; }
    static float gold_weight(const Bot& b) { return b.gold_weight(); }
    static const char* mode(const Bot& b) { return b.mode; }
    static std::uint64_t shared(const Bot& b) { return b.shared; } // this turn's shared-memory word (read-only)
    static int claim_of(const Bot& b, int s) { return b.claim_of(s); }
    static int last_flee_round(const Bot& b) { return b.last_flee_round; }
    static int ts_ran_round(const Bot& b) { return b.ts_ran_round; }
    static const World& world(const Bot& b) { return b.w; }
    static int avoid_until(const Bot& b, int gi) {
        return gi >= 0 && static_cast<std::size_t>(gi) < b.avoid_until.size() ? b.avoid_until[static_cast<std::size_t>(gi)] : 0;
    }

    // ------------------------------------------------------------------ captured teacher decisions (this turn only)
    static const nnt::Objective* objective(const Bot& b) { return nnt::g_objective.round == b.round ? &nnt::g_objective : nullptr; }
    static const nnt::Bank* bank(const Bot& b) { return nnt::g_bank.round == b.round ? &nnt::g_bank : nullptr; }
    static const nnt::Fight* fight(const Bot& b) { return nnt::g_fight.round == b.round ? &nnt::g_fight : nullptr; }
    static const nnt::Turn* turn(const Bot& b) { return nnt::g_turn.round == b.round ? &nnt::g_turn : nullptr; }
    static const nnt::Turn& last_turn() { return nnt::g_turn; } // previous turn's branch when called before the chain
    static const nnt::Shop* shop(const Bot& b) { return nnt::g_shop.round == b.round ? &nnt::g_shop : nullptr; }
    static const nnt::Move* move(const Bot& b) { return nnt::g_move.round == b.round ? &nnt::g_move : nullptr; }
    static const nnt::Cast* cast(const Bot& b) { return nnt::g_cast.round == b.round ? &nnt::g_cast : nullptr; }
    static const nnt::Ward* ward(const Bot& b) { return nnt::g_ward.round == b.round ? &nnt::g_ward : nullptr; }
    static const nnt::Draft& draft() { return nnt::g_draft; }

    // Invariant checks used by tests and the dev self-test (nn_teacher.cpp): candidate 0 is the teacher choice, sizes are
    // within bounds, ids are legal indices. Returns 0 when consistent, else a nonzero code naming the first violation.
    static int check_objective(const Bot& b);
    static int check_draft();

    // ------------------------------------------------------------------ capture entry points (called from patch 03)
    // All are inline so a disabled gate leaves nothing behind; each copies values the teacher already computed.
    static void cap_objective(const Bot& b, const Bot::RouteCand* top, int n_top, int best, int best_need, float best_score,
        int participants_hint) {
        auto& o = nnt::g_objective;
        o.calls = o.round == b.round ? o.calls + 1 : 1;
        o.round = b.round;
        o.teacher = best, o.teacher_need = best_need, o.teacher_score = best_score, o.participants_hint = participants_hint;
        o.teacher_in_top = 0, o.route_changed = 0, o.n = 0;
        if (best < 0) return;
        int ti = -1;
        for (int i = 0; i < n_top && i < nnt::kMaxGroups; ++i)
            if (top[i].gi == best) {
                ti = i;
                break;
            }
        o.route_changed = ti > 0;
        auto put = [&](const Bot::RouteCand& r) { o.cand[o.n++] = {r.gi, r.need, r.value, r.cost, r.score, r.finish}; };
        if (ti >= 0) {
            o.teacher_in_top = 1;
            put(top[ti]); // candidate 0 = the teacher's group with its own route-candidate record
            for (int i = 0; i < n_top && i < nnt::kMaxGroups; ++i)
                if (i != ti) put(top[i]);
        } else {
            o.cand[o.n++] = {best, best_need, 0.0f, 0.0f, best_score, 0};
        }
    }
    static void cap_bank(const Bot& b, bool go, int dist, bool wins, bool late, bool end_bank, bool rhythm, bool edge,
        bool threatened, bool use_safe) {
        auto& k = nnt::g_bank;
        k.calls = k.round == b.round ? k.calls + 1 : 1;
        k.round = b.round;
        k.gems = b.gems, k.dist = dist, k.carry = tune::kTributeCarry, k.near_dist = tune::kTributeNearDist;
        k.go = go, k.force = b.force_tribute, k.wins = wins, k.late = late, k.end_bank = end_bank, k.rhythm = rhythm, k.edge = edge;
        k.threatened = threatened, k.use_safe = use_safe;
    }
    static void cap_fight_begin(const Bot& b, int nearest_d, float ttd, float threat_on_me, float risk) {
        auto& f = nnt::g_fight;
        f = nnt::Fight{};
        f.round = b.round, f.nearest_d = nearest_d, f.ttd = ttd, f.threat_on_me = threat_on_me, f.risk = risk;
    }
    static void cap_enemy(const EnemyRec& e, float key, float ttk, float worth, int dist) {
        auto& f = nnt::g_fight;
        if (f.n < nnt::kMaxEnemies) f.cand[f.n++] = {e.id, key, ttk, worth, dist};
    }
    static void cap_formula(const EnemyRec* target, float target_ttk, bool winning, bool in_danger) {
        auto& f = nnt::g_fight;
        f.formula_target_id = f.target_id = target ? target->id : 0;
        f.target_ttk = target_ttk;
        f.formula_winning = winning, f.formula_in_danger = in_danger;
    }
    static void cap_tfc(int order) { nnt::g_fight.tfc_order = static_cast<std::int8_t>(order); }
    static void cap_td_verdict(int verdict) { nnt::g_fight.td_verdict = static_cast<std::int8_t>(verdict); }
    static void cap_td_values(float fight, float run, float margin) {
        auto& f = nnt::g_fight;
        f.td_fight = fight, f.td_run = run, f.td_margin = margin, f.td_ran = 1;
    }
    static void cap_fight_final(const EnemyRec* target, bool winning, bool in_danger, float threat_on_me) {
        auto& f = nnt::g_fight;
        f.target_id = target ? target->id : 0;
        f.winning = winning, f.in_danger = in_danger, f.threat_on_me = threat_on_me;
    }
    static void cap_chain(const Bot& b, nnt::Chain c) { nnt::g_turn = {b.round, c}; }
    static void cap_shop(const Bot& b, bool lock, int step, std::uint32_t item, int want) {
        nnt::g_shop = {b.round, b.gold, static_cast<std::uint8_t>(lock), step, item, want};
    }
    template <class C> static void cap_steps(const Bot& b, const C* cands, int n) {
        auto& m = nnt::g_move;
        m.calls = m.round == b.round ? m.calls + 1 : 1;
        m.round = b.round, m.combat = b.combat_move, m.n = 0;
        for (int i = 0; i < n && i < nnt::kMaxSteps; ++i, ++m.n)
            m.x[i] = static_cast<std::int16_t>(cands[i].p.x), m.y[i] = static_cast<std::int16_t>(cands[i].p.y), m.score[i] = cands[i].score;
    }
    static void cap_cast(const Bot& b, const EnemyRec& e, int slot, float value, int dash_slot, vec2 aim) {
        nnt::g_cast = {b.round, e.id, slot, dash_slot, value, static_cast<std::int16_t>(aim.x), static_cast<std::int16_t>(aim.y)};
    }
    static void cap_ward(const Bot& b, vec2 at, int key) {
        nnt::g_ward = {b.round, static_cast<std::int16_t>(at.x), static_cast<std::int16_t>(at.y), key};
    }
    static void cap_draft_begin() {
        auto& d = nnt::g_draft;
        d.teacher = -1;
        for (int c = 0; c < nnt::kMaxDraft; ++c) d.legal[c] = 0, d.z[c] = 0.0f;
    }
    static void cap_draft_score(int c, float z) {
        if (c >= 0 && c < nnt::kMaxDraft) nnt::g_draft.legal[c] = 1, nnt::g_draft.z[c] = z;
    }
    static void cap_draft_pick(int best) {
        nnt::g_draft.teacher = best;
        ++nnt::g_draft.picks_made;
    }
};
