#pragma once
#include "actions.h"

namespace dz {
#if DZ_ECONOMY_V2 && DZ_LIFECYCLE
// Singletons only. Crew/siege contracts remain with their original owners.
bool lifecycle_owns(const Memory&);
Goal lifecycle_goal(StaticWorld&,Memory&,const Observation&,const TurnContext&);
#endif
}
