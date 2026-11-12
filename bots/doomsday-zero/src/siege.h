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
const gate::Plan* opening_project(const Memory&,const Observation&,int group,const TurnContext&);
std::optional<Goal> begin_opening(StaticWorld&,Memory&,const Observation&,const TurnContext&,int altar);
std::optional<Goal> yield_siege_lane(StaticWorld&,Memory&,const Observation&,const TurnContext&);
std::optional<Goal> neutral_recovery(StaticWorld&,Memory&,const Observation&,const TurnContext&);
int bank_duration(int bag);
const Memory::BankAccess* bank_access(StaticWorld&,Memory&,const Observation&,unsigned altar,const TurnContext&,bool future=false);
const Memory::BankAccess* opening_bank(const Memory&,const gate::Plan&);
enum class BankAdmission { Allowed, Denied, Deferred };
BankAdmission bank_admission(const StaticWorld&,Memory&,const Observation&,unsigned altar,const TurnContext&);
bool build_bank_field(StaticWorld&,Memory&,const Observation&,const TurnContext&);
#endif
}
#endif
