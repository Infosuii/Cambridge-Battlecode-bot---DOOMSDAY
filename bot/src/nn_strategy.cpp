#include "nn_config.h"
#if NN_ANY_HEAD
#include "nn_strategy.h"
#include "nn_teacher.h"
#include "nn_rt.h"

namespace {
// Each champion has a separate Wasm instance. Constant-initialised POD only, no heap or shared protocol changes.
struct RoleCache { int round = -1000, id = nns::farmer; bool valid = false; };
constinit RoleCache g_role{};
constinit int g_signal_round = -1000;
constinit float g_signal = 0;
nns::Common common(const Bot& b, int role, float long_term) {
    using A = nn_teacher_access; const auto& w = A::world(b); const auto p = A::pos(b);
    int allies = 0, enemies = 0;
    for (const auto& a : w.allies) allies += cheb(a.pos, p) <= 6;
    for (const auto& e : w.enemies) enemies += cheb(e.pos, p) <= 6;
    return {static_cast<float>(A::round(b)), A::hp(b), A::max_hp(b), static_cast<float>(A::gems(b)),
            static_cast<float>(A::gold(b)), static_cast<float>(A::ally_score(b) - A::enemy_score(b)),
            static_cast<float>(A::slot(b)), static_cast<float>(A::team_size(b)), A::melee(b) ? 1.0f : 0.0f,
            static_cast<float>(allies), static_cast<float>(enemies), static_cast<float>(role), long_term};
}
float long_term(const Bot& b) {
    if constexpr (nncfg::mode(nncfg::H::value) != nncfg::Mode::off) {
        // The runtime caches all outputs on the first call. Each term is bounded before use as a ranking signal.
        const float win = nnh::value(b, nncfg::H::value, 0);
        const float margin = nnh::value(b, nncfg::H::value, 1);
        const float risk = nnh::value(b, nncfg::H::value, 2);
        return nns::bounded_value_signal(win, margin, risk);
    }
    return 0;
}
} // namespace

struct nn_strategy_access {
    static int teacher_role(const Bot& b) {
        if (b.heading_home || b.force_tribute || b.gems >= tune::kTributeCarry) return nns::carrier;
        if (!b.w.enemies.empty()) return nns::fighter;
        if (b.duo_ignore_slot >= 0 || std::string_view(b.mode) == "escort" || std::string_view(b.mode) == "regroup") return nns::escort;
        return nns::farmer;
    }
    static bool regroup(Bot& b) {
        const AllyRec* best = nullptr; int dist = 1000;
        for (const auto& a : b.w.allies) {
            const int d = cheb(a.pos, b.pos);
            if (a.id != b.my_id && a.hp > 0 && d > 2 && d < dist) best = &a, dist = d;
        }
        if (!best) return false;
        bc::bitboard goal; goal.clear(); goal.draw_chebyshev(best->pos, 2.0f);
        if (!b.walk_toward(goal)) return false;
        b.mode = "nn-regroup"; return true;
    }
    static bool execute(Bot& b, int option) {
        switch (option) {
        case nns::farm_first:
            if (!b.farm()) return false;
            b.opportunistic_attack(); b.support_casts(); return true;
        case nns::bank_first:
            if (!b.tribute_if_needed()) return false;
            b.mode = "nn-bank"; return true;
        case nns::home_first: {
            const bool old = b.heading_home; b.heading_home = true;
            if (b.go_home_if_needed()) { if (std::string_view(b.mode) == "idle") b.mode = "nn-home"; return true; }
            b.heading_home = old; return false;
        }
        case nns::hunt_first: return b.hunt();
        case nns::regroup_first: return regroup(b);
        default: return false;
        }
    }
    static bool valid_group(const Bot& b, int gi) {
        return gi >= 0 && gi < static_cast<int>(b.w.groups.size()) &&
               (static_cast<std::size_t>(gi) >= b.avoid_until.size() || b.avoid_until[static_cast<std::size_t>(gi)] <= b.round);
    }
    static float claims(const Bot& b, int gi) {
        int n = 0;
        for (int s = 0; s < std::min(b.team_size, kClaimSlots); ++s) n += s != b.slot && b.claim_of(s) == gi;
        return static_cast<float>(n);
    }
};

