#pragma once
#include "siege_model.h"
#include <limits>

namespace dz::crew {
inline constexpr unsigned max_units=6,max_camps=64;
struct Unit {
    unsigned slot=0,handle=0;
    Tile p{};
    float hp=0,max_hp=0,damage=0,factor=1;
    int range=1,arrival=0;
    float gold_multiplier=1;
    int capture_rounds=5;
};
struct Monster { unsigned member=0;Tile p{};float hp=0,damage=0;int range=0; };
struct Formation {
    bool valid=false;
    unsigned tank=0,active=0;
    unsigned focus=0;
    std::array<Tile,max_units> positions{};
    Tile exit{};
    int escape_steps=0;
};
inline int camp_target(const Monster& camp,std::span<const Unit> units,const Formation& f) {
    int target=-1,distance=camp.range+1;
    for(unsigned u=0;u<units.size();++u)if(f.active&(1u<<u)) {
        const int d=cheb(camp.p,f.positions[u]);
        if(d>camp.range)continue;
        if(d<distance||(d==distance&&(target<0||units[u].handle<units[target].handle))){distance=d;target=u;}
    }
    return target;
}
struct Unlimited { bool operator()() const { return true; } };
// Stable roles use maximum effective HP and native-handle ties, not this turn's
// fluctuating HP/positions. An earlier-handle melee helper that would steal the
// tank's target is omitted; ranged helpers can stand farther away. All positions
// are distinct and the tank's complete checked exit ray remains unoccupied.
template<class Walkable,class Home,class Budget=Unlimited>
Formation arrange(std::span<const Unit> units,std::span<const Monster> camps,unsigned focus,
                  Walkable walkable,Home home,Budget budget={}) {
    Formation f;f.focus=focus;
    if(units.empty()||units.size()>max_units||camps.empty()||camps.size()>max_camps||focus>=camps.size())return f;
    for(const auto& c:camps)if(!std::isfinite(c.hp)||!std::isfinite(c.damage)||c.hp<=0||c.damage<0||c.range<0)return f;
    for(const auto& u:units)if(!std::isfinite(u.hp)||!std::isfinite(u.max_hp)||!std::isfinite(u.damage)||
        !std::isfinite(u.factor)||u.hp<=0||u.max_hp<u.hp||u.damage<=0||u.factor<=0||u.range<1||u.range>3)return f;
    for(unsigned u=1;u<units.size();++u) {
        const double strength=units[u].max_hp/units[u].factor,best=units[f.tank].max_hp/units[f.tank].factor;
        if(strength>best||(strength==best&&units[u].handle<units[f.tank].handle))f.tank=u;
    }
    std::array<CampThreat,max_camps> threats{};
    for(unsigned c=0;c<camps.size();++c)threats[c]={camps[c].p,camps[c].damage,camps[c].range};
    const auto scene=std::span<const CampThreat>(threats.data(),camps.size());
    auto open=[&](Tile p) {
        return walkable(p)&&std::none_of(camps.begin(),camps.end(),[&](auto c){return c.p==p;});
    };
    struct TileCost { Tile p;float incoming;int home; };
    std::array<TileCost,8> front{};unsigned count=0;
    for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy) {
        if(!budget())return f;
        if(!dx&&!dy)continue;const Tile p{camps[focus].p.x+dx,camps[focus].p.y+dy};
        if(open(p))front[count++]={p,camp_damage(p,scene),home(p)};
    }
    std::sort(front.begin(),front.begin()+count,[](auto a,auto b){
        if(a.incoming!=b.incoming)return a.incoming<b.incoming;
        if(a.home!=b.home)return a.home<b.home;
        return a.p.x<b.p.x||(a.p.x==b.p.x&&a.p.y<b.p.y);
    });
    EscapeRoute route;
    for(unsigned i=0;i<count;++i) {
        const auto p=front[i].p;
        std::array<Tile,8> directions{{{-1,-1},{-1,0},{-1,1},{0,-1},{0,1},{1,-1},{1,0},{1,1}}};
        std::sort(directions.begin(),directions.end(),[&](auto a,auto b){
            return home({p.x+a.x,p.y+a.y})<home({p.x+b.x,p.y+b.y});
        });
        route=siege::escape_route(p,scene,directions,open,budget);
        if(route.truncated)return f;
        if(route.found){f.positions[f.tank]=p;break;}
    }
    if(!route.found)return f;
    f.exit=route.exit;f.escape_steps=route.steps;f.active=1u<<f.tank;
    auto reserved=[&](Tile p) {
        const auto start=f.positions[f.tank];const int dx=(f.exit.x>start.x)-(f.exit.x<start.x),dy=(f.exit.y>start.y)-(f.exit.y<start.y);
        for(int step=0;step<=route.steps;++step)if(p==Tile{start.x+step*dx,start.y+step*dy})return true;
        for(unsigned u=0;u<units.size();++u)if((f.active&(1u<<u))&&f.positions[u]==p)return true;
        return false;
    };
    std::array<unsigned,max_units> order{};for(unsigned u=0;u<units.size();++u)order[u]=u;
    std::sort(order.begin(),order.begin()+units.size(),[&](auto a,auto b){return units[a].handle<units[b].handle;});
    for(unsigned k=0;k<units.size();++k) {
        const unsigned u=order[k];if(u==f.tank)continue;
        bool found=false;float incoming=std::numeric_limits<float>::infinity();int reach=-1,distance=65535;
        for(int dx=-units[u].range;dx<=units[u].range;++dx)for(int dy=-units[u].range;dy<=units[u].range;++dy) {
            if(!budget())return {};
            const Tile p{camps[focus].p.x+dx,camps[focus].p.y+dy};const int r=cheb(p,camps[focus].p);
            if(!r||!open(p)||reserved(p)||(r==1&&units[u].handle<units[f.tank].handle))continue;
            const float danger=camp_damage(p,scene);const int h=home(p);
            if(!found||danger<incoming||(danger==incoming&&(r>reach||(r==reach&&h<distance)))) {
                found=true;incoming=danger;reach=r;distance=h;f.positions[u]=p;
            }
        }
        if(found)f.active|=1u<<u;
    }
    f.valid=true;return f;
}
struct Quote {
    bool complete=false,survivable=false;
    int clear=0,finish=0;
    std::array<double,max_units> loss{};
};
// Fixed-position, range-aware whole-encounter bound. Per-camp damage comes only
// from actors that can actually hit it. Nearest/handle targeting assigns each
// incoming stream to one actor. Each actor gets its WORST possible clear order;
// formation changes, hidden enemies and traffic remain runtime uncertainties.
inline Quote forecast(std::span<const Unit> units,std::span<const Monster> camps,const Formation& f,int setup=0,int capture=6,int horizon=2000) {
    Quote q;if(!f.valid||units.empty()||units.size()>max_units||camps.size()>max_camps||setup<0||capture<0||horizon<1||horizon>2000)return q;
    if(f.tank>=units.size()||f.focus>=camps.size()||!f.active||(f.active&~((1u<<units.size())-1u)))return q;
    for(const auto& c:camps)if(!std::isfinite(c.hp)||!std::isfinite(c.damage)||c.hp<=0||c.damage<0||c.range<0)return q;
    for(const auto& u:units)if(!std::isfinite(u.hp)||!std::isfinite(u.max_hp)||!std::isfinite(u.damage)||!std::isfinite(u.factor)||
        u.hp<=0||u.max_hp<u.hp||u.damage<=0||u.factor<=0||u.range<1||u.range>3)return q;
    struct Job { int turns;float incoming; };
    std::array<int,max_camps> work{};std::array<int,max_camps> targets{};
    for(unsigned c=0;c<camps.size();++c) {
        float damage=0;
        for(unsigned u=0;u<units.size();++u)if((f.active&(1u<<u))&&cheb(f.positions[u],camps[c].p)<=units[u].range)damage+=units[u].damage;
        if(damage<=0||!std::isfinite(damage)||camps[c].hp/damage>horizon)return q;
        work[c]=static_cast<int>(std::ceil(static_cast<double>(camps[c].hp)/damage));q.clear+=work[c];
        if(q.clear>horizon)return q;
        targets[c]=camp_target(camps[c],units,f);
    }
    q.finish=setup+q.clear+capture;if(q.finish>horizon)return q;
    q.survivable=true;
    for(unsigned u=0;u<units.size();++u)if(f.active&(1u<<u)) {
        std::array<Job,max_camps> jobs{};unsigned n=0;
        for(unsigned c=0;c<camps.size();++c)jobs[n++]={work[c],targets[c]==static_cast<int>(u)?camps[c].damage*units[u].factor:0};
        std::sort(jobs.begin(),jobs.begin()+n,[](auto a,auto b){return static_cast<double>(a.incoming)*b.turns<static_cast<double>(b.incoming)*a.turns;});
        int elapsed=setup;
        for(unsigned j=0;j<n;++j){elapsed+=jobs[j].turns;q.loss[u]+=jobs[j].incoming*std::max(0,elapsed-1);}
        q.survivable&=units[u].hp>1.25*q.loss[u]+.15*units[u].max_hp;
    }
    q.complete=true;return q;
}
}
