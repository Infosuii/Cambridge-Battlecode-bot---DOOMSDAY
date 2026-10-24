// TEST STUB (agent B) of agent C's nn_obs.h: a RawTurn that simply carries an encoded observation. The test (or the
// fuel probe) defines nnobs::capture; encode copies. Copied into scratch trees as nn_obs.h; never placed in bot/src.
#pragma once
#include <cstdint>
#include <cstring>

#include "nn_schema.h"

class Bot;

namespace nnobs {
struct RawTurn {
    float x[kObsDim];
};
bool capture(const Bot& bot, RawTurn& out);
inline void encode(const RawTurn& raw, float* x) { std::memcpy(x, raw.x, sizeof(raw.x)); }
} // namespace nnobs
