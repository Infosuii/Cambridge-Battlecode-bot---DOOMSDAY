// Direct-policy option state accessors. Root gameplay wrapper owns storage and implements these functions.
#pragma once
#include "nn_policy_config.h"
#if NN_POLICY_V2
#include <cambc.h>
namespace nnp {
int observation_role(); // current policy role0..4; initial farmer0, reset/commit rules owned by wrapper
cambc::vec2 observation_goal(); // current committed goal in WORLD tiles; {-1,-1} means absent -> self
}
#endif
