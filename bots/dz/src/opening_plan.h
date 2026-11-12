#pragma once
#include "allocation.h"

namespace dz::opening {
inline constexpr int horizon=120;
inline constexpr unsigned max_legs=objective::max_crew*8;
struct Leg {
    unsigned slot=6;int from=-1,to=-1,first_finish=0,travel=0,work=0;
    float value=0;unsigned first_generation=0,next_generation=0;
};
struct Route {
    int first=-1,next=-1,finish=0;unsigned first_generation=0,next_generation=0;
    bool valid() const {return first>=0&&next>=0&&first!=next&&finish>0;}
};
// Extend the actual immediate auction, rather than sell its first reward a
// second time. Every first job is excluded from the residual matching, and
// every next job/worker is used once. The extension adds no speculative bonus
// to the immediate auction. It is contingent on the later ownership check.
template<class Budget=economy::UnlimitedAuction>
std::array<Route,objective::max_crew> extend(const std::array<economy::Assignment,objective::max_crew>& first,
    std::span<const Leg> legs,int remaining,Budget budget={}) {
    std::array<Route,objective::max_crew> result{};
    if(remaining<=0||remaining>horizon||legs.size()>max_legs)return result;
    std::array<economy::Bid,max_legs> bids{};std::array<const Leg*,max_legs> source{};unsigned count=0,available=0;
    for(const auto& leg:legs) {
        if(!budget())return {};
        if(leg.slot>=first.size()||leg.from<0||leg.to<0||leg.to>=112||leg.from==leg.to||
            first[leg.slot].objective!=leg.from||first[leg.slot].crew!=(1u<<leg.slot)||first[leg.slot].capturer!=leg.slot||
            leg.first_finish<=0||leg.travel<0||leg.work<=0||!std::isfinite(leg.value)||leg.value<=0||
            leg.first_finish>remaining||leg.travel>remaining-leg.first_finish||leg.work>remaining-leg.first_finish-leg.travel)continue;
        if(std::any_of(first.begin(),first.end(),[&](const auto& job){return job.objective==leg.to;}))continue;
        source[count]=&leg;bids[count++]={leg.to,1u<<leg.slot,leg.slot,leg.value,static_cast<float>(leg.travel+leg.work)};
        available|=1u<<leg.slot;
    }
    const auto second=economy::allocate(std::span<const economy::Bid>(bids.data(),count),available,budget);
    for(unsigned s=0;s<result.size();++s)if(second[s].objective>=0) {
        const Leg* best=nullptr;float rate=-1;
        for(unsigned i=0;i<count;++i) {const auto& leg=*source[i];if(leg.slot==s&&leg.to==second[s].objective) {
            const float value=leg.value/(leg.travel+leg.work);
            if(value>rate){best=&leg;rate=value;}
        }}
        if(best)result[s]={best->from,best->to,best->first_finish+best->travel+best->work,best->first_generation,best->next_generation};
    }
    return result;
}
struct Commitment {
    Route route;int deadline=-1,bag=0,gold=0;bool joined=false;
    bool active() const {return route.valid()&&!joined&&deadline>=0;}
    bool start(Route value,int now,int carried,int cash) {
        if(!value.valid()||now<0||now>=horizon||value.finish>horizon-now||carried<0||cash<0)return false;
        *this={value,horizon,carried,cash,false};return true;
    }
    // Completion is an observed generation change plus our actual receipt.
    // A teammate's capture does not grant us a fictional opening payout.
    bool ready(int now,unsigned generation,int carried,int cash) const {
        return active()&&now<deadline&&generation>route.first_generation&&(carried>bag||cash>gold);
    }
    bool current(int now,int objective,unsigned generation) const {
        return active()&&now>=0&&now<deadline&&objective==route.first&&generation==route.next_generation;
    }
};
}
