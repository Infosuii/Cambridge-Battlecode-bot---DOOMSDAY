#pragma once
#include "objective_model.h"
#include "protocol.h"
#include <bit>

namespace dz::economy {
constexpr bool available_for_offer(unsigned intent,bool healthy_at_home) {
    return (intent!=protocol::shop&&intent!=protocol::retreat)||healthy_at_home;
}
constexpr bool starved(int round,int income_round,int work_round,int window=150) {
    return round-std::max(income_round,work_round)>window;
}
constexpr unsigned next_coalition_size(unsigned tested,unsigned eligible) {
    return eligible<=2||tested>=eligible?2:tested+1;
}
struct Bid {
    int objective=-1;
    unsigned crew=0, capturer=0;
    float value=0, duration=1, opportunity=0, followup=0;
    float utility() const { return value/std::max(1.f,duration)-opportunity+followup; }
};
struct Assignment { int objective=-1;unsigned crew=0,capturer=0;float utility=0; };
struct UnlimitedAuction { bool operator()() const {return true;} };
// Exact immediate-task set packing on six champion bits. Process each objective
// as a batch, so a camp is never sold to two different crews. Foregone solo work
// is priced by the best feasible disjoint assignment, not by adding mutually
// exclusive solo rates for the SAME camp. A budget stop keeps a feasible prefix;
// only an untruncated search is an optimum for the supplied bid estimates.
template<class Budget=UnlimitedAuction>
std::array<Assignment,objective::max_crew> allocate(std::span<const Bid> bids,unsigned available,Budget budget={}) {
    std::array<Assignment,objective::max_crew> result{};
    constexpr unsigned masks=1u<<objective::max_crew;
    if(!budget())return result;
    available&=masks-1;unsigned bits=0;std::array<unsigned,objective::max_crew> local{};
    for(unsigned slot=0;slot<objective::max_crew;++slot)if(available&(1u<<slot))local[slot]=1u<<bits++;
    const unsigned size=1u<<bits;
    struct State { float value;unsigned count;std::array<const Bid*,objective::max_crew> jobs; };
    std::array<State,masks> states,next;
    for(unsigned i=0;i<size;++i)states[i]={-1,0,{}};
    states[0].value=0;
    std::array<int,112> processed{};unsigned groups=0;bool stopped=false;
    for(const auto& head:bids) {
        if(head.objective<0||head.objective>=112||std::find(processed.begin(),processed.begin()+groups,head.objective)!=processed.begin()+groups)continue;
        if(!budget())break;
        processed[groups++]=head.objective;
        // Copy only the active subset table. Copying all 64 states for every
        // camp consumed most of a native turn even with just two free actors.
        std::copy_n(states.begin(),size,next.begin());
        for(const auto& bid:bids) {
            if(bid.objective!=head.objective||bid.crew==0||(bid.crew&~available)||bid.capturer>=objective::max_crew||
                !(bid.crew&(1u<<bid.capturer))||!std::isfinite(bid.value)||!std::isfinite(bid.duration)||
                !std::isfinite(bid.opportunity)||!std::isfinite(bid.followup)||bid.duration<=0||bid.value<=0||bid.utility()<=0)continue;
            if(!budget()){stopped=true;break;}
            unsigned crew=0;
            for(unsigned slot=0;slot<objective::max_crew;++slot)if(bid.crew&(1u<<slot))crew|=local[slot];
            const unsigned free=(size-1)&~crew;unsigned steps=0;
            for(unsigned mask=free;;mask=(mask-1)&free) {
                if((++steps&7u)==0&&!budget()){stopped=true;break;}
                if(states[mask].value>=0&&states[mask].count<objective::max_crew) {
                    const unsigned combined=mask|crew;const float value=states[mask].value+bid.utility();
                    if(std::isfinite(value)&&value>next[combined].value) {
                        next[combined]=states[mask];next[combined].value=value;
                        next[combined].jobs[next[combined].count++]=&bid;
                    }
                }
                if(!mask)break;
            }
            if(stopped)break;
        }
        std::copy_n(next.begin(),size,states.begin());if(stopped)break;
    }
    unsigned best=0;
    for(unsigned mask=1;mask<size;++mask)if(states[mask].value>states[best].value||
        (states[mask].value==states[best].value&&std::popcount(mask)<std::popcount(best)))best=mask;
    for(unsigned j=0;j<states[best].count;++j) {
        const auto& job=*states[best].jobs[j];
        for(unsigned i=0;i<result.size();++i)if(job.crew&(1u<<i))result[i]={job.objective,job.crew,job.capturer,job.utility()};
    }
    return result;
}
}
