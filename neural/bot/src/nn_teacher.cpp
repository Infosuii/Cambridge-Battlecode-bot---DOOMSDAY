// Teacher interface (Agent A), out-of-line parts: names and invariant checks. Nothing here runs unless a head, a test or
// the dev self-test calls it; with every head off nothing references these functions and wasm-ld drops them (verified
// by the Wasm code-section hash, agents/A/REPORT.md). No globals, so no dynamic initialisers.
#include "nn_teacher.h"

namespace nnt {

const char* chain_name(Chain c) {
    switch (c) {
    case Chain::none: return "none";
    case Chain::dead: return "dead";
    case Chain::enemy: return "enemy";
    case Chain::tribute_win: return "tribute_win";
    case Chain::home: return "home";
    case Chain::hunt: return "hunt";
    case Chain::tribute: return "tribute";
    case Chain::farm: return "farm";
    case Chain::nofarm: return "nofarm";
    }
    return "?";
}

} // namespace nnt

// 0 ok; 1 no capture this turn; 2 n out of range; 3 candidate 0 is not the teacher's group; 4 duplicate group;
// 5 a group index outside World::groups; 6 need < 1.
int nn_teacher_access::check_objective(const Bot& b) {
    const nnt::Objective* o = objective(b);
    if (!o) return 1;
    if (o->teacher < 0) return o->n == 0 ? 0 : 2;
    if (o->n < 1 || o->n > nnt::kMaxGroups) return 2;
    if (o->cand[0].gi != o->teacher || o->cand[0].need != o->teacher_need) return 3;
    const auto ng = static_cast<int>(b.w.groups.size());
    for (int i = 0; i < o->n; ++i) {
        if (o->cand[i].gi < 0 || o->cand[i].gi >= ng) return 5;
        if (o->cand[i].need < 1) return 6;
        for (int j = 0; j < i; ++j)
            if (o->cand[j].gi == o->cand[i].gi) return 4;
    }
    return 0;
}

// 0 ok; 1 no pick yet; 2 the pick is not a legal (free) champion; 3 a free champion scores above the pick (the
// teacher takes the first maximum, so a strictly higher score elsewhere means a broken capture).
int nn_teacher_access::check_draft() {
    const nnt::Draft& d = nnt::g_draft;
    if (d.teacher < 0) return 1;
    if (d.teacher >= nnt::kMaxDraft || !d.legal[d.teacher]) return 2;
    for (int c = 0; c < nnt::kMaxDraft; ++c)
        if (d.legal[c] && d.z[c] > d.z[d.teacher]) return 3;
    return 0;
}
