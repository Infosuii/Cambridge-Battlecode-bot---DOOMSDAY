#pragma once
#include "actions.h"
#if DZ_ECONOMY_V2
#include "formation.h"
namespace dz {
crew::Unit crew_unit(const SeenChampion&,unsigned slot);
struct CrewQuote { bool complete=false;unsigned members=0;int finish=0; };
CrewQuote crew_quote(const StaticWorld&,const Memory&,int group,std::span<const crew::Unit>,int capture,const TurnContext&);
Goal crew_action(Goal,StaticWorld&,Memory&,const Observation&,const TurnContext&);
bool build_crew_field(StaticWorld&,Memory&,const Observation&,const TurnContext&);
}
#endif
