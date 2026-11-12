#pragma once
#include <algorithm>
#include <cmath>

namespace dz {
// Restricted stationary alternating-turn primitive, sampled before our action.
// Enemy buffs are sampled NOW and remain active until THAT owner's start;
// first_can_cast describes availability at each actor's next action boundary.
// No movement, CC, healing, gear damage modifiers, splash, other actors
// or kill-credit refresh. Not connected to production decisions or EE.
struct DuelActor {
    float hp=0,max_hp=0,damage=0,missing_health_bonus=0;
    unsigned reset_cd=0,reset_period=0,shield_cd=0,shield_period=0,shield_duration=0;
    float shield_amount=0,existing_value=0;
    unsigned existing_duration=0;
    bool existing=false,first_can_cast=true;
};
enum class DuelStatus { Won=0,Dead=1,Horizon=2,Invalid=3 };
struct DuelCounts { unsigned basics=0,resets=0,shields=0; };
struct DuelOrder {
    bool alternating_round_lead=false;
    bool ours_first_now=true;
};
struct DuelProjection {
    DuelStatus status=DuelStatus::Invalid;
    // Inclusive own-turn observations. A win is visible in this own turn; a
    // lethal enemy reply is observed at our NEXT turn, hence one extra tick.
    unsigned owner_rounds=0;
    float our_hp=0,enemy_hp=0;
    DuelCounts ours,theirs;
};
inline DuelProjection stationary_duel(DuelActor ours,DuelActor enemy,DuelOrder order,unsigned horizon=96) {
    const auto valid=[](const DuelActor& p){
        auto nonnegative=[](float x){return std::isfinite(x)&&x>=0&&x<=1e9f;};
        return nonnegative(p.hp)&&p.hp>0&&nonnegative(p.max_hp)&&p.max_hp>=p.hp&&
            nonnegative(p.damage)&&p.damage>0&&nonnegative(p.missing_health_bonus)&&p.missing_health_bonus<=1&&
            nonnegative(p.shield_amount)&&nonnegative(p.existing_value)&&p.reset_cd<=2000&&p.reset_period<=2000&&
            p.shield_cd<=2000&&p.shield_period<=2000&&p.shield_duration<=2000&&p.existing_duration<=2000&&
            (p.reset_period||!p.reset_cd)&&(p.shield_period||!p.shield_cd)&&
            (!p.shield_period||(p.shield_duration&&p.shield_amount>0));
    };
    if(!horizon||horizon>2000||!valid(ours)||!valid(enemy))return {};
    struct State { DuelActor p;bool shield;float value;int duration;DuelCounts count; };
    State a{ours,ours.existing,ours.existing_value,static_cast<int>(ours.existing_duration),{}};
    State b{enemy,enemy.existing,enemy.existing_value,static_cast<int>(enemy.existing_duration),{}};
    DuelProjection out;
    const auto finish=[&](DuelStatus status,unsigned rounds){
        out.status=status;out.owner_rounds=rounds;out.our_hp=a.p.hp;out.enemy_hp=b.p.hp;out.ours=a.count;out.theirs=b.count;return out;
    };
    const auto hit=[](State& from,State& to){
        float damage=from.p.damage;
        if(from.p.missing_health_bonus>0)damage*=1.f+from.p.missing_health_bonus*(1.f-from.p.hp/from.p.max_hp);
        // A defender's duration0 shield still protects against an actor who
        // attacks before the defender's next start. Depletion is immediate.
        if(to.shield){const float absorbed=std::min(damage,to.value);damage-=absorbed;to.value-=absorbed;if(to.value<=0)to.shield=false;}
        to.p.hp=std::max(0.f,to.p.hp-damage);++from.count.basics;
    };
    const auto turn=[&](State& from,State& to,bool can_cast){
        if(from.shield&&(from.duration<=0||from.value<=0))from.shield=false;
        hit(from,to);if(to.p.hp<=0)return;
        bool cast=false;
        if(can_cast&&from.p.reset_period&&!from.p.reset_cd){
            from.p.reset_cd=from.p.reset_period;++from.count.resets;cast=true;hit(from,to);if(to.p.hp<=0)return;
        }
        if(!cast&&can_cast&&from.p.shield_period&&!from.p.shield_cd&&!from.shield&&from.p.hp<.85f*from.p.max_hp){
            from.shield=true;from.value=from.p.shield_amount;from.duration=static_cast<int>(from.p.shield_duration);
            from.p.shield_cd=from.p.shield_period;++from.count.shields;
        }
        if(from.p.reset_cd)--from.p.reset_cd;if(from.p.shield_cd)--from.p.shield_cd;
        if(from.shield)--from.duration;
    };
    unsigned enemy_turns_taken=0;
    for(unsigned i=0;i<horizon;++i){
        turn(a,b,i>0||ours.first_can_cast);if(b.p.hp<=0)return finish(DuelStatus::Won,i+1);
        if(i+1==horizon)return finish(DuelStatus::Horizon,i+1);
        // Default engine teams alternate the round's first actor. With the
        // fixed first-slot controlled subjects, the gap between OUR turns
        // therefore contains either two enemy turns or zero, not always one.
        const bool first=order.ours_first_now!=(bool(i&1));
        const unsigned replies=order.alternating_round_lead?(first?2:0):1;
        for(unsigned j=0;j<replies;++j){
            turn(b,a,enemy_turns_taken>0||enemy.first_can_cast);++enemy_turns_taken;
            if(a.p.hp<=0)return finish(DuelStatus::Dead,i+2);
        }
    }
    return finish(DuelStatus::Horizon,horizon);
}
}
