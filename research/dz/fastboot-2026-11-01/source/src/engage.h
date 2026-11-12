#pragma once
#include "actions.h"
#if DZ_ECONOMY_V2
namespace dz { std::optional<Goal> engagement_goal(const StaticWorld&,Memory&,const Observation&,const TurnContext&); }
#endif
