// SDK option boundary. Builders run only after Core admission. No teacher ranking.
#pragma once
#include "nn_policy_config.h"
#if NN_POLICY_V2
#include "common.h"
#include "nn_policy_candidates.h"
class Bot;
namespace nnp {
struct OptionsState {
    int intent=0, role=0, objective=-1, altar=-1, engagement=-1;
    vec2 goal{-1,-1};
};
struct Execution {
    bool legal=false, executed=false, changed=false;
};
// Canonical transform is its own inverse; follows compact observation frame semantics.
vec2 canonical(const Bot&,vec2);
bool build_strategy(const Bot&,const OptionsState&,nnpc::Decision&);
bool build_objective(const Bot&,const OptionsState&,nnpc::Decision&);
bool build_role(const Bot&,const OptionsState&,nnpc::Decision&);
Execution execute_strategy(Bot&,OptionsState&,std::uint32_t);
Execution execute_objective(Bot&,OptionsState&,std::uint32_t);
Execution execute_role(Bot&,OptionsState&,std::uint32_t);
// Revalidate an existing assignment after a temporary teacher turn; never select a replacement goal.
bool resume_assignments(Bot&,const OptionsState&);
// Metadata/count-only pre-admission estimate. Bank fields cap64 expansions; unresolved options refuse the whole decision.
std::uint64_t bank_candidate_fuel(const Bot&);
bool build_bank(const Bot&,const OptionsState&,nnpc::Decision&);
bool build_shop(const Bot&,const OptionsState&,nnpc::Decision&);
Execution execute_bank(Bot&,OptionsState&,std::uint32_t);
Execution execute_shop(Bot&,OptionsState&,std::uint32_t);
bool build_move(const Bot&,const OptionsState&,nnpc::Decision&);
bool build_combat(const Bot&,const OptionsState&,nnpc::Decision&);
bool build_engage(const Bot&,const OptionsState&,nnpc::Decision&);
std::uint64_t tactics_candidate_bound(const Bot&,const OptionsState&,nncfg::H);
Execution execute_move(Bot&,OptionsState&,std::uint32_t);
Execution execute_combat(Bot&,OptionsState&,std::uint32_t);
Execution execute_engage(Bot&,OptionsState&,std::uint32_t);
}
#endif
