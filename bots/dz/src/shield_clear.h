#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>

namespace dz {
enum class ShieldClearStatus { NotQuoted=-1, Cleared=0, Dead=1, BeyondHorizon=2, Invalid=3 };
struct ShieldClearInput {
    float hp=0,max_hp=0,target_hp=0,damage=0,incoming=0;
    unsigned reset_cd=0,reset_period=0,shield_cd=0,shield_period=0,shield_duration=0;
    float shield_amount=0,existing_value=0;
    unsigned existing_duration=0;
    bool existing=false,can_cast=true;
};
struct ShieldClearProjection {
    ShieldClearStatus status=ShieldClearStatus::NotQuoted;
    unsigned rounds=0,attacks=0,resets=0,shields=0;
    float loss=0,remaining_hp=0;
};
// Diagnostic single stationary target, fixed outgoing/incoming damage. Sample
// after the current camp phase. Reset has cast priority; at most one cast/turn.
// Native duration0 shields absorb the camp phase, then expire at owner start.
// No splash, movement, healing, other actors or health-dependent damage.
inline ShieldClearProjection shield_clear(ShieldClearInput in,unsigned horizon=96) {
    auto valid=[](float x){return std::isfinite(x)&&x>=0;};
    if(!horizon||horizon>2000||!valid(in.hp)||!in.hp||!valid(in.max_hp)||in.max_hp<in.hp||
       !valid(in.target_hp)||!in.target_hp||!valid(in.damage)||!in.damage||!valid(in.incoming)||
       !valid(in.shield_amount)||!valid(in.existing_value)||in.reset_cd>2000||in.reset_period>2000||
       in.shield_cd>2000||in.shield_period>2000||in.shield_duration>2000||in.existing_duration>2000||
       (!in.reset_period&&in.reset_cd)||(!in.shield_period&&in.shield_cd)||
       (in.shield_period&&(!in.shield_duration||!in.shield_amount)))return {ShieldClearStatus::Invalid};
    ShieldClearProjection result;result.remaining_hp=in.hp;const float initial_hp=in.hp;
    bool active=in.existing;float value=in.existing_value;
    int duration=static_cast<int>(in.existing_duration);
    for(unsigned turn=0;turn<horizon;++turn) {
        if(active&&(duration<=0||value<=0))active=false; // owner-start expiry, after camp phase
        bool cast=false;const bool may_cast=turn>0||in.can_cast;
        in.target_hp-=in.damage;++result.attacks;
        if(in.target_hp>0&&may_cast&&in.reset_period&&in.reset_cd==0) {
            in.target_hp-=in.damage;++result.attacks;++result.resets;
            in.reset_cd=in.reset_period;cast=true;
        }
        result.rounds=turn+1;
        if(in.target_hp<=0){result.status=ShieldClearStatus::Cleared;return result;}
        if(!cast&&may_cast&&in.shield_period&&!in.shield_cd&&!active&&in.hp<.85f*in.max_hp) {
            active=true;value=in.shield_amount;duration=static_cast<int>(in.shield_duration);
            in.shield_cd=in.shield_period;++result.shields;
        }
        if(turn+1==horizon){result.status=ShieldClearStatus::BeyondHorizon;return result;}
        if(in.reset_cd)--in.reset_cd;
        if(in.shield_cd)--in.shield_cd;
        if(active)--duration; // duration0 still protects the next camp phase
        float incoming=in.incoming;
        if(active) {
            const float absorbed=std::min(incoming,value);incoming-=absorbed;value-=absorbed;
            if(value<=0)active=false; // depleted shields disappear immediately
        }
        in.hp=std::max(0.f,in.hp-incoming);result.loss=initial_hp-in.hp;result.remaining_hp=in.hp;
        if(in.hp<=0){result.status=ShieldClearStatus::Dead;result.rounds=turn+2;return result;}
    }
    return result;
}
}
