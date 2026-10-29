#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <span>

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
inline FightResult simulate_fight(std::span<const Fighter> ours,std::span<const Fighter> theirs,unsigned max_rounds=40) {
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
}
}
