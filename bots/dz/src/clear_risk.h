#pragma once
#include "basic_clear.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <span>

namespace dz {
// Conservative solo-clear risk for objective selection. Extends the validated
// single-camp stationary duel to a group: every live member is assumed to hit
// the attacker every camp phase until it dies (members of a group are adjacent
// and their ranges are 3-5). No spells, resets, splash, healing or allies.
// This is a selection gate, not the calibrated ObjModel; V-M1 stays open.
struct ClearMember { float hp=0, incoming=0; };
struct ClearRisk {
    WorkStatus status=WorkStatus::Invalid;
    std::uint32_t attacks=0;
    double damage=0; // Future HP loss for a fresh engagement.
    bool complete() const { return status==WorkStatus::Complete; }
};
inline constexpr std::size_t clear_risk_members=64;
inline ClearRisk solo_clear_risk(std::span<const ClearMember> members,float damage_per_attack,std::uint32_t horizon=2000) {
    if (members.size()>clear_risk_members||horizon>2000) return {};
    struct Job { std::uint32_t attacks; float incoming; };
    std::array<Job,clear_risk_members> jobs{};
    std::size_t count=0;
    std::uint32_t total=0;
    for (auto m:members) {
        if (!std::isfinite(m.incoming)||m.incoming<0) return {};
        const BasicTarget one[]{{m.hp,damage_per_attack}};
        auto work=basic_attack_work(one,horizon-total);
        if (!work.complete()) return {work.status,total+work.attacks,0};
        if (!work.attacks) continue;
        total+=work.attacks;
        jobs[count++]={work.attacks,m.incoming};
    }
    // Smith's rule: kill the most incoming damage per attack first. This order
    // minimizes the summed exposure of a single stationary attacker.
    std::sort(jobs.begin(),jobs.begin()+count,[](const Job& a,const Job& b) {
        return static_cast<double>(a.incoming)*b.attacks>static_cast<double>(b.incoming)*a.attacks;
    });
    double damage=0;
    std::uint32_t elapsed=0;
    for (std::size_t i=0;i<count;++i) {
        elapsed+=jobs[i].attacks;
        // The first attack wakes the group after this turn's camp phase, and a
        // kill prevents that member's next phase: N attacks, N-1 future phases.
        damage+=static_cast<double>(jobs[i].incoming)*(elapsed-1);
    }
    return {WorkStatus::Complete,total,damage};
}
// Camps hit their nearest champion, so a crew spreads the group's damage. Price
// one member's share as if it absorbed two members' worth (capped at all of it).
inline double crew_share(unsigned crew) { return crew<=2 ? 1. : 2./crew; }
// Accept only with a margin over the predicted loss and a small HP floor.
inline bool clear_survivable(const ClearRisk& risk,float hp,float max_hp,double share=1) {
    return risk.complete()&&std::isfinite(hp)&&hp>0&&hp>1.25*risk.damage*share+.1*max_hp;
}
}
