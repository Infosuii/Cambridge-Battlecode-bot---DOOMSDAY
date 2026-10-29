#pragma once
#include "clear_risk.h"
#include "fight.h"
#include "profile.h"
#include "memory.h"

namespace dz {
enum class GoalKind { Farm, Bank, Home, Retreat, Idle, YieldSpawn, Fight };
struct Goal { GoalKind kind = GoalKind::Idle; int index = -1; std::optional<vec2> destination; };
// Allied strength visible within radius of a tile (allies' own Monster bonus ignored).
float crew_strength(const Observation&, vec2 around, int radius);
// Solo/crew clear risk from remembered member HP; extra = allied damage per attack.
ClearRisk group_clear_risk(const StaticWorld&, const Memory&, const Observation&, int group, float extra = 0);
float danger(vec2 p, const Observation&);
float enemy_danger(vec2 p, const Observation&);
bool channel_safe(const StaticWorld&,const Observation&,const TurnContext&);
inline unsigned execute_entries = 0; // Trace-only counter.
void execute(Goal, StaticWorld&, Memory&, Observation&, const TurnContext&, Actuator&);
}
