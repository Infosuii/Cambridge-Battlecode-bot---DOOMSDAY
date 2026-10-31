#pragma once
#include "actions.h"
#if DZ_SIEGE || DZ_ECONOMY_V2
#include "access_route.h"
namespace dz {
access::Route altar_route(const StaticWorld&,const Memory&,const Observation&,unsigned altar,const TurnContext&);
std::optional<bool> altar_access(StaticWorld&,Memory&,const Observation&,unsigned altar,const TurnContext&);
std::optional<Goal> siege_goal(StaticWorld&,Memory&,const Observation&,const TurnContext&,bool altar_open);
bool siege_strike_allowed(const Memory&,const Observation&,int group,const TurnContext&);
#if DZ_ECONOMY_V2
void quote_opening(StaticWorld&,Memory&,const Observation&,const TurnContext&);
const gate::Plan* best_opening(const Memory&,const Observation&,const TurnContext&);
std::optional<Goal> begin_opening(StaticWorld&,Memory&,const Observation&,const TurnContext&,int altar);
std::optional<Goal> yield_siege_lane(StaticWorld&,Memory&,const Observation&,const TurnContext&);
#endif
}
#endif
