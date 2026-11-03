// Isolated I-70-02 prototype. Not included in any benchmark bot.
#pragma once
#ifndef X1_G70_COORD
#define X1_G70_COORD 0
#endif
#if X1_G70_COORD
namespace g70 {
struct ActionWindow {
    int verified_walk_steps = -1; // -1 means path arrival is unknown: give no support credit.
    bool melee = false;
    bool can_move_now = false;
    bool can_attack_now = false;
    bool completed_turn = false;
    bool channeling = false;
    bool future_actions_available = false; // Caller must establish this assumption explicitly.
};

// Count feasible basic attacks in at most two turns, assuming the target stays in the verified range plan.
// No spells, resets, dashes or unobserved paths are invented. Future target movement is a separate veto.
constexpr int basic_shots(ActionWindow unit, int horizon = 2) {
    if (unit.verified_walk_steps < 0 || unit.channeling || horizon <= 0) return 0;
    if (horizon > 2) horizon = 2;
    int shots = 0;
    for (int turn = 0; turn < horizon; ++turn) {
        if (turn == 0 && unit.completed_turn) continue;
        const bool move = turn == 0 ? unit.can_move_now : unit.future_actions_available;
        const bool attack = turn == 0 ? unit.can_attack_now : unit.future_actions_available;
        bool moved = false;
        if (unit.verified_walk_steps > 0) {
            if (!move) continue;
            --unit.verified_walk_steps;
            moved = true;
        }
        if (unit.verified_walk_steps == 0 && attack && (unit.melee || !moved)) ++shots;
    }
    return shots;
}
} // namespace g70
#endif
