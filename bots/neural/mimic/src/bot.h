// Mimic runtime: reads the game through the SDK into the core's observation, asks the fitted models (weights.h)
// for each decision and carries them out with legal actions.
#pragma once
#include <cambc.h>

#include <cstdint>
#include <vector>

#include "core.h"

class Mimic {
public:
    void turn();

private:
    struct Slot {
        int kind = 0;           // bc::ability_kind value, 0 none
        float range = 0, radius = 0;
        bool exclusive = false; // excludes walking this turn
    };

    void init();
    void build_fields(std::uint64_t reserve);
    void observe_game();
    void shop();
    mc::Objective choose_objective();
    void act(mc::Objective ob);
    bool attack(const mc::TargetCand& t);
    bool move(mc::Objective ob);
    void cast_phase(mc::Objective ob);
    void after_attack(mc::Objective ob, const mc::TargetCand& t);
    void maybe_tribute();
    void finish(bool alive);
    const mc::UnitObs* enemy(int id) const;
    static cambc::champion champion(int id); // a champion handle by id (no listing)
    float noise(int salt) const;

    bool ready_ = false;
    mc::Map map_;
    mc::Memory mem_;
    mc::Obs obs_;
    std::uint32_t shared_read_[2] = {}; // the actual shared bytes used by this observation (parity diagnostics)
    std::uint32_t me_ = 0;
    int team_row_ = 0; // weights row: 0 pooled, 1 + team index
    std::vector<std::uint32_t> group_handles_, camp_handles_;
    std::vector<cambc::camp> camps_;                  // by core camp index
    cambc::bitboard camp_tiles_;                       // every camp spawn tile
    std::vector<std::vector<std::uint16_t>> fields_;  // groups, then altar, then home
    std::vector<int> field_order_;
    std::size_t fields_built_ = 0;
    std::uint64_t field_cost_ = 30000; // dearest field build so far (fuel)
    std::vector<int> ally_ids_; // ascending: shared-memory slot = index
    int my_slot_ = -1;
    Slot slots_[2];
    int dash_slot_ = -1;
    bool perma_ = false, trick_pending_ = false;
    mc::Objective prev_obj_{};
    bool have_prev_ = false;
    int decided_round_ = -100;       // round the objective was last chosen
    std::int8_t decided_state_ = 0; // the farm objective's group state then
    bool attacked_ = false, moved_ = false, excl_cast_ = false, cast_done_ = false;
    int pending_reset_ = -1; // attack reset slot held for after the basic attack
    int x_ = 0, y_ = 0; // my tile, updated as I move this turn
};
