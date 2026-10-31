#pragma once
#include "clear_risk.h"
#include <limits>

namespace dz::objective {
inline constexpr unsigned max_crew=6;
struct Actor {
    float hp=0, max_hp=0, damage=0, incoming_factor=1;
    int arrival=0;
    float shield=0;
    int shield_duration=0;
    float gold_multiplier=1;
    bool prospector=false;
    int capture_rounds=5;
};
struct Encounter {
    std::span<const ClearMember> members;
    float gems=0, gold=0;
    int ready_in=0, capture_remaining=-1, reposition_rounds=0;
    bool cluster=false, contested=false, exact_arrival=true;
    int horizon=2000;
};
enum class Quality { Invalid, Bounded, Conservative, Contested, BeyondHorizon };
struct Quote {
    Quality quality=Quality::Invalid;
    int arrival=0, clear=0, capture=0, finish=0;
    float champion_rounds=0, gems=0, gold_low=0, gold_high=0;
    std::array<double,max_crew> loss_upper{};
    bool survivable=false;
    bool complete() const { return quality==Quality::Bounded||quality==Quality::Conservative; }
    float reward(float gold_price) const { return gems+gold_price*gold_low; }
    float rate(float gold_price) const { return complete()&&survivable ? reward(gold_price)/std::max(1.f,champion_rounds) : 0; }
};
inline float gold_price(int remaining) { return std::clamp(remaining*.25f/900.f,.02f,.6f); }

// A bounded rendezvous forecast, not a fitted probability or V-M1 certification.
// Every actor arrives before waking the group. All can focus the same member;
// damage is deliberately rounded down to the pooled basic rate. No reset,
// splash, shield recast, death sharing or unseen ally is needed for admission.
// Upper exposure uses the WORST member order (weak damaging members die last).
// Every actor must survive being the sole tank: proximity is not damage sharing.
inline Quote forecast(const Encounter& e,std::span<const Actor> crew,unsigned capturer) {
    Quote q;
    if(crew.empty()||crew.size()>max_crew||capturer>=crew.size()||e.members.size()>clear_risk_members||
        e.ready_in<0||e.reposition_rounds<0||e.horizon<1||e.horizon>2000||
        !std::isfinite(e.gems)||!std::isfinite(e.gold)||e.gems<0||e.gold<0) return q;
    if(e.contested) { q.quality=Quality::Contested;return q; }
    float damage=0;
    for(auto a:crew) {
        if(!std::isfinite(a.hp)||!std::isfinite(a.max_hp)||!std::isfinite(a.damage)||
            !std::isfinite(a.incoming_factor)||!std::isfinite(a.shield)||!std::isfinite(a.gold_multiplier)||
            a.hp<=0||a.max_hp<a.hp||a.damage<0||a.incoming_factor<0||a.shield<0||
            a.gold_multiplier<0||a.arrival<0||a.arrival>2000||a.capture_rounds<0||a.capture_rounds>2000) return q;
        damage+=a.damage;q.arrival=std::max(q.arrival,a.arrival);
    }
    q.arrival=std::max(q.arrival,e.ready_in);
    struct Job { int rounds;float incoming; };
    std::array<Job,clear_risk_members> jobs{};
    unsigned n=0;double incoming=0;
    for(auto m:e.members) {
        if(!std::isfinite(m.hp)||!std::isfinite(m.incoming)||m.hp<0||m.incoming<0) return {};
        if(m.hp==0) continue;
        if(damage<=0) return {};
        const double rounds=std::ceil(static_cast<double>(m.hp)/damage);
        if(rounds>e.horizon||q.clear+rounds>e.horizon) { q.quality=Quality::BeyondHorizon;return q; }
        const int work=static_cast<int>(rounds);
        jobs[n++]={work,m.incoming};q.clear+=work;incoming+=m.incoming;
    }
    std::sort(jobs.begin(),jobs.begin()+n,[](auto a,auto b) {
        return static_cast<double>(a.incoming)*b.rounds<static_cast<double>(b.incoming)*a.rounds;
    });
    double exposure=0;int elapsed=0;
    for(unsigned i=0;i<n;++i) { elapsed+=jobs[i].rounds;exposure+=jobs[i].incoming*(elapsed-1); }
    // Member travel and round-order ambiguity each add full living-group exposure.
    if(n) { q.clear+=e.reposition_rounds;exposure+=incoming*(e.reposition_rounds+1); }
    q.capture=e.capture_remaining>=0 ? e.capture_remaining : crew[capturer].capture_rounds+1;
    if(q.capture>2000) return {};
    q.finish=q.arrival+q.clear+q.capture;
    if(q.finish>e.horizon) { q.quality=Quality::BeyondHorizon;return q; }
    q.champion_rounds=q.capture;
    q.survivable=true;
    for(unsigned i=0;i<crew.size();++i) {
        auto a=crew[i];
        q.champion_rounds+=q.arrival+q.clear;
        // Existing shield credit only while it can still be present at arrival.
        const int protected_rounds=std::max(0,a.shield_duration-q.arrival);
        const double credit=std::min<double>(a.shield,incoming*a.incoming_factor*protected_rounds);
        q.loss_upper[i]=std::max(0.,exposure*a.incoming_factor-credit);
        q.survivable &= a.hp>1.25*q.loss_upper[i]+.15*a.max_hp;
    }
    const auto& cap=crew[capturer];
    const double boost=e.cluster&&cap.prospector ? 1.25 : 1.;
    q.gems=static_cast<float>(std::floor(e.gems*boost));
    const double gold=e.gold*boost*cap.gold_multiplier;
    // Unknown accumulated fractional gold remainder: never invent a carry.
    q.gold_low=static_cast<float>(std::floor(gold));q.gold_high=static_cast<float>(std::ceil(gold));
    q.quality=e.exact_arrival ? Quality::Conservative : Quality::Bounded;
    return q;
}
}
