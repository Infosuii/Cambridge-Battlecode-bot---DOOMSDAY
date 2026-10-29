#pragma once
#include "observation.h"
#include "clear_risk.h"

namespace dz {
struct Memory {
    std::vector<GroupBelief> groups;
    std::vector<std::vector<float>> member_hp;
    Contract contract;
    int field_needed=-1; // Deferred cold goal field, built before next planner work.
    std::size_t cursor = 0;
    // Memoized clear risk per group and per damage key. Member HP and own
    // damage rarely change between turns; recomputing every group each turn
    // cost 50-68k fuel. Keyed by remembered HP sum and both multipliers.
    std::vector<unsigned> hp_version; // Bumped only when remembered member HP changes.
    struct RiskEntry { unsigned version=~0u; float damage=-1, factor=-1; ClearRisk risk; };
    mutable std::vector<std::array<RiskEntry,2>> risk_cache;
    mutable float quantize_raw=-1, quantize_out=0; // Last damage quantization (libm is costly).
    int idle_until = 0;
    // Starvation fallback: no team income for a while reverts this champion
    // to the plain nearest-group policy (no feasibility/crew gates) for a spell.
    int last_income = 0, last_bag = 0, last_submitted = 0, legacy_until = 0;
    bool legacy(int round) const { return round < legacy_until; } // An idle champion re-plans every few rounds, not every turn.
    bool initialized = false;
    void init(const StaticWorld&);
    void observe_group(const StaticWorld&, int index, const TurnContext&);
    void update(const StaticWorld&, const TurnContext&);
    void release(int round);
};
}
