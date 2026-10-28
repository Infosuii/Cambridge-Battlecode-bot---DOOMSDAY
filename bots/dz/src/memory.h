#pragma once
#include "observation.h"

namespace dz {
struct Memory {
    std::vector<GroupBelief> groups;
    std::vector<std::vector<float>> member_hp;
    Contract contract;
    std::size_t cursor = 0;
    bool initialized = false;
    void init(const StaticWorld&);
    void observe_group(const StaticWorld&, int index, const TurnContext&);
    void update(const StaticWorld&, const TurnContext&);
    void release(int round);
};
}
