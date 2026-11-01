#pragma once
#include "camp_threat.h"
#include <array>
#include <cstdint>
#include <limits>

namespace dz::bank {
inline constexpr unsigned max_threats=64,max_cuts=8;
struct AdmissionStamp {
    int round=-1,altar=-1,bag=0;Tile tile;float hp=0;
    bool current(int now,int endpoint,Tile p,float health,int carried) const {
        return round==now&&altar==endpoint&&tile==p&&bag==carried&&std::isfinite(health)&&health>=hp&&hp>0;
    }
};
struct Stamp {
    int round=-10000,channel=-1,until=2000;
    unsigned revision=~0u,threat_revision=~0u;
    float max_hp=0,factor=0;
    bool current(int now,unsigned topology,unsigned threats,float health,float mitigation,int duration) const {
        return now>=round&&now-round<until&&revision==topology&&threat_revision==threats&&
            std::isfinite(health)&&health>0&&std::isfinite(mitigation)&&mitigation>=0&&
            max_hp==health&&factor==mitigation&&channel==duration&&duration>=0;
    }
};
struct Delivery {
    int altar=-1,bag=0,deadline=0;
    bool active() const {return altar>=0;}
    bool start(int endpoint,int now,int carried,int window) {
        if(active()||endpoint<0||now<0||now>2000||carried<=0||window<=0||window>2000-now)return false;
        altar=endpoint;bag=carried;deadline=now+window;return true;
    }
    bool update(int now,int carried,int finish) {
        if(!active())return false;
        if(now<0||now>deadline||carried<bag||carried<=0||finish<0||finish>deadline-now){*this={};return false;}
        return true;
    }
};
struct Context {
    float hp=0,max_hp=0,shield=0;
    int shield_rounds=0,channel=0,horizon=2000;
};
struct Threat { int group=-1,member=-1;CampThreat camp;float clear_time=0;bool future=false; };
struct Root { Tile tile;int distance=0;EscapeRoute escape;int until=2000;std::uint64_t required=0; };
struct Expiry {Tile tile;int until=0;};
inline int root_deadline(const Root& root,std::span<const Expiry> empty) {
    int until=root.until;
    for(auto cell:empty) {
        if(cell.tile==root.tile)until=std::min(until,cell.until);
        if(!root.escape.found)continue;
        const int length=cheb(root.tile,root.escape.exit),step=cheb(root.tile,cell.tile);
        const int dx=(root.escape.exit.x>root.tile.x)-(root.escape.exit.x<root.tile.x),dy=(root.escape.exit.y>root.tile.y)-(root.escape.exit.y<root.tile.y);
        if(step>0&&step<=length&&cell.tile==Tile{root.tile.x+dx*step,root.tile.y+dy*step})
            until=std::min(until,cell.until-length); // Pay the full post-channel exit.
    }
    return until;
}
enum class Quality { Unknown, Bounded, Cuts, Invalid };
struct Plan {
    Quality quality=Quality::Unknown;Tile root;
    std::array<unsigned,max_cuts> cuts{};unsigned count=0;
    float work=0,loss=0;int travel=0;
    unsigned root_index=~0u;
    bool complete() const {return quality==Quality::Bounded||quality==Quality::Cuts;}
};
inline float channel_loss(const Context& c,float raw,float escape) {
    if(!std::isfinite(raw)||raw<0||!std::isfinite(escape)||escape<0||c.channel<0||c.channel>2000||c.shield_rounds<0||
        !std::isfinite(c.hp)||!std::isfinite(c.max_hp)||!std::isfinite(c.shield)||c.hp<=0||c.hp>c.max_hp||c.shield<0)
        return std::numeric_limits<float>::infinity();
    const int phases=c.channel+1; // Pay the initialization camp phase too.
    const float credit=std::min(c.shield,raw*std::min(phases,c.shield_rounds));
    return raw*phases-credit+1.25f*escape+.15f*c.max_hp;
}
inline float residual_damage(Tile tile,std::span<const Threat> threats,std::uint64_t removed) {
    float raw=0;
    for(unsigned i=0;i<threats.size();++i)if(!(removed&(std::uint64_t{1}<<i))&&cheb(tile,threats[i].camp.p)<=threats[i].camp.range)
        raw+=threats[i].camp.strength;
    return raw;
}
// Hypothetical exits carry ALL occupancy cuts needed along their straight ray.
// Damage is repriced after that complete cut set is known. These are forecasts;
// the executor still requires a fresh, currently walkable escape certificate.
template<class Walkable,class Budget=UnlimitedEscapeBudget>
unsigned escape_roots(Tile tile,int distance,int until,std::span<const Threat> threats,std::span<Root> output,Walkable open,Budget budget={}) {
    if(threats.size()>max_threats||output.empty())return 0;
    std::uint64_t base=0;int range=0;
    for(unsigned i=0;i<threats.size();++i){if(threats[i].camp.p==tile)base|=std::uint64_t{1}<<i;range=std::max(range,threats[i].camp.range);}
    if(range<0||range>16)return 0;
    unsigned n=0;output[n++]={tile,distance,{},until,base};
    for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy) {
        if((!dx&&!dy)||n==output.size())continue;
        std::array<Tile,34> path{};std::uint64_t removed=base;
        for(int step=1;step<=2*range+2;++step) {
            if(!budget())return n;
            const Tile p{tile.x+dx*step,tile.y+dy*step};if(!open(p,step))break;
            path[step-1]=p;
            for(unsigned i=0;i<threats.size();++i)if(threats[i].camp.p==p)removed|=std::uint64_t{1}<<i;
            if(residual_damage(p,threats,removed)>0)continue;
            float loss=0;for(int k=0;k<step;++k)loss+=residual_damage(path[k],threats,removed);
            output[n++]={tile,distance,{p,loss,step,true},until,removed};break;
        }
    }
    return n;
}
// Conservative channel/exit accounting. Cut ranking uses clear-time estimates;
// actual multi-visit cuts are priced and admitted by the live opening controller.
// A budget stop preserves the best COMPLETE root prefix, never a partial cut set.
template<class Budget=UnlimitedEscapeBudget>
Plan choose(const Context& context,std::span<const Threat> threats,std::span<const Root> roots,Budget budget={}) {
    Plan best;float cost=std::numeric_limits<float>::infinity();
    if(threats.size()>max_threats||context.horizon<=0||context.horizon>2000||
        !std::isfinite(channel_loss(context,0,0))){best.quality=Quality::Invalid;return best;}
    for(auto t:threats)if(t.group<0||t.member<0||!std::isfinite(t.clear_time)||t.clear_time<=0||
        !std::isfinite(t.camp.strength)||t.camp.strength<0||t.camp.range<0){best.quality=Quality::Invalid;return best;}
    int minimum=65535;for(auto root:roots)if(root.distance>=0)minimum=std::min(minimum,root.distance);
    // Prove the common zero-cut lower bound before sorting hypothetical cuts.
    // Dense harmless resources otherwise spent the entire slice before even
    // considering a free submission root.
    for(unsigned r=0;r<roots.size();++r) {
        if(!budget())return best;const auto& root=roots[r];
        if(root.required||root.distance<0||root.distance>=65535||root.distance+context.channel+1>std::min(context.horizon,root.until))continue;
        bool clear=true;
        for(unsigned i=0;i<threats.size();++i) {
            if((i&7u)==0&&!budget())return best;
            if(threats[i].camp.p==root.tile||(threats[i].camp.strength>0&&cheb(root.tile,threats[i].camp.p)<=threats[i].camp.range)){clear=false;break;}
        }
        const float finish=root.distance+context.channel+1;
        if(clear&&finish<cost){best.quality=Quality::Bounded;best.root=root.tile;best.travel=root.distance;best.root_index=r;cost=finish;
            if(root.distance==minimum)return best;}
    }
    std::array<unsigned,max_threats> order{};for(unsigned i=0;i<threats.size();++i)order[i]=i;
    std::sort(order.begin(),order.begin()+threats.size(),[&](auto a,auto b) {
        const float x=threats[a].camp.strength/threats[a].clear_time,y=threats[b].camp.strength/threats[b].clear_time;
        return x>y||(x==y&&a<b);
    });
    for(unsigned r=0;r<roots.size();++r) {const auto& root=roots[r];
        if(!budget())return best;
        if(root.distance<0||root.distance>=65535)continue;
        if(threats.size()<64&&(root.required>>threats.size()))continue;
        Plan candidate;candidate.root=root.tile;candidate.travel=root.distance;candidate.root_index=r;
        std::uint64_t removed=0;float raw=0;
        auto cut=[&](unsigned i) {
            if(candidate.count==candidate.cuts.size())return false;
            removed|=std::uint64_t{1}<<i;candidate.cuts[candidate.count++]=i;candidate.work+=threats[i].clear_time;return true;
        };
        bool supported=true;
        for(unsigned i=0;i<threats.size();++i) {
            if((i&7u)==0&&!budget())return best;
            if((threats[i].camp.p==root.tile||(root.required&(std::uint64_t{1}<<i)))&&!cut(i)){supported=false;break;}
            if(cheb(root.tile,threats[i].camp.p)<=threats[i].camp.range)raw+=threats[i].camp.strength;
        }
        if(!supported)continue;
        for(unsigned i=0;i<threats.size();++i)if((removed&(std::uint64_t{1}<<i))&&cheb(root.tile,threats[i].camp.p)<=threats[i].camp.range)
            raw-=threats[i].camp.strength;
        auto loss=[&] {return raw<=0?0.f:root.escape.found?channel_loss(context,raw,root.escape.damage):std::numeric_limits<float>::infinity();};
        for(unsigned k=0;k<threats.size()&&context.hp<=loss();++k) {
            if((k&7u)==0&&!budget())return best;
            const auto i=order[k];
            if((removed&(std::uint64_t{1}<<i))||cheb(root.tile,threats[i].camp.p)>threats[i].camp.range||threats[i].camp.strength<=0)continue;
            if(!cut(i)){supported=false;break;}raw=std::max(0.f,raw-threats[i].camp.strength);
        }
        candidate.loss=loss();
        const float finish=candidate.work+root.distance+context.channel+1;
        if(!supported||context.hp<=candidate.loss||finish>std::min(context.horizon,root.until))continue;
        if(finish<cost){cost=finish;candidate.quality=candidate.count?Quality::Cuts:Quality::Bounded;best=candidate;}
    }
    return best;
}
}
