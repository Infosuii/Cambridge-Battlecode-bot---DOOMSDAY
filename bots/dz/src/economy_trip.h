#pragma once
#include "macro_value.h"
#include <array>

namespace dz::trip {
inline constexpr unsigned max_jobs=3,max_nodes=6;
inline constexpr int unreachable=65535;
struct Node {
    int id=-1,work=0,ready=0;
    float gems=0,gold=0,exposure=0;
};
struct Network {
    unsigned count=0;
    std::array<Node,max_nodes> nodes{};
    std::array<int,max_nodes> arrival{},delivery{};
    std::array<std::array<int,max_nodes>,max_nodes> travel{};
};
struct Plan {
    unsigned count=0;
    std::array<int,max_jobs> jobs{{-1,-1,-1}},ends{};
    int finish=0,altar=-1;
    bool shop=false;
    macro::Option option;
};
// Enumerate small complete circuits with a compulsory first job and a real bank
// leg. No repeated objective or speculative respawn reward. Static travel is an
// estimate; runtime occupancy/admission still owns executable safety.
template<class BankTime,class Budget>
Plan best(const macro::Context& c,const Network& n,unsigned first,int altar,BankTime bank_time,Budget budget) {
    Plan result;
    if(!n.count||n.count>max_nodes||first>=n.count||altar<0||c.horizon<1||c.horizon>2000)return result;
    for(unsigned i=0;i<n.count;++i) {
        const auto& node=n.nodes[i];
        if(node.id<0||node.work<0||node.ready<0||!std::isfinite(node.gems)||node.gems<0||
            !std::isfinite(node.gold)||node.gold<0||!std::isfinite(node.exposure)||node.exposure<0||node.exposure>1)return result;
        for(unsigned j=0;j<i;++j)if(node.id==n.nodes[j].id)return result;
    }
    std::array<unsigned,max_jobs> path{};
    float winner=-std::numeric_limits<float>::infinity();bool exhausted=false;
    auto visit=[&](auto&& recurse,unsigned index,unsigned used,unsigned depth,int elapsed,float gems,float gold,float risk)->void {
        if(exhausted)return;
        if(!budget()){exhausted=true;return;}
        const auto& node=n.nodes[index];
        const int travel=depth?n.travel[path[depth-1]][index]:n.arrival[index];
        if(travel<0||travel>=unreachable||elapsed>c.horizon-travel)return;
        elapsed=std::max(elapsed+travel,node.ready);
        if(node.work>c.horizon-elapsed)return;
        elapsed+=node.work;path[depth]=index;
        risk+=node.exposure*(c.bag+gems);gems+=(1-node.exposure)*node.gems;gold+=(1-node.exposure)*node.gold;
        const int bank=bank_time(c.bag+gems);
        if(n.delivery[index]>=0&&n.delivery[index]<unreachable&&bank>=0&&bank<unreachable) {
            macro::Option option{macro::Kind::Farm,n.nodes[first].id,elapsed,n.delivery[index]+bank,gems,gold,0,risk,true};
            const auto score=macro::value(c,option);
            // Stable short-route ties prevent unnecessary extra jobs/claims.
            if(score>winner&&static_cast<long long>(elapsed)+option.delivery<=c.horizon) {
                winner=score;result.count=depth+1;result.finish=elapsed+option.delivery;result.altar=altar;result.option=option;
                int time=0;
                for(unsigned k=0;k<=depth;++k) {
                    const unsigned u=path[k];time=std::max(time+(k?n.travel[path[k-1]][u]:n.arrival[u]),n.nodes[u].ready)+n.nodes[u].work;
                    result.jobs[k]=n.nodes[u].id;result.ends[k]=time;
                }
            }
        }
        if(depth+1==max_jobs)return;
        for(unsigned next=0;next<n.count;++next)if(!(used&(1u<<next)))recurse(recurse,next,used|(1u<<next),depth+1,elapsed,gems,gold,risk);
    };
    visit(visit,first,1u<<first,0,0,0,0,0);
    // A partial search is a useful feasible circuit, not a claim of optimality.
    return result;
}
enum class Phase { Idle, Work, Deliver, Shop };
struct Commitment {
    Plan plan;
    unsigned next=0;
    Phase phase=Phase::Idle;
    int started=0,deadline=0,initial_bag=0,grace=0;
    std::array<int,max_jobs> generations{};
    bool active() const {return phase!=Phase::Idle;}
    int job() const {return phase==Phase::Work&&next<plan.count?plan.jobs[next]:-1;}
    void start(const Plan& quote,int round,int bag,int slack) {
        *this={};if(!quote.count||quote.count>max_jobs||quote.altar<0||quote.finish<1)return;
        plan=quote;started=round;grace=std::max(0,slack);deadline=round+quote.finish+grace;initial_bag=bag;phase=Phase::Work;
    }
    // Absolute deadlines never slide when a new forecast is produced. Income
    // from an unrelated kill is not evidence that the assigned camp converted.
    void advance(int round,int bag,bool converted,bool available,bool at_home=false) {
        if(!active())return;
        if(bag<initial_bag&&phase==Phase::Work){*this={};return;}
        if(phase==Phase::Shop){if(at_home)*this={};return;}
        if(phase==Phase::Deliver){if(bag==0)phase=plan.shop?Phase::Shop:Phase::Idle;return;}
        if(round>deadline||round>started+plan.ends[next]+grace){if(bag>0)phase=Phase::Deliver;else *this={};return;}
        if(converted||!available) {
            ++next;
            if(next==plan.count)phase=bag>0?Phase::Deliver:plan.shop?Phase::Shop:Phase::Idle;
        }
    }
};
}
