#pragma once
#include "observation.h"
namespace dz {
bool fixed_shop(const TurnContext&, Actuator&);
#if DZ_ECONOMY_V2
bool planned_shop(const TurnContext&,Actuator&,const StaticWorld*);
#endif
#if DZ_GEAR_PROSPECT
bool map_shop(const TurnContext&,Actuator&,const StaticWorld*);
#endif
#if DZ_JOB_GEAR
bool job_shop(const TurnContext&,Actuator&,const StaticWorld*);
#endif
inline bool shop(const TurnContext& tc,Actuator& act,const StaticWorld* world) {
#if DZ_ECONOMY_V2
    return planned_shop(tc,act,world);
#elif DZ_JOB_GEAR
    return job_shop(tc,act,world);
#elif DZ_GEAR_PROSPECT
    return map_shop(tc,act,world);
#else
    (void)world;return fixed_shop(tc,act);
#endif
}
}
