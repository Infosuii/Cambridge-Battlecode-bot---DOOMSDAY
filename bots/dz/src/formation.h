#pragma once
#include "siege_model.h"
#include <limits>
#include <bit>

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
inline bool same_roles(std::span<const Unit> a,std::span<const Unit> b) {
    if(a.size()!=b.size())return false;
    for(unsigned i=0;i<a.size();++i)if(a[i].hp<=0||a[i].slot!=b[i].slot||a[i].handle!=b[i].handle||
        a[i].max_hp!=b[i].max_hp||a[i].damage!=b[i].damage||a[i].factor!=b[i].factor||a[i].range!=b[i].range)return false;
    return true;
}
inline bool same_scene(std::span<const Monster> a,std::span<const Monster> b) {
    if(a.size()!=b.size())return false;
    for(unsigned i=0;i<a.size();++i)if(a[i].hp<=0||a[i].member!=b[i].member||a[i].p!=b[i].p||a[i].damage!=b[i].damage||a[i].range!=b[i].range)return false;
    return true;
}
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
                  Walkable walkable,Home home,Budget budget={},unsigned preferred=max_units) {
    Formation f;f.focus=focus;
    if(units.empty()||units.size()>max_units||camps.empty()||camps.size()>max_camps||focus>=camps.size())return f;
    for(const auto& c:camps)if(!std::isfinite(c.hp)||!std::isfinite(c.damage)||c.hp<=0||c.damage<0||c.range<0)return f;
    for(const auto& u:units)if(!std::isfinite(u.hp)||!std::isfinite(u.max_hp)||!std::isfinite(u.damage)||
        !std::isfinite(u.factor)||u.hp<=0||u.max_hp<u.hp||u.damage<=0||u.factor<=0||u.range<1||u.range>3)return f;
    for(unsigned u=1;u<units.size();++u) {
        const double strength=units[u].max_hp/units[u].factor,best=units[f.tank].max_hp/units[f.tank].factor;
        if(strength>best||(strength==best&&units[u].handle<units[f.tank].handle))f.tank=u;
    }
    if(preferred<units.size())f.tank=preferred;
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
        if(!budget())return f;
        const auto p=front[i].p;
        const std::array<Tile,8> steps{{{-1,-1},{-1,0},{-1,1},{0,-1},{0,1},{1,-1},{1,0},{1,1}}};
        std::array<std::pair<int,Tile>,8> ordered{};
        for(unsigned d=0;d<steps.size();++d) {
            if(!budget())return f;
            ordered[d]={home({p.x+steps[d].x,p.y+steps[d].y}),steps[d]};
        }
        // The adapter's home lookup is not free. Never put it in a comparator:
        // one uninterruptible sort used to re-read it dozens of times between
        // budget checks, including after a previous route exhausted its slice.
        std::sort(ordered.begin(),ordered.end(),[](const auto& a,const auto& b){return a.first<b.first;});
        std::array<Tile,8> directions{};
        for(unsigned d=0;d<steps.size();++d)directions[d]=ordered[d].second;
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
template<class Budget=Unlimited>
Quote forecast(std::span<const Unit> units,std::span<const Monster> camps,const Formation& f,int setup=0,int capture=6,int horizon=2000,Budget budget={}) {
    Quote q;if(!f.valid||units.empty()||units.size()>max_units||camps.size()>max_camps||setup<0||capture<0||horizon<1||horizon>2000)return q;
    if(f.tank>=units.size()||f.focus>=camps.size()||!f.active||(f.active&~((1u<<units.size())-1u)))return q;
    for(const auto& c:camps)if(!std::isfinite(c.hp)||!std::isfinite(c.damage)||c.hp<=0||c.damage<0||c.range<0)return q;
    for(const auto& u:units)if(!std::isfinite(u.hp)||!std::isfinite(u.max_hp)||!std::isfinite(u.damage)||!std::isfinite(u.factor)||
        u.hp<=0||u.max_hp<u.hp||u.damage<=0||u.factor<=0||u.range<1||u.range>3)return q;
    struct Job { int turns;float incoming; };
    std::array<int,max_camps> work{};std::array<int,max_camps> targets{};
    for(unsigned c=0;c<camps.size();++c) {
        if(!budget())return {};
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
        if(!budget())return {};
        std::array<Job,max_camps> jobs{};unsigned n=0;
        for(unsigned c=0;c<camps.size();++c)jobs[n++]={work[c],targets[c]==static_cast<int>(u)?camps[c].damage*units[u].factor:0};
        std::sort(jobs.begin(),jobs.begin()+n,[](auto a,auto b){return static_cast<double>(a.incoming)*b.turns<static_cast<double>(b.incoming)*a.turns;});
        int elapsed=setup;
        for(unsigned j=0;j<n;++j){elapsed+=jobs[j].turns;q.loss[u]+=jobs[j].incoming*std::max(0,elapsed-1);}
        q.survivable&=units[u].hp>1.25*q.loss[u]+.15*units[u].max_hp;
    }
    q.complete=true;return q;
}
struct Visit {
    bool complete=false;
    int attacks=0,waves=0,finish=0;
    unsigned ready=0;
};
// Bounded partial-clear contract. Every actor funds its OWN full-raw camp
// exposure and a checked exit with all other formation poses occupied. A future
// visit uses full HP only after paying escape, recall/heal and return travel.
// This deliberately needs no future shield, ally tank credit or kill reset.
template<class Walkable,class Home,class Budget=Unlimited>
Visit visit(std::span<const Unit> units,std::span<const Monster> camps,const Formation& f,
            int recall,Walkable walkable,Home home,Budget budget={}) {
    Visit result;const auto full=forecast(units,camps,f,0,6,2000,budget);
    if(!full.complete||recall<0||recall>2000)return result;
    std::array<CampThreat,max_camps> threats{};
    for(unsigned c=0;c<camps.size();++c)threats[c]={camps[c].p,camps[c].damage,camps[c].range};
    const auto scene=std::span<const CampThreat>(threats.data(),camps.size());
    const std::array<Tile,8> directions{{{-1,-1},{-1,0},{-1,1},{0,-1},{0,1},{1,-1},{1,0},{1,1}}};
    int capacity=2000,recovered=2000,heal=0;
    for(unsigned u=0;u<units.size();++u)if(f.active&(1u<<u)) {
        if(!budget())return {};
        const float raw=camp_damage(f.positions[u],scene)*units[u].factor;
        float loss=0;int steps=0;
        if(raw>0) {
            const auto route=siege::escape_route(f.positions[u],scene,directions,[&](Tile p) {
                if(!walkable(p)||std::any_of(camps.begin(),camps.end(),[&](auto c){return p==c.p;}))return false;
                for(unsigned a=0;a<units.size();++a)if(a!=u&&(f.active&(1u<<a))&&p==f.positions[a])return false;
                return true;
            },budget);
            if(!route.found)return {};
            loss=route.damage*units[u].factor;steps=route.steps;
        }
        const int distance=home(f.positions[u]);if(distance<0||distance>=65535)return {};
        heal=std::max(heal,steps+recall+1+distance);
        const auto current=siege::quote(units[u].hp,units[u].max_hp,static_cast<float>(full.clear),1,raw,loss,2000,2*raw);
        const auto fresh=siege::quote(units[u].max_hp,units[u].max_hp,static_cast<float>(full.clear),1,raw,loss,2000,2*raw);
        if(!fresh.valid||fresh.attacks<1)return {};
        if(current.attacks>0)result.ready|=1u<<u;
        capacity=std::min(capacity,current.attacks);recovered=std::min(recovered,fresh.attacks);
    }
    result.attacks=capacity;
    result.waves=1+(std::max(0,full.clear-capacity)+recovered-1)/recovered;
    const long long finish=static_cast<long long>(full.finish)+(result.waves-1)*static_cast<long long>(heal);
    if(finish>2000)return {};
    result.finish=finish;result.complete=true;return result;
}
// Compare the actual earliest melee target with the maximum-effective-HP tank.
// Always choosing the latter could discard an earlier-handle melee damage
// dealer and make a useful two-body clear disappear. Rank roles with full HP
// so transient damage cannot flip the tank/poses on every turn; current HP is
// still checked by the caller before any wake or attack commitment.
template<class Walkable,class Home,class Budget=Unlimited>
Formation choose(std::span<const Unit> units,std::span<const Monster> camps,unsigned focus,Walkable walkable,Home home,Budget budget={}) {
    if(units.empty()||units.size()>max_units)return {};
    unsigned melee=max_units,robust=0;
    std::array<Unit,max_units> full{};
    for(unsigned u=0;u<units.size();++u) {
        full[u]=units[u];full[u].hp=full[u].max_hp;
        if(units[u].range==1&&(melee==max_units||units[u].handle<units[melee].handle))melee=u;
        if(units[u].max_hp/units[u].factor>units[robust].max_hp/units[robust].factor||
            (units[u].max_hp/units[u].factor==units[robust].max_hp/units[robust].factor&&units[u].handle<units[robust].handle))robust=u;
    }
    Formation result;int fastest=2001;unsigned most=0,previous=max_units;bool survives=false;
    for(unsigned candidate:{melee<max_units?melee:robust,robust}) {
        if(candidate==previous)continue;previous=candidate;
        const auto proposal=arrange(units,camps,focus,walkable,home,budget,candidate);
        const auto quote=forecast(std::span<const Unit>(full.data(),units.size()),camps,proposal,0,6,2000,budget);
        if(!quote.complete)continue;
        const unsigned count=std::popcount(proposal.active);
        // A complete contributing lineup is executable even when it needs
        // recovery visits. Do not spend its entire budget trying to replace
        // the first melee tank with one that would exclude that actor.
        if(count==units.size())return proposal;
        if(!result.valid||(quote.survivable&&!survives)||(quote.survivable==survives&&
            (quote.finish<fastest||(quote.finish==fastest&&count>most)||
            (quote.finish==fastest&&count==most&&units[candidate].handle<units[result.tank].handle)))) {
            result=proposal;fastest=quote.finish;most=count;survives=quote.survivable;
        }
    }
    return result;
}
}
