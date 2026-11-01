#pragma once
#include <algorithm>
#include <array>
#include <bit>
#include <cmath>
#include <span>

namespace dz::draft_value {
inline constexpr unsigned bodies=13,picks=12,jobs=8;
constexpr unsigned physical(unsigned pick) {
    return pick>=picks?0:pick==3?((1u<<3)|(1u<<4)):1u<<(pick<3?pick:pick+1);
}
struct Score {float value=0;bool complete=false;};
struct Unlimited {bool operator()() const {return true;}};
// Rates are explicit static-design estimates, never safety/admission claims.
// One objective can fund one solo or pair, and each physical body works once.
// This exact small matching measures marginal lineup coverage without selling
// the same attractive resource to every champion independently.
struct Portfolio {
    unsigned count=0;
    std::array<std::array<std::array<float,bodies>,bodies>,jobs> rates{};
    template<class Budget=Unlimited>
    Score score(unsigned roster,Budget budget={}) const {
        Score result;
        if(count>jobs||roster>=(1u<<bodies)||std::popcount(roster)>6)return result;
        std::array<unsigned,6> actors{};unsigned n=0;
        for(unsigned b=0;b<bodies;++b)if(roster&(1u<<b))actors[n++]=b;
        std::array<float,64> current{},next{};current.fill(-1);current[0]=0;
        const unsigned size=1u<<n;
        for(unsigned g=0;g<count;++g) {
            if(!budget())return result;
            std::copy_n(current.begin(),size,next.begin());
            for(unsigned a=0;a<n;++a)for(unsigned b=a;b<n;++b) {
                const float rate=rates[g][actors[a]][actors[b]];
                if(!std::isfinite(rate)||rate<0)return {};
                if(rate==0)continue;
                const unsigned crew=(1u<<a)|(1u<<b),free=(size-1)&~crew;
                for(unsigned mask=free;;mask=(mask-1)&free) {
                    if(!budget())return result;
                    if(current[mask]>=0)next[mask|crew]=std::max(next[mask|crew],current[mask]+rate);
                    if(!mask)break;
                }
            }
            std::copy_n(next.begin(),size,current.begin());
            result.value=*std::max_element(current.begin(),current.begin()+size);
        }
        result.complete=true;return result;
    }
};
}
