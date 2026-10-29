#pragma once
#include "core.h"
#include <numeric>
#include <optional>
#include <stdexcept>
#include <vector>

namespace dz {
struct GroupSample {
    GroupState state = GroupState::Alive;
    int respawn_timer=0, capture_timer=65535;
    std::vector<std::optional<float>> members;
};
inline void apply_group_sample(GroupBelief& belief,std::vector<float>& hp,const std::vector<float>& initial,
                               const GroupSample& sample,int round) {
    if (hp.size()!=initial.size()||sample.members.size()!=initial.size()) throw std::logic_error("camp ledger member mismatch");
    bool new_generation=belief.state==GroupState::Reward||belief.state==GroupState::Respawning;
    if (std::all_of(hp.begin(),hp.end(),[](float value){return value<=0;})) new_generation=true;
    for (unsigned i=0;i<hp.size();++i) if (sample.members[i]&&*sample.members[i]>hp[i]+.01f) new_generation=true;
    if (sample.state==GroupState::Respawning) {
        hp=initial; belief.state=GroupState::Respawning;
        belief.ready=round+sample.respawn_timer; belief.capture=65535;
        belief.failures=0; // Someone completed it; earlier failures are stale.
    } else if (sample.state==GroupState::Reward) {
        std::fill(hp.begin(),hp.end(),0); belief.state=GroupState::Reward;
        belief.capture=sample.capture_timer;
    } else {
        if (new_generation) hp=initial;
        for (unsigned i=0;i<hp.size();++i) if (sample.members[i]) hp[i]=*sample.members[i];
        const auto total=std::accumulate(hp.begin(),hp.end(),0.f);
        const auto maximum=std::accumulate(initial.begin(),initial.end(),0.f);
        belief.state=total+.01f<maximum ? GroupState::Partial : GroupState::Alive;
        belief.capture=65535;
    }
    belief.hp=std::accumulate(hp.begin(),hp.end(),0.f); belief.seen=round;
}
}