namespace nns {
void reset_role() { g_role.valid = false; g_signal_round = -1000; }
int current_role(const Bot& b) {
    const int teacher = nn_strategy_access::teacher_role(b);
    if constexpr (nncfg::mode(nncfg::H::role) == nncfg::Mode::off) return teacher;
    const int round = nn_teacher_access::round(b);
    if (g_role.valid && round >= g_role.round && round - g_role.round < 20) return g_role.id;
    // A rejected admission leaves no committed sampled option, so the next opportunity can retry.
    if (!nnh::admit(b, nncfg::H::role, 5, 2500)) return teacher;
    static nnh::Decision d;
    const auto state = common(b, teacher, 0);
    build_role(state, teacher, nn_teacher_access::target_group(b) >= 0, d);
    const auto r = nnh::decide(b, d);
    if (r.reason == nnh::kOk || r.reason == nnh::kShadow) {
        g_role = {round, static_cast<int>(d.id[r.choice]), true};
        return g_role.id;
    }
    return teacher;
}
int objective(const Bot& b, int teacher, int& need, float& score) {
    if constexpr (nncfg::mode(nncfg::H::objective) == nncfg::Mode::off) return teacher;
    const auto* o = nn_teacher_access::objective(b);
    if (!o || o->teacher != teacher || teacher < 0 || o->n <= 0 || o->cand[0].gi != teacher) return teacher;
    const int K = o->n < 8 ? o->n : 8;
    // Bounded candidates were narrowed by the teacher before any neural observation/features.
    if (!nnh::admit(b, nncfg::H::objective, K, 1800 + static_cast<unsigned>(K) * 600)) return teacher;
    const int role = g_role.valid ? g_role.id : nn_strategy_access::teacher_role(b);
    // Do not nest another neural admission inside the admitted builder: it would replace the runtime's token.
    const auto c = common(b, role, g_signal_round == nn_teacher_access::round(b) ? g_signal : 0);
    ObjectiveCandidate rows[8]; const auto& w = nn_teacher_access::world(b);
    for (int k = 0; k < K; ++k) {
        const auto& a = o->cand[k]; const bool valid = nn_strategy_access::valid_group(b, a.gi);
        auto& q = rows[k]; q = {a.gi, a.need, a.value, a.cost, a.score, static_cast<float>(a.finish), 0, 0, 0, 0, 0, 0, valid};
        if (!valid && k != 0) continue;
        if (a.gi < 0 || a.gi >= static_cast<int>(w.groups.size())) return teacher;
        const auto& g = w.groups[static_cast<std::size_t>(a.gi)];
        q.gems = static_cast<float>(g.gems); q.gold = static_cast<float>(g.gold); q.strength = g.strength;
        q.wait = g.state == GroupState::respawning ? static_cast<float>(std::max(0, g.respawn_round - nn_teacher_access::round(b))) : 0;
        q.distance = w.has_field(a.gi) ? static_cast<float>(w.group_distance(a.gi, nn_teacher_access::pos(b))) : -1.0f;
        q.claimed = nn_strategy_access::claims(b, a.gi);
    }
    static nnh::Decision d; build_objective(c, rows, K, d);
    const auto r = nnh::decide(b, d);
    if (r.choice <= 0 || r.choice >= K || !rows[r.choice].legal) return teacher;
    need = rows[r.choice].need; score = rows[r.choice].score; return rows[r.choice].id;
}
int draft_pick(const Bot& b, int teacher, const float* map, unsigned taken, unsigned our_picks, unsigned their_picks,
               float progress, bool first) {
    if constexpr (nncfg::mode(nncfg::H::draft_pick) == nncfg::Mode::off) return teacher;
    if (teacher < 0 || teacher >= 12 || (taken & (1u << teacher))) return teacher;
    // Number free is an inexpensive deterministic mask reduction, no candidate features yet.
    int K = 0; for (int i = 0; i < 12; ++i) K += (taken & (1u << i)) == 0;
    if (!nnh::admit(b, nncfg::H::draft_pick, K, 3000)) return teacher;
    DraftInput input{}; input.taken = taken;
    // The SDK champion_draft enum identifies these melee-bearing picks (Cassi+Issac contributes one melee body).
    constexpr unsigned melee_mask = (1u << 0) | (1u << 2) | (1u << 3) | (1u << 6) | (1u << 8) | (1u << 9) | (1u << 11);
    for (int c = 0; c < 12; ++c) {
        input.our_melee += ((our_picks & melee_mask) >> c) & 1u;
        input.their_melee += ((their_picks & melee_mask) >> c) & 1u;
    }
    input.progress = progress; input.first = first ? 1.0f : 0.0f;
    const auto& capture = nn_teacher_access::draft();
    for (int i = 0; i < 6; ++i) input.map[i] = map ? map[i] : 0;
    for (int i = 0; i < 12; ++i) input.score[i] = capture.z[i];
    static nnh::Decision d; build_draft(input, teacher, d);
    const auto r = nnh::decide(b, d); const int chosen = static_cast<int>(d.id[r.choice]);
    return chosen >= 0 && chosen < 12 && !(taken & (1u << chosen)) ? chosen : teacher;
}
bool act(Bot& b) {
    // Called only after combat, win-bank, and emergency go-home have had their normal teacher opportunity.
    // Role options persist exactly 20 rounds; no repeated forced decision records are emitted.
    const int role = current_role(b);
    float signal = 0;
    if constexpr (nncfg::mode(nncfg::H::value) != nncfg::Mode::off) signal = long_term(b);
    g_signal = signal; g_signal_round = nn_teacher_access::round(b);
    if constexpr (nncfg::mode(nncfg::H::strategy) != nncfg::Mode::off) {
        if (!nnh::admit(b, nncfg::H::strategy, 6, 2500)) return false;
        const auto& w = nn_teacher_access::world(b);
        const bool legal[6] = {true, !w.groups.empty(), nn_teacher_access::gems(b) > 0 && !w.no_bank,
                              !w.spawn_tiles.empty(), !w.sightings.empty() || !w.enemies.empty(), !w.allies.empty()};
        static nnh::Decision d; build_strategy(common(b, role, signal), legal, d);
        const auto r = nnh::decide(b, d);
        return nn_strategy_access::execute(b, static_cast<int>(d.id[r.choice]));
    }
    // A role-only ablation remains meaningful without turning on a policy head.
    if constexpr (nncfg::mode(nncfg::H::role) == nncfg::Mode::active) {
        const int implied = nn_strategy_access::teacher_role(b);
        if (role != implied) {
            const int priority = role == carrier ? bank_first : role == escort ? regroup_first :
                                 (role == fighter || role == scout) ? hunt_first : farm_first;
            return nn_strategy_access::execute(b, priority);
        }
    }
    return false;
}
} // namespace nns
#endif
