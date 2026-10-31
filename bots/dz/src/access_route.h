#pragma once
#include "camp_threat.h"

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
}
