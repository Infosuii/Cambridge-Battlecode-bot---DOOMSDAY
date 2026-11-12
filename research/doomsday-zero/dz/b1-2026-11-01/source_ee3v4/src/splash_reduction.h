#pragma once
#include "camp_threat.h"
#include <bit>
#include <cstdint>
#include <span>

namespace dz {
struct SplashMember { Tile position;float hp=0,strength=0;int attack_range=0; };
struct SplashReduction { int target=-1;unsigned live=0;bool supported=false; };
// Exact restricted reduction, not a general group simulator. One live monster
// remains the executor's preferred target. Every other live member is harmless,
// within its splash radius and has no more HP, so all die by its killing hit.
// The existing single-target shield/reset model then prices the WHOLE clear.
inline SplashReduction splash_reduction(std::span<const SplashMember> members,Tile actor,int range) {
    SplashReduction result;
    auto position_ok=[](Tile p){return p.x>=-10000&&p.x<=10000&&p.y>=-10000&&p.y<=10000;};
    if(members.empty()||members.size()>64||!position_ok(actor)||range<0||range>100)return result;
    for(unsigned k=0;k<members.size();++k) {
        const auto& m=members[k];
        if(!position_ok(m.position)||!std::isfinite(m.hp)||m.hp<0||!std::isfinite(m.strength)||m.strength<0||
           m.attack_range<0||m.attack_range>100)return {};
        if(m.hp<=0)continue;
        ++result.live;
        if(m.strength>0) {
            if(result.target>=0)return result;
            result.target=static_cast<int>(k);
        }
    }
    if(result.target<0)return result;
    const auto& monster=members[result.target];const int distance=cheb(actor,monster.position);
    if(distance>range||distance>monster.attack_range)return result;
    // Use the executor's actual additive float score. A lexicographic sort is
    // not equivalent when HP differences exceed a thousand points.
    const float worst_monster_score=distance*1000.f+monster.hp-1e6f*monster.strength;
    if(!std::isfinite(worst_monster_score))return result;
    for(unsigned k=0;k<members.size();++k) {
        if(static_cast<int>(k)==result.target||members[k].hp<=0)continue;
        const auto& resource=members[k];
        if(resource.strength>0||cheb(resource.position,monster.position)>1||resource.hp>monster.hp||
           !(worst_monster_score<cheb(actor,resource.position)*1000.f))return result;
    }
    result.supported=true;return result;
}
// A sanity fingerprint of the observed member HP vector, not a security hash.
// Replay validation recomputes it in the same SDK member order, independently
// of aggregate HP (which could match despite an incorrect distribution).
inline std::uint32_t member_hp_hash(std::span<const float> hp) {
    std::uint32_t h=2166136261u;
    for(unsigned k=0;k<hp.size();++k) {
        h=(h^k)*16777619u;
        h=(h^std::bit_cast<std::uint32_t>(std::max(0.f,hp[k])))*16777619u;
    }
    return h;
}
}
