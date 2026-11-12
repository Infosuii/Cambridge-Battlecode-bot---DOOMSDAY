#pragma once
#include "basic_clear.h"
#include <algorithm>

namespace dz {
// Restricted elapsed attack clock: stationary, one basic per turn plus one
// available reset on the SAME surviving target, one cast per turn. Movement,
// other spells/actors and changing damage are outside this model. Keep the
// conservative damage/survival gate separate from this timing estimate.
struct TimedAttackJob { std::uint32_t attacks=0;bool refresh_on_kill=false; };
struct AttackClock {
    WorkStatus status=WorkStatus::Invalid;
    std::uint32_t rounds=0,resets=0,remaining_cooldown=0;
    bool complete() const { return status==WorkStatus::Complete; }
};
inline AttackClock attack_clock(std::span<const TimedAttackJob> jobs,
                               std::uint32_t remaining,std::uint32_t period) {
    if(jobs.size()>64||remaining>2000||period>2000||(!period&&remaining))return {};
    std::uint32_t work=0,rounds=0,resets=0,cd=remaining;
    for(auto job:jobs) {
        if(job.attacks>2000-work)return {WorkStatus::BeyondHorizon,0,0,cd};
        work+=job.attacks;
    }
    for(auto job:jobs) {
        auto n=job.attacks;
        if(!n)continue;
        if(!period) { rounds+=n;continue; }
        const auto ordinary=std::min(n,cd);
        n-=ordinary;rounds+=ordinary;cd-=ordinary;
        if(n) {
            // From ready: each complete period supplies period+1 attacks.
            const auto cycles=n/(period+1);
            rounds+=cycles*period;resets+=cycles;n%=period+1;
            if(n==1)++rounds; // First attack kills: no reset may be cast.
            else if(n>=2) { rounds+=n-1;++resets;cd=period-(n-1); }
        }
        if(job.refresh_on_kill)cd=0;
    }
    return {WorkStatus::Complete,rounds,resets,cd};
}
}
