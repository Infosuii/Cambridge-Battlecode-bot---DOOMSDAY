#pragma once
#include "camp_threat.h"
#include <cstdint>
#include <array>

namespace dz::siege {
template<class Walkable,class Budget=UnlimitedEscapeBudget>
EscapeRoute escape_route(Tile origin,std::span<const CampThreat> camps,std::span<const Tile> directions,Walkable walkable,Budget budget={}) {
    int range=0;for(auto camp:camps)range=std::max(range,camp.range);
    EscapeRoute best;
    // Only completed routes can be returned. A budget stop may leave the search
    // incomplete, but does not invalidate a previously checked escape path.
    for(auto direction:directions) {
        float damage=0;
        for(int step=1;step<=2*range+2;++step) {
            if((step&3)==1&&!budget()){best.truncated=true;return best;}
            const Tile p{origin.x+direction.x*step,origin.y+direction.y*step};
            if(!walkable(p))break;
            const float incoming=camp_damage(p,camps);damage+=incoming;
            if(best.found&&damage>=best.damage)break;
            if(incoming==0) {
                best={p,damage,step,true,false};
                if(damage==0)return best;
                break;
            }
        }
    }
    return best;
}
enum class Phase : std::uint8_t { None, Approach, Strike, Escape, Recover };
inline bool backtrack_safe(float hp,float max_hp,float here,float next,float escape) {
    for(auto x:{hp,max_hp,here,next,escape})if(!std::isfinite(x)||x<0)return false;
    // After the next camp phase, retain a step back to the checked origin,
    // its complete escape, and one raw surprise phase. No future ally/shield.
    return hp>.15f*max_hp+1.25f*(escape+here)+next+std::max(here,next);
}
inline bool yield_lane(Tile self,Tile ally,float hp,float max_hp,float ally_hp,float ally_max,int home,int ally_home) {
    return max_hp>0&&ally_max>0&&ally_hp>0&&cheb(self,ally)<=2&&home<ally_home&&
        ally_hp/ally_max<hp/max_hp;
}
struct Support { Tile p;unsigned handle;float hp,max_hp; };
struct Incoming { float raw=0,current=0;unsigned protected_camps=0;bool valid=false; };
// Other actors are admitted only by the SDK adapter after their turn is done.
// Thus their positions cannot change before this round's camp phase. Unknown
// armour on allies is priced as NONE; a dying ally never supplies protection.
inline Incoming incoming(Tile p,unsigned handle,std::span<const CampThreat> camps,std::span<const Support> allies,float nominal_ratio=1) {
    if(allies.size()>6||camps.size()>64||!std::isfinite(nominal_ratio)||nominal_ratio<1)return {};
    for(auto ally:allies)if(!std::isfinite(ally.hp)||!std::isfinite(ally.max_hp)||ally.hp<0||ally.max_hp<ally.hp)return {};
    for(auto camp:camps)if(!std::isfinite(camp.strength)||camp.strength<0||camp.range<0)return {};
    std::array<int,64> targets{};std::array<float,6> damage{};Incoming result;
    for(unsigned i=0;i<camps.size();++i) {
        const auto& camp=camps[i];
        int nearest=cheb(p,camp.p);unsigned first=handle;int target=-1;
        for(unsigned a=0;a<allies.size();++a) {
            const int distance=cheb(allies[a].p,camp.p);
            if(distance<nearest||(distance==nearest&&allies[a].handle<first)) {nearest=distance;first=allies[a].handle;target=a;}
        }
        if(cheb(p,camp.p)<=camp.range)result.raw+=camp.strength;
        if(nearest>camp.range)target=-2;
        targets[i]=target;
        if(target>=0)damage[target]+=camp.strength*nominal_ratio;
    }
    for(unsigned i=0;i<camps.size();++i)if(cheb(p,camps[i].p)<=camps[i].range) {
        const int target=targets[i];
        const bool protected_by_ally=target>=0&&allies[target].hp>1.25f*damage[target]+.15f*allies[target].max_hp;
        if(protected_by_ally)++result.protected_camps;else result.current+=camps[i].strength;
    }
    result.valid=true;return result;
}
struct Wave {
    bool valid=false;
    int attacks=0,needed=0,waves=0;
    float reserve=0,damage=0;
};
// A visit can be useful without completing a clear. Camp HP persists through
// healing. Credit at most a VERIFIED shield's first incoming phase. Future casts
// and future ally protection never reduce the escape or surprise-phase reserve.
inline Wave quote(float hp,float max_hp,float target_hp,float damage,float incoming,float escape_loss,int horizon=2000,float surprise=-1,float shield_credit=0) {
    for(auto value:{hp,max_hp,target_hp,damage,incoming,escape_loss})if(!std::isfinite(value)||value<0)return {};
    if(hp<=0||hp>max_hp||target_hp<=0||damage<=0||horizon<1||horizon>2000)return {};
    const double work=std::ceil(static_cast<double>(target_hp)/damage);
    if(work>2000000)return {};
    Wave result;result.needed=static_cast<int>(work);
    if(!std::isfinite(surprise)||surprise< -1)return {};
    if(!std::isfinite(shield_credit)||shield_credit<0||shield_credit>incoming)return {};
    result.reserve=.15f*max_hp+1.25f*escape_loss+std::max(incoming,surprise);
    int capacity=horizon;
    if(incoming>0) {
        const double room=(static_cast<double>(hp)+shield_credit-result.reserve)/incoming;
        if(room<=1)return result;
        capacity=static_cast<int>(std::min<double>(horizon,std::ceil(room)-1));
    } else if(hp<=result.reserve)return result;
    result.attacks=std::min(result.needed,capacity);
    if(result.attacks<=0)return result;
    result.waves=(result.needed+capacity-1)/capacity;
    result.damage=std::min(target_hp,result.attacks*damage);
    result.valid=true;return result;
}
struct Task {
    int group=-1,member=-1;
    Phase phase=Phase::None;
    Tile attack{},exit{};
    float last_target_hp=0,escape_loss=0,incoming=0;
    float visit_hp=0;
    float shield_credit=0,required_shield=0;
    bool struck=false,finished=false,support_seen=false,restock=false;
    bool planned_approach=false;
    int checked=0,distance=65535,last_round=-1,retry_after=0,visits=0,failures=0;
    bool active() const { return group>=0&&member>=0&&phase!=Phase::None; }
    void reset(int round,int cooldown=0) { *this={};retry_after=round+cooldown; }
    void start(int g,int k,int round,int dist,float hp) {
        *this={};group=g;member=k;phase=Phase::Approach;last_target_hp=hp;checked=round;distance=dist;
    }
    bool progress(int round,int dist,float hp) {
        if(dist<distance||hp+.01f<last_target_hp){checked=round;distance=dist;last_target_hp=hp;failures=0;}
        return round-checked<=30;
    }
};
}
