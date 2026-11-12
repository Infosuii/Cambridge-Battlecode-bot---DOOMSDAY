// Wave 2 D: pure, bounded candidate builders and SDK glue declarations.
// Untrained heads remain off in release. Candidate 0 always denotes the computed teacher choice.
#pragma once
#include "nn_head.h"
#include "nn_rt.h"

class Bot;
namespace nns {
inline constexpr int kF = 24;
enum Role : int { farmer = 0, carrier = 1, fighter = 2, escort = 3, scout = 4 };
enum Priority : int { teacher_chain = 0, farm_first = 1, bank_first = 2, home_first = 3, hunt_first = 4, regroup_first = 5 };
struct Common {
    float round, hp, max_hp, gems, gold, margin, slot, team_size, melee, near_allies, near_enemies, role, long_term;
};
struct ObjectiveCandidate {
    int id, need;
    float value, cost, score, finish, gems, gold, wait, distance, strength, claimed;
    bool legal;
};
struct DraftInput {
    float map[6]; // original teacher's public, normalised map feature prefix
    float score[12];
    unsigned taken; // bit c means already selected by either team
    float our_melee, their_melee, progress, first;
};
inline float clip(float x, float lo = -4.0f, float hi = 4.0f) { return x < lo ? lo : x > hi ? hi : x; }
inline float bounded_value_signal(float win_logit, float margin, float carry_risk) {
    // value.margin is already normalized: final submitted gem margin / 1000 (fixed model output unit).
    return clip(0.5f * nnrt::act(carry_risk) - 0.25f * nnrt::act(win_logit) -
                0.25f * nnrt::act(margin), -1, 1);
}
inline void common_features(const Common& c, float* f) {
    f[0] = clip(c.round / 2000.0f); f[1] = clip(c.hp / (c.max_hp > 1.0f ? c.max_hp : 1.0f), 0, 1);
    f[2] = clip(c.gems / 100.0f); f[3] = clip(c.gold / 1000.0f); f[4] = clip(c.margin / 500.0f);
    f[5] = clip(c.slot / 6.0f); f[6] = clip(c.team_size / 6.0f); f[7] = c.melee;
    f[8] = clip(c.near_allies / 6.0f); f[9] = clip(c.near_enemies / 8.0f);
    f[10] = clip(c.role / 4.0f); f[11] = clip(c.long_term, -1, 1);
}
inline void begin(nnh::Decision& d, nncfg::H head, int K) { d.head = head; d.K = K; d.F = kF; d.context = 0; }
inline void build_strategy(const Common& c, const bool* legal, nnh::Decision& d) {
    begin(d, nncfg::H::strategy, 6);
    for (int k = 0; k < d.K; ++k) {
        float* f = d.feat + k * kF; common_features(c, f);
        for (int j = 0; j < 6; ++j) f[12 + j] = k == j ? 1.0f : 0.0f;
        for (int j = 0; j < 5; ++j) f[18 + j] = static_cast<int>(c.role) == j ? 1.0f : 0.0f;
        f[23] = k == 0 ? 1.0f : 0.0f;
        d.legal[k] = k == 0 || legal[k]; d.id[k] = static_cast<unsigned>(k);
        // All learned values are bounded and affect ranking only; never emergency checks or legality.
        const float risk_bias = k == bank_first ? 0.10f * clip(c.long_term, 0, 1) : 0;
        const int role = static_cast<int>(c.role);
        const bool role_fit = (k == farm_first && role == farmer) || (k == bank_first && role == carrier) ||
                             (k == hunt_first && (role == fighter || role == scout)) || (k == regroup_first && role == escort);
        d.prior[k] = k == 0 ? 0.0f : -0.25f + (role_fit ? 0.05f : 0.0f) + risk_bias;
    }
}
inline void build_role(const Common& c, int teacher, bool has_target, nnh::Decision& d) {
    begin(d, nncfg::H::role, 5);
    int ids[5], n = 1; ids[0] = teacher >= 0 && teacher < 5 ? teacher : farmer;
    for (int r = 0; r < 5; ++r) if (r != ids[0]) ids[n++] = r;
    for (int k = 0; k < 5; ++k) {
        float* f = d.feat + k * kF; common_features(c, f); const int r = ids[k];
        for (int j = 0; j < 5; ++j) f[12 + j] = r == j ? 1.0f : 0.0f;
        f[17] = has_target ? 1.0f : 0.0f;
        f[18] = r == carrier ? f[2] : 0; f[19] = r == fighter ? f[9] : 0;
        f[20] = r == escort ? f[8] : 0; f[21] = r == scout ? 1.0f - clip(f[9], 0, 1) : 0;
        f[22] = r == farmer ? 1.0f - clip(f[2], 0, 1) : 0; f[23] = k == 0 ? 1.0f : 0.0f;
        d.id[k] = static_cast<unsigned>(r); d.legal[k] = 1; d.prior[k] = k == 0 ? 0.0f : -0.25f;
    }
}
inline void build_objective(const Common& c, const ObjectiveCandidate* cand, int n, nnh::Decision& d) {
    begin(d, nncfg::H::objective, n < 0 ? 0 : n > 8 ? 8 : n);
    for (int k = 0; k < d.K; ++k) {
        const auto& a = cand[k]; float* f = d.feat + k * kF; common_features(c, f);
        f[12] = clip(a.value / 100.0f); f[13] = clip(a.cost / 100.0f); f[14] = clip(a.score / 5.0f);
        f[15] = clip(a.finish / 100.0f); f[16] = clip(static_cast<float>(a.need) / 6.0f);
        f[17] = clip(a.gems / 100.0f); f[18] = clip(a.gold / 1000.0f); f[19] = clip(a.wait / 200.0f);
        f[20] = clip(a.distance / 100.0f); f[21] = clip(a.strength / 100.0f); f[22] = clip(a.claimed / 6.0f);
        f[23] = k == 0 ? 1.0f : 0.0f; d.id[k] = static_cast<unsigned>(a.id); d.legal[k] = k == 0 || a.legal;
        const float difference = clip((a.score - cand[0].score) / 5.0f, -4, 0);
        d.prior[k] = k == 0 ? 0.0f : -0.25f + difference - 0.10f * clip(c.long_term, 0, 1) * clip(f[15], 0, 1);
    }
}
inline void build_draft(const DraftInput& a, int teacher, nnh::Decision& d) {
    begin(d, nncfg::H::draft_pick, 0);
    if (teacher < 0 || teacher >= 12 || (a.taken & (1u << teacher))) return;
    int ids[12], n = 1; ids[0] = teacher;
    for (int c = 0; c < 12; ++c) if (c != teacher && !(a.taken & (1u << c))) ids[n++] = c;
    d.K = n;
    for (int k = 0; k < n; ++k) {
        const int c = ids[k]; float* f = d.feat + k * kF;
        for (int j = 0; j < 12; ++j) f[j] = c == j ? 1.0f : 0.0f;
        f[12] = clip(a.score[c] / 10.0f);
        for (int j = 0; j < 6; ++j) f[13 + j] = clip(a.map[j]);
        f[19] = clip(a.our_melee / 6.0f); f[20] = clip(a.their_melee / 6.0f);
        f[21] = clip(a.progress, 0, 1); f[22] = a.first; f[23] = k == 0 ? 1.0f : 0.0f;
        d.legal[k] = 1; d.id[k] = static_cast<unsigned>(c);
        d.prior[k] = k == 0 ? 0.0f : -0.25f + clip((a.score[c] - a.score[teacher]) / 10.0f, -4, 0);
    }
}

// Runtime functions below compile only for NN_ANY_HEAD. The caller keeps a fully computed teacher fallback.
int objective(const Bot& bot, int teacher, int& need, float& score);
int draft_pick(const Bot& bot, int teacher, const float* map_features, unsigned taken,
               unsigned our_picks, unsigned their_picks, float progress, bool first);
// Insert after the existing emergency win-bank and go_home branches. True means an alternative acted;
// false executes the remaining teacher chain unchanged. No action is sampled twice during a role commitment.
bool act(Bot& bot);
int current_role(const Bot& bot);
void reset_role(); // dead-turn hook: the next alive opportunity starts a new option
} // namespace nns
