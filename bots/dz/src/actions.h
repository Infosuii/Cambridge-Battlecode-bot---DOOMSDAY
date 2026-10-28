#pragma once
#include "memory.h"

namespace dz {
enum class GoalKind { Farm, Bank, Home, Retreat, Idle };
struct Goal { GoalKind kind = GoalKind::Idle; int index = -1; };
float danger(vec2 p, const Observation&);
void execute(Goal, StaticWorld&, Memory&, const Observation&, const TurnContext&, Actuator&);
}
