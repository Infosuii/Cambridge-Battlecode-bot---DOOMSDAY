#pragma once
#include "attack_clock.h"
#include <array>

namespace dz {
struct TimedDamageJob { TimedAttackJob attack;float incoming=0; };
struct TimedClearDamage { AttackClock clock;double damage=0; };
// Diagnostic stationary model, sampled after this turn's camp phase. Every
// living camp hits this body each subsequent phase until its elimination.
// Reset timing changes exposure by mechanism, without a fitted discount.
// No movement, other actors, splash, shields, spells or changing damage.
inline TimedClearDamage timed_clear_damage(std::span<const TimedDamageJob> jobs,
                                           unsigned remaining,unsigned period) {
    if(jobs.size()>64)return {};
    std::array<TimedAttackJob,64> attacks;
    for(unsigned k=0;k<jobs.size();++k) {
        if(!std::isfinite(jobs[k].incoming)||jobs[k].incoming<0)return {};
        attacks[k]=jobs[k].attack;
    }
    const auto clock=attack_clock(std::span<const TimedAttackJob>(attacks.data(),jobs.size()),remaining,period);
    if(!clock.complete())return {clock,0};
    unsigned elapsed=0,cd=remaining;double loss=0;
    for(const auto& job:jobs) {
        if(!job.attack.attacks)continue;
        const auto part=attack_clock(std::span<const TimedAttackJob>(&job.attack,1),cd,period);
        if(!part.complete())return {part,0};
        elapsed+=part.rounds;cd=part.remaining_cooldown;
        loss+=static_cast<double>(job.incoming)*(elapsed-1);
    }
    return {clock,loss};
}
}
