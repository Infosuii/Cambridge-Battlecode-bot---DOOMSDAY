// Tactical candidate schema/builders (E). Pure bounded data; no engine includes or allocations.
#pragma once
#include "nn_head.h"
#include <cmath>
#include <cstdint>

class Bot;
struct EnemyRec;
namespace ts { struct State; }

namespace nne {
inline constexpr int kF = 24, kLeafF = 8;
inline constexpr float kTeacherMargin = 0.05f;
// raw[] names/scales are specified by schemas/heads/{move,combat,engage,ward}.json.
// Input order is teacher first. The builder preserves legality, IDs and all ordering; it never invents legality.
struct Option { std::uint32_t id = 0; std::uint8_t legal = 1; float raw[kF]{}; };
struct Tile { int x = 0, y = 0; float score = 0; };
struct CastPick { int slot = -1; bool dash = false; };

inline constexpr float kMoveScale[kF] = {8,8,1024,64,64,64,8,8,500,1,50,1,1,1,1,8,1,1,2000,64,64,1,1,1};
inline constexpr float kCombatScale[kF] = {1,2,8,500,1,50,500,500,8,8,8,8,1,1,1,1,1,1,1,1,2000,1,1,1};
inline constexpr float kEngageScale[kF] = {1,1,1,1000,1000,100,20,20,1,50,8,8,500,500,1,1,1,2000,1,1,1,1,1,1};
inline constexpr float kWardScale[kF] = {8,8,64,8,8,1,1,1,1,1,50,1,2000,1,1,1,1,1,1,1,1,1,1,1};
inline constexpr float kLeafScale[kLeafF] = {1000,1000,4,4,1,64,50,1};

// Same octants as nfs.transforms.sector_of, for bounded integer tile displacements (radius16).
constexpr int belief_sector(int dx, int dy) {
    const int ax=dx<0?-dx:dx, ay=dy<0?-dy:dy;
    if (ax>16 || ay>16) return 8;
    if (dx==0 && dy==0) return 0;
    if (ax*1000000 < ay*414214) return dy>=0 ? 0 : 4;
    if (ay*1000000 < ax*414214) return dx>=0 ? 2 : 6;
    return dx>=0 ? (dy>=0 ? 1 : 3) : (dy>=0 ? 7 : 5);
}
inline float bounded_belief(float logit) {
    if (!std::isfinite(logit)) return 0.0f;
    return logit/(1.0f+std::fabs(logit));
}

inline float normalise(float x, float scale) {
    if (!std::isfinite(x)) return x; // runtime rejects non-finite input; do not silently hide an invalid feature
    x /= scale;
    return x < -1.0f ? -1.0f : x > 1.0f ? 1.0f : x;
}
inline void build(nncfg::H head, const Option* options, int n, std::uint8_t context,
                  const float* scales, nnh::Decision& d) {
    d.head = head; d.F = kF; d.K = n < 0 ? 0 : n > nnh::kMaxK ? nnh::kMaxK : n; d.context = context;
    for (int k = 0; k < d.K; ++k) {
        d.id[k] = options[k].id; d.legal[k] = options[k].legal;
        d.prior[k] = k == 0 ? 0.0f : -kTeacherMargin;
        for (int f = 0; f < kF; ++f) d.feat[k * kF + f] = normalise(options[k].raw[f], scales[f]);
    }
}
inline void build_move(const Option* a, int n, std::uint8_t c, nnh::Decision& d) { build(nncfg::H::move,a,n,c,kMoveScale,d); }
inline void build_combat(const Option* a, int n, std::uint8_t c, nnh::Decision& d) { build(nncfg::H::combat,a,n,c,kCombatScale,d); }
inline void build_engage(const Option* a, int n, std::uint8_t c, nnh::Decision& d) { build(nncfg::H::engage,a,n,c,kEngageScale,d); }
inline void build_ward(const Option* a, int n, std::uint8_t c, nnh::Decision& d) { build(nncfg::H::ward,a,n,c,kWardScale,d); }
inline void build_leaf(const float* raw, float* feat) {
    for (int f = 0; f < kLeafF; ++f) feat[f] = normalise(raw[f], kLeafScale[f]);
}

// All wrappers gate before feature work; selected actions still use the original execution paths.
// Movement contexts: 0 travel/waypoint, 1 combat/chase, 2 retreat/escape, 3 spacing/position.
int move_rank(const Bot& bot, const Tile* narrowed, int n, std::uint8_t context);
Tile local_move(const Bot& bot, Tile teacher, std::uint8_t context);
const EnemyRec* combat_target(const Bot& bot, const EnemyRec* teacher);
CastPick combat_cast(const Bot& bot, const EnemyRec& target, int teacher_slot, int dash_slot, int aim_x, int aim_y);
int engage(const Bot& bot, int teacher, float fight, float run, float margin, float ttd, bool has_target);
// Ward rank returns -1 for no-ward, otherwise an index in narrowed; teacher is index0.
int ward_rank(const Bot& bot, const Tile* narrowed, int n, std::uint8_t context);
float leaf(const Bot& bot, const ts::State& start, const ts::State& end, int home_x, int home_y, int plan);
} // namespace nne
