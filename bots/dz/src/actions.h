#pragma once
#include "memory.h"

namespace dz {
enum class GoalKind { Farm, Bank, Home, Retreat, Idle, YieldSpawn };
struct Goal { GoalKind kind = GoalKind::Idle; int index = -1; std::optional<vec2> destination; };
float danger(vec2 p, const Observation&);
float enemy_danger(vec2 p, const Observation&);
bool channel_safe(const StaticWorld&,const Observation&,const TurnContext&);
void execute(Goal, StaticWorld&, Memory&, const Observation&, const TurnContext&, Actuator&);
}
