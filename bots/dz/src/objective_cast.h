#pragma once
#include "clear_risk.h"
#include <limits>

namespace dz::objective {
enum class CastKind { None, Reset, Shield, Damage };
struct Cast {
    CastKind kind=CastKind::None;
    unsigned cooldown=0,period=0,duration=0;
    float amount=0;
    bool operator==(const Cast&) const=default;
};
struct Kit {
    std::array<Cast,2> casts{};
    bool can_cast=true,refresh_on_monster=false;
    float shield=0;
    unsigned shield_duration=0;
    bool operator==(const Kit&) const=default;
    bool useful() const {
        return std::any_of(casts.begin(),casts.end(),[](auto c){return c.kind!=CastKind::None;});
    }
};
enum class CastStatus { Invalid, Complete, Dead, Horizon, Budget };
struct CastClear {
    CastStatus status=CastStatus::Invalid;
    unsigned rounds=0,attacks=0;
    std::array<unsigned,2> casts{};
    float loss=0,hp=0,shield=0;
    unsigned shield_duration=0;
    Kit remaining;
};
struct UnlimitedCast { bool operator()() const {return true;} };
// Owner-turn phase model for a supplied stationary focus sequence. Every living
// monster is charged against this body, regardless of range or allied tanks.
// One cast per turn: proactive self shield, basic, then reset/direct damage on a
// surviving target. No AoE, CC, dash, healing, future equipment or passive damage
// growth. Arrival and member travel belong to the adapter. A completed timeline
// is conditional on that geometry/policy; it is not a general survival proof.
template<class Budget=UnlimitedCast>
CastClear cast_clear(std::span<const ClearMember> members,float hp,float max_hp,float damage,
                     Kit kit,unsigned horizon=96,Budget budget={}) {
    CastClear out;out.hp=hp;out.remaining=kit;
    const auto positive=[](float x){return std::isfinite(x)&&x>=0;};
    if(members.empty()||members.size()>clear_risk_members||!positive(hp)||hp<=0||!positive(max_hp)||max_hp<hp||
       !positive(damage)||damage<=0||!positive(kit.shield)||kit.shield_duration>2000||!horizon||horizon>2000)return out;
    for(auto c:kit.casts)if(c.cooldown>2000||c.period>2000||c.duration>2000||!positive(c.amount)||
        (c.kind!=CastKind::None&&!c.period)||(c.kind==CastKind::Shield&&(!c.duration||!c.amount)))return out;
    std::array<float,clear_risk_members> targets{};float incoming=0;unsigned alive=0;
    for(unsigned k=0;k<members.size();++k) {
        if(!positive(members[k].hp)||!positive(members[k].incoming))return out;
        targets[k]=members[k].hp;
        if(targets[k]>0){incoming+=members[k].incoming;++alive;}
    }
    if(!std::isfinite(incoming))return out;
    unsigned focus=0;float shield=kit.shield;unsigned duration=kit.shield_duration;
    auto finish=[&](CastStatus status){
        out.status=status;out.loss=hp-out.hp;out.shield=shield;out.shield_duration=duration;out.remaining=kit;return out;
    };
    if(!alive)return finish(CastStatus::Complete);
    auto eliminate=[&](unsigned target) {
        if(targets[target]>0)return false;
        incoming=std::max(0.f,incoming-members[target].incoming);--alive;
        if(kit.refresh_on_monster&&members[target].incoming>0)for(auto& c:kit.casts)c.cooldown=0;
        return true;
    };
    for(unsigned turn=0;turn<horizon;++turn) {
        if(!budget())return finish(CastStatus::Budget);
        while(focus<members.size()&&targets[focus]<=0)++focus;
        if(!duration||shield<=0){shield=0;duration=0;}
        const bool may_cast=turn||kit.can_cast;
        int used=-1;
        if(may_cast&&!shield&&incoming>0)for(unsigned s=0;s<kit.casts.size();++s) {
            auto& c=kit.casts[s];
            if(c.kind==CastKind::Shield&&!c.cooldown) {
                shield=c.amount;duration=c.duration;c.cooldown=c.period;used=s;++out.casts[s];break;
            }
        }
        targets[focus]-=damage;++out.attacks;
        bool killed=eliminate(focus);
        if(!killed&&may_cast&&used<0)for(unsigned s=0;s<kit.casts.size();++s) {
            auto& c=kit.casts[s];if(c.cooldown||(c.kind!=CastKind::Reset&&c.kind!=CastKind::Damage))continue;
            targets[focus]-=c.kind==CastKind::Reset?damage:c.amount;
            if(c.kind==CastKind::Reset)++out.attacks;
            c.cooldown=c.period;used=s;++out.casts[s];killed=eliminate(focus);break;
        }
        out.rounds=turn+1;
        if(!alive)return finish(CastStatus::Complete);
        // Owner end decrements cooldowns/durations; duration zero still protects
        // the intervening camp phase and expires at the next owner start.
        for(auto& c:kit.casts)if(c.cooldown)--c.cooldown;
        if(duration)--duration;
        float hit=incoming;
        const float absorbed=std::min(hit,shield);shield-=absorbed;hit-=absorbed;
        out.hp=std::max(0.f,out.hp-hit);
        if(out.hp<=0)return finish(CastStatus::Dead);
    }
    return finish(CastStatus::Horizon);
}
}
