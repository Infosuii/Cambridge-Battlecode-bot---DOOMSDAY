#pragma once
#include "observation.h"
namespace dz {
bool fixed_shop(const TurnContext&, Actuator&,const StaticWorld* = nullptr);
#if DZ_ECONOMY_V2
struct ShopVisit {
    cambc::item_type item;
    unsigned purchases=0,shards=0,emblems=0;
    int cost=0,round=0;
    float value=0;
    bool valid=false;
    int horizon=0;
    unsigned searched=0;
};
ShopVisit shop_visit(const TurnContext&,const Observation&,int horizon,float income,float gold_income);
void commit_shop_visit(const ShopVisit&);
bool shop_visit_pending(unsigned round);
bool planned_shop(const TurnContext&,Actuator&,const StaticWorld*);
#endif
#if DZ_HAS(GEAR_PROSPECT)
bool map_shop(const TurnContext&,Actuator&,const StaticWorld*);
#endif
#if DZ_JOB_GEAR
bool job_shop(const TurnContext&,Actuator&,const StaticWorld*);
#endif
inline bool shop(const TurnContext& tc,Actuator& act,const StaticWorld* world) {
#if DZ_ECONOMY_V2 && !DZ_LIFECYCLE
    return planned_shop(tc,act,world);
#elif DZ_JOB_GEAR
    return job_shop(tc,act,world);
#elif DZ_HAS(GEAR_PROSPECT)
    return map_shop(tc,act,world);
#else
    return fixed_shop(tc,act,world);
#endif
}
}
