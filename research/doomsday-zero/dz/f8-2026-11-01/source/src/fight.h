#pragma once
#include "config.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <span>
#include "ee_model.h"
#include "ee_enemy_model.h"

namespace dz {
// Local champion-fight estimate for engage / join / avoid decisions. Every
// fighter hits once per round for `damage`; each side focuses the opposing
// fighter with the least HP; damage applies simultaneously. Movement, range,
// spells, healing and hidden units are ignored. Index 0 of `ours` is the
// deciding champion. A heuristic, not the gated engagement evaluator (EE).
struct Fighter { float hp=0, damage=0; };
struct FightResult {
    bool valid=false;
    unsigned ours_alive=0, theirs_alive=0, rounds=0;
    bool self_alive=false;
    // The deciding champion survives and the enemy group is destroyed.
    bool won() const { return valid&&theirs_alive==0&&self_alive; }
};
inline constexpr std::size_t fight_units=12;
// Same result as simulate_fight, bit for bit (tests/dz/host/fast_fight_test.cpp): until a focus target dies, the
// damage sums and both targets cannot change, so only the two subtractions repeat. Scans run once per death
// instead of once per round; a 12-unit 40-round fight was ~15k fuel (dz-diag-ee3-profile-01, mark g).
inline FightResult simulate_fight_fast(std::span<const Fighter> ours,std::span<const Fighter> theirs,unsigned max_rounds=40) {
    if (ours.empty()||ours.size()>fight_units||theirs.size()>fight_units) return {};
    std::array<float,fight_units> a{},b{};
    for (std::size_t i=0;i<ours.size();++i) {
        if (!std::isfinite(ours[i].hp)||!std::isfinite(ours[i].damage)||ours[i].damage<0) return {};
        a[i]=std::max(0.f,ours[i].hp);
    }
    for (std::size_t i=0;i<theirs.size();++i) {
        if (!std::isfinite(theirs[i].hp)||!std::isfinite(theirs[i].damage)||theirs[i].damage<0) return {};
        b[i]=std::max(0.f,theirs[i].hp);
    }
    auto alive=[](const auto& hp,std::size_t n) { unsigned c=0; for (std::size_t i=0;i<n;++i) c+=hp[i]>0; return c; };
    auto weakest=[](const auto& hp,std::size_t n) {
        std::size_t best=n; for (std::size_t i=0;i<n;++i) if (hp[i]>0&&(best==n||hp[i]<hp[best])) best=i; return best;
    };
    unsigned round=0;
    while (round<max_rounds&&alive(a,ours.size())&&alive(b,theirs.size())) {
        float to_b=0,to_a=0;
        for (std::size_t i=0;i<ours.size();++i) if (a[i]>0) to_b+=ours[i].damage;
        for (std::size_t i=0;i<theirs.size();++i) if (b[i]>0) to_a+=theirs[i].damage;
        const auto tb=weakest(b,theirs.size()), ta=weakest(a,ours.size());
        do { b[tb]-=to_b; a[ta]-=to_a; ++round; } while (round<max_rounds&&b[tb]>0&&a[ta]>0);
    }
    return {true,alive(a,ours.size()),alive(b,theirs.size()),round,a[0]>0};
}
inline FightResult simulate_fight(std::span<const Fighter> ours,std::span<const Fighter> theirs,unsigned max_rounds=40) {
#if DZ_FAST_FIGHT
    return simulate_fight_fast(ours,theirs,max_rounds);
#else
    if (ours.empty()||ours.size()>fight_units||theirs.size()>fight_units) return {};
    std::array<float,fight_units> a{},b{};
    for (std::size_t i=0;i<ours.size();++i) {
        if (!std::isfinite(ours[i].hp)||!std::isfinite(ours[i].damage)||ours[i].damage<0) return {};
        a[i]=std::max(0.f,ours[i].hp);
    }
    for (std::size_t i=0;i<theirs.size();++i) {
        if (!std::isfinite(theirs[i].hp)||!std::isfinite(theirs[i].damage)||theirs[i].damage<0) return {};
        b[i]=std::max(0.f,theirs[i].hp);
    }
    auto alive=[](const auto& hp,std::size_t n) { unsigned c=0; for (std::size_t i=0;i<n;++i) c+=hp[i]>0; return c; };
    auto weakest=[](const auto& hp,std::size_t n) {
        std::size_t best=n; for (std::size_t i=0;i<n;++i) if (hp[i]>0&&(best==n||hp[i]<hp[best])) best=i; return best;
    };
    unsigned round=0;
    while (round<max_rounds&&alive(a,ours.size())&&alive(b,theirs.size())) {
        float to_b=0,to_a=0;
        for (std::size_t i=0;i<ours.size();++i) if (a[i]>0) to_b+=ours[i].damage;
        for (std::size_t i=0;i<theirs.size();++i) if (b[i]>0) to_a+=theirs[i].damage;
        const auto tb=weakest(b,theirs.size()), ta=weakest(a,ours.size());
        b[tb]-=to_b; a[ta]-=to_a; // Overkill is wasted, as in focus fire.
        ++round;
    }
    return {true,alive(a,ours.size()),alive(b,theirs.size()),round,a[0]>0};
#endif
}
// V-M2 calibrated logit of the deciding body (ours[0]) dying within 4 rounds; tools/dz_vm2.py fits the
// weights from replay contacts. ours: the body plus allies within 6; theirs: enemies within 8 at true HP.
inline float contact_logit(std::span<const Fighter> ours,std::span<const Fighter> theirs,float hp_fraction,int nearest,
                           float reach_damage,float intercept,const float* weights) {
    if (ours.empty()||theirs.empty()||theirs.size()>fight_units) return 0;
    std::array<Fighter,fight_units> inflated{};
    float po=0,pt=0,top=0;
    for (std::size_t i=0;i<theirs.size();++i) {
        inflated[i]={1.25f*theirs[i].hp,theirs[i].damage};
        pt+=theirs[i].hp*theirs[i].damage; top=std::max(top,theirs[i].damage);
    }
    for (const auto& f:ours) po+=f.hp*f.damage;
    const auto sim=simulate_fight(ours,std::span<const Fighter>(inflated.data(),theirs.size()));
    const float x[10]={hp_fraction,static_cast<float>(ours.size()-1),static_cast<float>(theirs.size()),nearest/8.f,
        sim.won()?1.f:0.f,sim.self_alive?1.f:0.f,sim.rounds/40.f,po+pt>0?po/(po+pt):.5f,
        reach_damage>0?std::min(ours[0].hp/reach_damage,20.f)/20.f:1.f,
        ours[0].damage+top>0?ours[0].damage/(ours[0].damage+top):.5f};
    float z=intercept;
    for (int i=0;i<10;++i) z+=weights[i]*x[i];
    return z;
}
inline float death_logit(std::span<const Fighter> ours,std::span<const Fighter> theirs,float hp_fraction,int nearest,
                         float reach_damage) {
    return contact_logit(ours,theirs,hp_fraction,nearest,reach_damage,ee_model::intercept,ee_model::weights);
}
// Logistic without libm: (1+z/256)^256 ~ e^z (about 1% error for |z|<6, clamped beyond).
inline float sigmoid(float z) {
    z=std::clamp(z,-12.f,12.f);
    float e=1.f-z/256.f;
    for (int i=0;i<8;++i) e*=e; // e^-z
    return 1.f/(1.f+e);
}
}
