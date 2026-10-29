#pragma once
#include "actions.h"
namespace dz {
#if DZ_TRACE
struct RecoverySample {
    std::uint32_t round=0;
    std::uint64_t entry=0,remaining=0;
    bool valid=false,moved=false,cleared=false;
    int before=-1,after=-1;
};
inline RecoverySample recovery_sample;
#endif
void quick_home(const StaticWorld&,const TurnContext&,Actuator&);
Goal safe_goal(StaticWorld&, Memory&, const Observation&, const TurnContext&);
}
