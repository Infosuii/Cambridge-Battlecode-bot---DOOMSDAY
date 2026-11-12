#pragma once
#include "nn_policy_config.h"
#if NN_POLICY_V2
class Bot;
namespace nnp {
bool play_turn(Bot&);
void warmup();
void idle();
}
#endif
