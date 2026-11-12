#pragma once
#include <algorithm>
#include <cmath>
#include <span>

namespace dz {
struct Tile {
    int x=0,y=0;
    friend bool operator==(Tile,Tile)=default;
};
inline int cheb(Tile a,Tile b) { return std::max(std::abs(a.x-b.x),std::abs(a.y-b.y)); }
struct CampThreat { Tile p; float strength; int range; };
inline float camp_damage(Tile p, std::span<const CampThreat> camps) {
    float damage=0;
    for (auto c:camps) if (cheb(p,c.p)<=c.range) damage+=c.strength;
    return damage;
}
struct EscapeRoute { Tile exit; float damage=0; int steps=0; bool found=false, truncated=false; };
struct UnlimitedEscapeBudget { bool operator()() const { return true; } };
// Exact damage along each unobstructed straight walking route, under the
// conservative assumption that every observed camp can hit us every round.
// This is an escape-budget safeguard, not a calibrated objective/crew model.
template<class Walkable,class Budget=UnlimitedEscapeBudget>
EscapeRoute camp_escape(Tile origin,std::span<const CampThreat> camps,Walkable walkable,Budget can_spend={}) {
    EscapeRoute best;
    int max_range=0;
    for (auto c:camps) max_range=std::max(max_range,c.range);
    for (int dx=-1;dx<=1;++dx) for (int dy=-1;dy<=1;++dy) {
        if (!dx&&!dy) continue;
        float damage=0;
        for (int step=1;step<=max_range*2+2;++step) {
            if (!can_spend()) { best.truncated=true; return best; }
            Tile p{origin.x+dx*step,origin.y+dy*step};
            if (!walkable(p,step)) break;
            float incoming=camp_damage(p,camps);
            damage+=incoming;
            if (incoming==0) {
                if (!best.found || damage<best.damage || (damage==best.damage&&step<best.steps)) best={p,damage,step,true};
                break;
            }
        }
    }
    return best;
}
inline bool must_escape_camps(float hp,float incoming,float escape_damage) {
    // Continuing for another round must leave enough health to escape afterwards.
    return incoming>0 && hp<=incoming+escape_damage;
}
}
