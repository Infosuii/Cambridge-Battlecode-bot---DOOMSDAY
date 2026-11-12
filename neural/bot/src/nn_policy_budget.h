// GENERATED from models/policy_v2_budget.json. Direct-policy only.
#pragma once
#include "nn_policy_core.h"
namespace nnp {
inline constexpr Budget kPolicyBudget{
    .turn_allowance=90000u,
    .action_reserve=16000u,
    .tail_reserve=7000u,
    .observation=16000u,
    .candidate=3500u,
    .head_base=1800u,
    .per_candidate=300u,
    .log=6000u,
    .log_per_candidate=600u
};
}
