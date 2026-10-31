#pragma once
#include "objective_model.h"

namespace dz::economy {
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
// Bounded set-packing auction: tasks and champions are exclusive. Crew bids pay
// the best foregone SOLO income of each helper. Thus a pair must earn back the
// work it prevents elsewhere; fixed pairs and whole-team grouping do not.
inline std::array<Assignment,objective::max_crew> allocate(std::span<const Bid> bids,unsigned available) {
    std::array<Assignment,objective::max_crew> result{};
    std::array<int,objective::max_crew> used{};unsigned count=0;
    for(unsigned turn=0;turn<objective::max_crew&&available;++turn) {
        const Bid* best=nullptr;
        for(const auto& bid:bids) {
            if(bid.objective<0||bid.crew==0||(bid.crew&~available)||bid.capturer>=objective::max_crew||
                !(bid.crew&(1u<<bid.capturer))||!std::isfinite(bid.value)||!std::isfinite(bid.duration)||
                !std::isfinite(bid.opportunity)||!std::isfinite(bid.followup)||bid.duration<=0||bid.value<=0) continue;
            if(std::find(used.begin(),used.begin()+count,bid.objective)!=used.begin()+count) continue;
            if(!best||bid.utility()>best->utility()||
                (bid.utility()==best->utility()&&(bid.objective<best->objective||
                (bid.objective==best->objective&&bid.crew<best->crew)))) best=&bid;
        }
        if(!best||best->utility()<=0) break;
        used[count++]=best->objective;
        for(unsigned i=0;i<result.size();++i) if(best->crew&(1u<<i))
            result[i]={best->objective,best->crew,best->capturer,best->utility()};
        available&=~best->crew;
    }
    return result;
}
}
