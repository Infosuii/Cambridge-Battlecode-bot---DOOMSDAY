#pragma once
#include "actions.h"
#if DZ_SIEGE || DZ_ECONOMY_V2
#include "access_route.h"
namespace dz {
access::Route altar_route(const StaticWorld&,const Memory&,const Observation&,unsigned altar,const TurnContext&);
std::optional<bool> altar_access(StaticWorld&,Memory&,const Observation&,unsigned altar,const TurnContext&);
std::optional<Goal> siege_goal(StaticWorld&,Memory&,const Observation&,const TurnContext&,bool altar_open);
bool siege_strike_allowed(const Memory&,const Observation&,int group,const TurnContext&);
}
#endif
