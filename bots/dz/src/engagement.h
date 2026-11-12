#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <span>

namespace dz::combat {
inline constexpr unsigned max_units=12;
enum class Kind { None, Reset, Damage, Shield, Dash, Heal, Control };
struct Spell { Kind kind=Kind::None;float amount=0,range=0;int cooldown=0,period=0,duration=0;bool exclusive=false; };
struct Unit {
    int x=0,y=0,side=0,range=1;
    float hp=0,max_hp=0,damage=0,mitigation=1,shield=0,bag=0;
    float retaliation=0,environment_factor=0,uncertain_incoming=0,removal_value=35;
    int shield_ticks=0,stun=0,linked=-1;
    bool can_move=true,can_attack=true,can_cast=true,immune=false,heart=false,ranged=false,splash=false;
    std::array<Spell,2> spells{};
    unsigned committed_ticks=8;
    bool pursue=true;
    int preferred=-1;
};
struct Result {
    bool valid=false;float self_hp=0,our_loss=0,their_loss=0,kill_value=0,death_value=0;
    unsigned our_dead=0,their_dead=0;int self_death=-1;
};
inline int distance(const Unit& a,const Unit& b) { return std::max(std::abs(a.x-b.x),std::abs(a.y-b.y)); }
// Deliberately bounded microforecast, with explicit action-order variants.
// Caller provides frozen legal terrain; dynamic occupancy and movement are
// resolved here. This is not the stationary duel primitive's conformance claim.
struct Unlimited { bool operator()() const { return true; } };
struct NoExposure {float operator()(int,int) const {return 0;}};
struct NoHome {bool operator()(int,int,int) const {return false;}};
template<class Walkable,class Budget=Unlimited,class Exposure=NoExposure,class Home=NoHome>
Result project(std::span<const Unit> scene,unsigned focus,bool enemy_first,Walkable walkable,unsigned horizon=4,bool fleeing=false,int escape_x=0,int escape_y=0,Budget budget={},Exposure exposure={},Home home={},bool enemy_flee=false) {
    if(scene.empty()||scene.size()>max_units||focus>=scene.size()||scene[0].side!=0||scene[focus].side!=1||horizon<1||horizon>8)return {};
    std::array<Unit,max_units> units{};
    for(unsigned i=0;i<scene.size();++i) {
        const auto& u=scene[i];
        if(!std::isfinite(u.hp)||!std::isfinite(u.max_hp)||!std::isfinite(u.damage)||!std::isfinite(u.shield)||
            !std::isfinite(u.mitigation)||!std::isfinite(u.bag)||!std::isfinite(u.retaliation)||u.retaliation<0||u.hp<=0||u.max_hp<u.hp||u.damage<0||u.shield<0||
            u.mitigation<0||u.mitigation>1||u.range<1||u.range>20||u.side<0||u.side>1||u.linked>=static_cast<int>(scene.size())||
            !std::isfinite(u.environment_factor)||u.environment_factor<0||!std::isfinite(u.uncertain_incoming)||u.uncertain_incoming<0||
            !std::isfinite(u.removal_value)||u.removal_value<0||u.preferred>=static_cast<int>(scene.size())||
            (u.preferred>=0&&scene[u.preferred].side==u.side))return {};
        for(auto s:u.spells)if(!std::isfinite(s.amount)||!std::isfinite(s.range)||s.amount<0||s.range<0||s.range>100||s.cooldown<0||s.period<0||s.duration<0)return {};
        units[i]=u;
    }
    Result result;result.valid=true;
    auto apply=[&](unsigned target,float damage,bool reduced=false) {
        auto& t=units[target];if(!reduced)damage*=t.mitigation;
        const float absorbed=std::min(t.shield,damage);t.shield-=absorbed;damage-=absorbed;
        t.hp=std::max(0.f,t.hp-damage);
        if(t.hp==0&&t.linked>=0)units[t.linked].hp=0;
    };
    auto hit=[&](unsigned attacker,unsigned target,float damage,bool splash=false) {
        apply(target,damage);
        // Retaliation cannot recursively trigger itself in the approximation.
        if(units[target].retaliation>0)apply(attacker,units[target].retaliation);
        if(splash)for(unsigned j=0;j<scene.size();++j)
            if(j!=target&&units[j].side!=units[attacker].side&&units[j].hp>0&&distance(units[j],units[target])<=1) {
                apply(j,damage);
                if(units[j].retaliation>0)apply(attacker,units[j].retaliation);
            }
    };
    auto free=[&](int x,int y,unsigned actor) {
        if constexpr(requires{walkable(x,y,units[actor].side);}) {if(!walkable(x,y,units[actor].side))return false;}
        else if(!walkable(x,y))return false;
        for(unsigned i=0;i<scene.size();++i)if(i!=actor&&units[i].hp>0&&units[i].x==x&&units[i].y==y)return false;
        return true;
    };
    for(unsigned tick=0;tick<horizon;++tick) {for(unsigned pass=0;pass<2;++pass) {
        const int side=enemy_first?1-static_cast<int>(pass):static_cast<int>(pass);
        for(unsigned i=0;i<scene.size();++i) {
            auto& u=units[i];if(u.side!=side||u.hp<=0)continue;
            if(!budget())return {}; // Discard partial forecasts; never treat them as a safe fight.
            if(tick>0&&home(u.x,u.y,u.side))u.hp=u.max_hp;
            if(u.shield_ticks<=0)u.shield=0;
            if(tick>=u.committed_ticks) {for(auto& s:u.spells)if(s.cooldown>0)--s.cooldown;--u.shield_ticks;continue;}
            if(u.stun>0) {--u.stun;--u.shield_ticks;for(auto& s:u.spells)if(s.cooldown>0)--s.cooldown;continue;}
            unsigned target=scene.size();float best=1e30f;
            for(unsigned j=0;j<scene.size();++j)if(units[j].side!=side&&units[j].hp>0) {
                const auto& t=units[j];
                const float score=std::max(0,distance(u,t)-u.range)*u.damage+t.hp+t.shield-
                    ((side==0&&j==static_cast<unsigned>(u.preferred>=0?u.preferred:static_cast<int>(focus)))?u.damage*2:0)-t.bag*.5f;
                if(score<best){best=score;target=j;}
            }
            if(target==scene.size())continue;
            auto& t=units[target];bool cast=false,moved=false,exclusive=false;
            const bool may_cast=tick>0||u.can_cast;
            float incoming=0;
            for(unsigned j=0;j<scene.size();++j)if(units[j].side!=side&&units[j].hp>0&&distance(u,units[j])<=units[j].range+1)incoming+=units[j].damage;
            const float neutral=exposure(u.x,u.y)*u.environment_factor;
            if(!std::isfinite(neutral)||neutral<0)return {};
            incoming+=neutral+u.uncertain_incoming;
            // Reserve the one cast: a useful ready shield takes priority over
            // damage. No arbitrary low-HP prerequisite; full HP can be exposed.
            for(auto& s:u.spells)if(!cast&&may_cast&&s.kind==Kind::Shield&&s.cooldown==0&&u.shield<=0&&incoming>=.5f*s.amount) {
                u.shield=s.amount;u.shield_ticks=s.duration;cast=true;exclusive=s.exclusive;s.cooldown=s.period;
            }
            const bool escape=(fleeing&&i==0)||(enemy_flee&&side==1&&!home(u.x,u.y,u.side));
            const int tx=escape?(side==1?u.x+8*((u.x>t.x)-(u.x<t.x)):escape_x):t.x;
            const int ty=escape?(side==1?u.y+8*((u.y>t.y)-(u.y<t.y)):escape_y):t.y;
            if(!cast&&may_cast&&(escape||(u.pursue&&!(enemy_flee&&side==1)))&&(tick>0||u.can_move))for(auto& s:u.spells)
                if(s.kind==Kind::Dash&&s.cooldown==0&&(escape||distance(u,t)>u.range)) {
                    const int ox=u.x,oy=u.y;
                    for(int step=0;step<std::min(8,static_cast<int>(s.range))&&(escape?(u.x!=tx||u.y!=ty):distance(u,t)>u.range);++step) {
                        const int x=u.x+(tx>u.x)-(tx<u.x),y=u.y+(ty>u.y)-(ty<u.y);
                        if(!free(x,y,i))break;u.x=x;u.y=y;
                    }
                    if(u.x==ox&&u.y==oy)continue;
                    if(!escape&&distance(u,t)<=1){hit(i,target,s.amount);if(!t.immune)t.stun=std::max(t.stun,s.duration);}
                    cast=true;exclusive=s.exclusive;s.cooldown=s.period;break;
                }
            if(!exclusive&&(tick>0||u.can_move)&&(escape||(u.pursue&&!(enemy_flee&&side==1)&&distance(u,t)>u.range))) {
                int bx=u.x,by=u.y;
                const int sx=(tx>u.x)-(tx<u.x),sy=(ty>u.y)-(ty<u.y);
                const std::array<std::array<int,2>,3> moves{{{sx,sy},{sx,0},{0,sy}}};
                for(auto delta:moves) {
                    const int dx=delta[0],dy=delta[1];
                    const int x=u.x+dx,y=u.y+dy;if(!free(x,y,i))continue;
                    if(std::max(std::abs(x-tx),std::abs(y-ty))<std::max(std::abs(u.x-tx),std::abs(u.y-ty)))
                        {bx=x;by=y;break;}
                }
                moved=bx!=u.x||by!=u.y;u.x=bx;u.y=by;
            }
            const float multiplier=u.heart?1+.5f*(1-u.hp/u.max_hp):1;
            bool attacked=false;
            if(u.hp>0&&t.hp>0&&(tick>0||u.can_attack)&&distance(u,t)<=u.range&&!(u.ranged&&moved)) {hit(i,target,u.damage*multiplier,u.splash);attacked=true;}
            for(auto& s:u.spells)if(u.hp>0&&!cast&&may_cast&&s.cooldown==0&&!(s.exclusive&&moved)) {
                if(s.kind==Kind::Reset&&attacked&&t.hp>0){hit(i,target,u.damage*multiplier,u.splash);if(!t.immune)t.stun=std::max(t.stun,s.duration);cast=true;}
                else if((s.kind==Kind::Damage||s.kind==Kind::Control)&&t.hp>0&&distance(u,t)<=s.range) {
                    hit(i,target,s.amount*multiplier);if(s.kind==Kind::Control&&!t.immune)t.stun=std::max(t.stun,s.duration);cast=true;
                } else if(s.kind==Kind::Heal&&u.hp<u.max_hp&&incoming>0){u.hp=std::min(u.max_hp,u.hp+s.amount);cast=true;}
                if(cast)s.cooldown=s.period;
            }
            for(auto& s:u.spells)if(s.cooldown>0)--s.cooldown;
            --u.shield_ticks;
            if(units[0].hp<=0&&result.self_death<0)result.self_death=tick;
        }
    }
        // Neutral hazards hit even a stunned or non-participating ally. Never
        // infer enemy camp damage to make an exchange look favourable.
        for(unsigned i=0;i<scene.size();++i)if(units[i].hp>0) {
            if(!budget())return {};
            const float damage=exposure(units[i].x,units[i].y)*units[i].environment_factor;
            if(!std::isfinite(damage)||damage<0)return {};
            apply(i,damage+units[i].uncertain_incoming,true);
        }
        if(units[0].hp<=0&&result.self_death<0)result.self_death=tick;
    }
    result.self_hp=units[0].hp;
    for(unsigned i=0;i<scene.size();++i) {
        const float lost=scene[i].hp-units[i].hp;
        const float value=scene[i].bag+scene[i].removal_value;
        if(scene[i].side==0){result.our_loss+=lost;if(units[i].hp<=0){++result.our_dead;result.death_value+=value;}}
        else {result.their_loss+=lost;if(units[i].hp<=0){++result.their_dead;result.kill_value+=value;}}
    }
    return result;
}
}
