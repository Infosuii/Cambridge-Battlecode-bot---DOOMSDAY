#pragma once
#include "actions.h"
#if DZ_ECONOMY_V2
#include "objective_model.h"
namespace dz {
objective::Actor economic_growth(const SeenChampion&);
objective::Actor economic_actor(const SeenChampion&);
std::optional<Goal> economic_goal(StaticWorld&,Memory&,const Observation&,const TurnContext&,int altar,int altar_distance);
bool crew_ready(const StaticWorld&,Memory&,const Observation&,int group,const TurnContext&);
}
#endif
