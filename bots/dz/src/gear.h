#pragma once
#include "observation.h"
namespace dz {
bool fixed_shop(const TurnContext&, Actuator&);
#if DZ_ECONOMY_V2
struct ShopVisit {
    cambc::item_type item;
    unsigned purchases=0,shards=0,emblems=0;
    int cost=0,round=0;
    float value=0;
    bool valid=false;
};
ShopVisit shop_visit(const TurnContext&,const Observation&,int horizon);
void commit_shop_visit(const ShopVisit&);
bool planned_shop(const TurnContext&,Actuator&,const StaticWorld*);
#endif
#if DZ_HAS(GEAR_PROSPECT)
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
#elif DZ_HAS(GEAR_PROSPECT)
    return map_shop(tc,act,world);
#else
    (void)world;return fixed_shop(tc,act);
#endif
}
}
