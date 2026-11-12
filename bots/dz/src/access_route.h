#pragma once
#include "camp_threat.h"
#include <array>

namespace dz::access {
// The ledger restores DESIGN HP during a known respawn interval. Those HP are
// not a live occupant. Price the intended arrival tick, not only the current
// tick; a camp due to respawn on that tick is conservatively blocking.
inline bool member_blocks(bool recorded_alive,bool respawning,int ready,int arrival) {
    return recorded_alive&&(!respawning||ready<=arrival);
}
enum class Status { Clear, Blocked, Unreachable, Unknown };
struct Blocker { int group=-1,member=-1;float work=0; };
struct Route { Status status=Status::Unknown;Blocker blocker;int steps=0;Tile tile{},previous{}; };
struct Unlimited { bool operator()() const { return true; } };
// Follow a shortest static route, checking every occupied camp cell in order.
// A dead cell on a pocket boundary is not proof that deeper layers are open.
// Unknown means the bounded scan stopped, never a declaration of reachability.
template<class Distance,class Blocking,class Budget=Unlimited>
Route inspect(Tile start,Distance distance,Blocking blocking,Budget budget={},int maximum_steps=32) {
    Tile p=start;int current=distance(p);
    if(current<0||current>=65535)return {Status::Unreachable,{},0,p};
    for(int step=0;step<=maximum_steps;++step) {
        if(current==0)return {Status::Clear,{},step,p};
        if(step==maximum_steps||!budget())return {Status::Unknown,{},step,p};
        Tile next=p;int shortest=current;Blocker chosen;float cost=1e30f;
        for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy) {
            if(!dx&&!dy)continue;
            const Tile q{p.x+dx,p.y+dy};const int d=distance(q);
            if(d<0||d>=current||d>shortest)continue;
            const auto obstacle=blocking(q);const float work=obstacle.group>=0?obstacle.work+1:0;
            if(d<shortest||work<cost){next=q;shortest=d;chosen=obstacle;cost=work;}
        }
        if(shortest>=current)return {Status::Unknown,{},step,p};
        if(chosen.group>=0)return {Status::Blocked,chosen,step+1,next,p};
        p=next;current=shortest;
    }
    return {};
}
// Enumerate ALL blocking members on one descending static route in a single
// bounded pass. The callback returns false on capacity/unsupported knowledge.
// An incomplete scan never publishes a complete access itinerary.
template<class Distance,class Blocking,class Record,class Budget=Unlimited>
Route itinerary(Tile start,Distance distance,Blocking blocking,Record record,Budget budget={},int maximum_steps=128) {
    Tile p=start;int current=distance(p);
    if(current<0||current>=65535)return {Status::Unreachable,{},0,p};
    for(int step=0;step<=maximum_steps;++step) {
        if(current==0)return {Status::Clear,{},step,p};
        if(step==maximum_steps||!budget())return {Status::Unknown,{},step,p};
        Tile next=p;int shortest=current;Blocker chosen;float cost=1e30f;
        for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy) {
            if(!dx&&!dy)continue;
            const Tile q{p.x+dx,p.y+dy};const int d=distance(q);
            if(d<0||d>=current||d>shortest)continue;
            const auto obstacle=blocking(q);const float work=obstacle.group>=0?obstacle.work+1:0;
            if(d<shortest||work<cost){next=q;shortest=d;chosen=obstacle;cost=work;}
        }
        if(shortest>=current)return {Status::Unknown,{},step,p};
        if(!record(chosen,p,next,step+1))return {Status::Unknown,chosen,step+1,next,p};
        p=next;current=shortest;
    }
    return {};
}
struct ApproachCut { Blocker blocker;Tile tile,approach;int arrival=0; };
struct ApproachPlan { Status status=Status::Unknown;std::array<ApproachCut,12> cuts{};unsigned count=0; };
// Trace from the attack endpoint back to Home, then reverse the blockers.
// Each prerequisite is attacked from its HOME side, not the still-closed side.
// Publish only after the entire bounded route and cut list are complete.
struct ApproachSearch {
    std::array<Tile,129> path{};std::array<Blocker,128> blockers{};unsigned n=0;bool active=false;
    Tile cursor{};
    void begin(Tile endpoint){n=0;active=true;cursor=endpoint;path[0]=endpoint;}
    template<class Distance,class Blocking,class Budget=Unlimited>
    ApproachPlan advance(Distance home,Blocking blocking,Budget budget={},int slice=8) {
        if(!active)return {};
        bool full=false;
        const auto route=itinerary(cursor,home,blocking,[&](Blocker b,Tile,Tile tile,int) {
            if(n==blockers.size()){full=true;return false;}
            blockers[n]=b;path[++n]=tile;return true;
        },budget,slice);
        cursor=route.tile;ApproachPlan result;
        if(full){active=false;result.status=Status::Unreachable;return result;}
        if(route.status!=Status::Clear){if(route.status==Status::Unreachable)active=false;result.status=route.status;return result;}
        for(unsigned i=n;i>0;--i)if(blockers[i-1].group>=0) {
            if(i==n||result.count==result.cuts.size()){active=false;return {};}
            result.cuts[result.count++]={blockers[i-1],path[i],path[i+1],home(path[i+1])};
        }
        active=false;result.status=Status::Clear;return result;
    }
};
template<class Distance,class Blocking,class Budget=Unlimited>
ApproachPlan approach_cuts(Tile endpoint,Distance home,Blocking blocking,Budget budget={}) {
    ApproachSearch search;search.begin(endpoint);return search.advance(home,blocking,budget,128);
}
}
