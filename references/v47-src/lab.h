// Engine-lab control block (A2_LAB builds only; agent2/lab/macro_lab.js). The host writes one intervention for one
// champion before a game; the bot applies it and records what it would have done. Shipped builds never include this.
#pragma once
#include <cstdint>

namespace lab {
struct Ctl {
    std::int32_t champ = -1; // champion handle the intervention applies to (-1 = none)
    std::int32_t round = 0;  // first round of the intervention
    std::int32_t kind = 0;   // 1 forbid camp target, 2 bank now, 3 hold bag, 4 force fight, 5 force run, 6 regroup, 7 home; -k: record only
    std::int32_t len = 0;    // rounds it lasts
    // Records (written by the bot at the first intervention turn; -2 = not yet).
    std::int32_t rec_target = -2, rec_after = -2, rec_gems = -2, rec_hp = -2, rec_dist = -2, rec_round = -2;
};
inline Ctl ctl;
// Joint-search knobs (agent2/lab/knob_es.js), written by the host before a game; 0 = the build's own setting.
// Neural fight/run policy (A2_POLICY, agent2/lab/ppo_lab.js): 24 features -> 32 tanh -> 3 logits (fight, run, keep the
// bot's own verdict).
// The host writes the weights and the mode (0 argmax, 1 sample) before a game and reads the decision log after it.
#if A2_POLICY >= 2
// Version 2 (paper-style per-unit view): self 10 + global 2 + 4 nearest enemies x 10 + 3 nearest allies x 4 = 64
// inputs -> 48 tanh -> verdict head (fight, run, keep) and target head (4 enemy slots, keep the bot's target).
inline constexpr int kPolIn = 64, kPolHid = 48, kPolOut = 3, kPolT = 5;
inline constexpr int kPolW = kPolIn * kPolHid + kPolHid + kPolHid * kPolOut + kPolOut + kPolHid * kPolT + kPolT;
inline constexpr int kPolEntry = kPolIn + 5; // features, verdict, target, log-probability (both heads), round, valid slots
#else
inline constexpr int kPolIn = 24, kPolHid = 32, kPolOut = 3, kPolW = kPolIn * kPolHid + kPolHid + kPolHid * kPolOut + kPolOut;
inline constexpr int kPolEntry = kPolIn + 3; // features, action, log-probability, round
#endif
inline float pol_w[kPolW] = {};
inline std::int32_t pol_cfg[4] = {0, 1, 0, kPolEntry}; // mode, rng seed, entries logged, entry size
inline constexpr int kPolLogMax = 600;
inline float pol_log[kPolLogMax * kPolEntry] = {};
// Macro what-ifs (agent2/lab/exit_lab.js): the controlled champion's situation at its first turn at or after ctl.round.
inline constexpr int kMacroF = 20;
inline float macro_feat[kMacroF + 1] = {}; // features, then the round they were taken (-1 = not yet)
inline bool macro_done = false;
// Item build table (agent2/lab/build_lab.js): per champion type (SDK champion_type, 16 slots) a step count, then up to
// 8 steps of (item id, total shards wanted); a type with steps replaces build_for's choice. Item id = family * 6 +
// stat * 2 (families monster, power, durability, treasure, jungle, home, bruiser; stats strength, focus, health).
inline constexpr int kBuildSlot = 17;
inline std::int32_t builds[16 * kBuildSlot] = {};
// 0-15 tuning knobs (bot.cpp), 16-21 targeting weights, 22-23 melee / ranged aggression, 24-31 fight/run verdict
// (tsearch.cpp ts_decide), 32 caster micro risk, 33-35 economy passives, 36-39 banking, cohesion and ward distances,
// 40 middle-camp weight, 41 team-fight engage ratio, 42 altar prelocking, 43-44 early aggression and hunt range.
inline constexpr int kKnobs = 48;
#ifdef A2_KNOBS
inline float knobs[kKnobs] = {A2_KNOBS}; // a search result baked into a build (comma-separated, missing = 0)
#else
inline float knobs[kKnobs] = {};
#endif
// The intervention starts at the first turn its condition holds (recorded in rec_round) and lasts len rounds.
inline bool active(std::int32_t me, std::int32_t round, std::int32_t kind) {
    return ctl.champ == me && ctl.kind == kind && ctl.rec_round >= 0 && round >= ctl.rec_round && round < ctl.rec_round + ctl.len;
}
} // namespace lab
