#pragma once
#include <algorithm>
namespace dz {
// All terms are GE. Damage is fractional progress towards a kill; movement
// earns productive rounds, threat risks the carried bag and respawn tempo.
struct ActionValue {
    float damage=0,target_hp=1,kill_value=0,objective_gain=0;
    float rounds_saved=0,income=.45f,incoming=0,hp=1,death_cost=35;
    bool kills=false;
};
inline float action_value(const ActionValue& a) {
    return (a.kills?a.kill_value:.1f*a.kill_value*std::min(1.f,a.damage/std::max(1.f,a.target_hp)))+
        a.objective_gain+a.rounds_saved*a.income-
        std::min(1.f,a.incoming/std::max(1.f,a.hp))*a.death_cost;
}
}
