#pragma once
// Agent 2: per-official-map switch profile (A2_MAP_PROFILE bit mask; the ladder plays only the 17 official maps).
// Pool evidence (EXPERIMENTS E34): the fuel package's fast bush labelling lets bush hiding run where v34 ran out of fuel
// (stampede 67.8% -> 49.1%, ambush 63.4% -> 55.0%), and the 4-unit fight snapshot loses collision (70% -> 61%).
//   bit 0: stampede uses v34's bush labelling     bit 1: ambush uses v34's bush labelling
//   bit 2: collision uses the full 8-unit snapshot
//   bit 3: expanse uses the camp-clearing item build (pool: 53.6% -> 88.4% there; a farming race)
#include "common.h"

namespace a2map {
inline int id = -1; // nova_map_id order: ambush 0, collision 1, ..., stampede 15; -1 = unseen map / not set
inline bool slow_bush() { return ((A2_MAP_PROFILE & 1) && id == 15) || ((A2_MAP_PROFILE & 2) && id == 0); }
inline int snap_cap(int cap) { return (A2_MAP_PROFILE & 4) && id == 1 ? 8 : cap; }
inline bool farm_build() { return (A2_MAP_PROFILE & 8) && id == 6; }
} // namespace a2map
