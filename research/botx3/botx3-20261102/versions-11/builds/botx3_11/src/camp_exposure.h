#pragma once
#include <algorithm>
#include <cstdlib>
namespace camp_exposure {
struct Camp {int x,y;float damage;int range;};
// Engine 2: maximum camp range 5, admitted within range+2 => 15x15 camp tiles.
constexpr int capacity=256;
inline float incoming(const Camp* camps,int count,int x,int y) {
    float damage=0;
    for (int i=0;i<count;++i)
        if (std::max(std::abs(camps[i].x-x),std::abs(camps[i].y-y))<=camps[i].range) damage+=camps[i].damage;
    return damage;
}
}
