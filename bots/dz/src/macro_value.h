#pragma once
#include <algorithm>
#include <cmath>
#include <limits>
#include <span>

namespace dz::macro {
enum class Kind { Farm, Bank, Shop, Recover, Gate, Wait };
struct Context {
    int horizon=0;
    float bag=0, income=0, gold_price=0;
    float gold_income=0;
};
// A one-job rollout followed by the same continuation rate. All alternatives
// account for delivery of the EXISTING bag; it is not a new reward for banking.
// Equipment benefit and risk cost are explicit GE estimates supplied by the
// adapter, not calibrated probabilities. Unknown delivery earns no terminal
// gems. A quote may still earn gold if its capture precedes the horizon.
struct Option {
    Kind kind=Kind::Wait;
    int id=-1, work=0, delivery=-1;
    float gems=0, gold=0, equipment=0, risk_cost=0;
    bool feasible=false;
};
inline float value(const Context& c,const Option& q) {
    constexpr float invalid=-std::numeric_limits<float>::infinity();
    if(!q.feasible||c.horizon<=0||q.work<0||q.delivery< -1||
        !std::isfinite(c.bag)||c.bag<0||!std::isfinite(c.income)||c.income<0||
        !std::isfinite(c.gold_price)||c.gold_price<0||!std::isfinite(c.gold_income)||c.gold_income<0)return invalid;
    for(auto x:{q.gems,q.gold,q.equipment,q.risk_cost})if(!std::isfinite(x)||x<0)return invalid;
    if(q.work>c.horizon)return invalid;
    const auto finish=static_cast<long long>(q.work)+std::max(0,q.delivery);
    const bool delivered=q.delivery>=0&&finish<=c.horizon;
    // Future income also needs a known delivery route. If access is closed,
    // only current gold/progression benefits can be certified by this rollout.
    const float future=(delivered?c.income:0)*std::max(0LL,c.horizon-finish)+
        c.gold_price*c.gold_income*std::max(0LL,c.horizon-finish);
    const float result=(delivered?c.bag+q.gems:0)+c.gold_price*q.gold+q.equipment+future-q.risk_cost;
    return std::isfinite(result)?result:invalid;
}
inline int choose(const Context& c,std::span<const Option> options,int incumbent=-1,int switch_rounds=1) {
    int best=-1;float score=-std::numeric_limits<float>::infinity();
    for(unsigned i=0;i<options.size();++i) {
        auto v=value(c,options[i]);
        // Switching costs one explicit productive round, not a large sticky
        // multiplier that can retain an exhausted or impossible objective.
        if(static_cast<int>(i)!=incumbent)v-=(c.income+c.gold_price*c.gold_income)*std::max(0,switch_rounds);
        if(v>score){score=v;best=static_cast<int>(i);}
    }
    return best;
}
}
