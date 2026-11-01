#pragma once
#include "actions.h"
#if DZ_ECONOMY_V2
#include "formation.h"
namespace dz {
crew::Unit crew_unit(const SeenChampion&,unsigned slot);
enum class CrewQuoteStatus { Ready, Budget, Unsupported, Formation, Model, Escape, Exhausted, Horizon };
struct CrewQuote { bool complete=false;unsigned members=0;int finish=0;CrewQuoteStatus status=CrewQuoteStatus::Budget;int arrival=0,home=0;bool isolated=false; };
CrewQuote crew_quote(const StaticWorld&,const Memory&,int group,std::span<const crew::Unit>,int capture,const TurnContext&,bool investments=true);
Goal crew_action(Goal,StaticWorld&,Memory&,const Observation&,const TurnContext&);
bool build_crew_field(StaticWorld&,Memory&,const Observation&,const TurnContext&);
void progress_crew_layout(const StaticWorld&,const Memory&,const TurnContext&);
void prepare_crew_reward(const StaticWorld&,Memory&,const Observation&,int group,const TurnContext&);
}
#endif
