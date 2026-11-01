#include "draft_value.h"
#include <cassert>
#include <functional>
#include <iostream>
#include <random>
using namespace dz;
int main() {
    unsigned all=0;for(unsigned p=0;p<12;++p){const auto bodies=draft_value::physical(p);assert(bodies&&!(all&bodies));all|=bodies;}
    assert(all==8191&&std::popcount(draft_value::physical(3))==2&&!draft_value::physical(12));
    std::mt19937 rng(19594);
    for(unsigned test=0;test<600;++test) {
        draft_value::Portfolio profile;profile.count=1+rng()%3;const unsigned actors=1+rng()%4,roster=(1u<<actors)-1;
        for(unsigned g=0;g<profile.count;++g)for(unsigned a=0;a<actors;++a)for(unsigned b=a;b<actors;++b)
            profile.rates[g][a][b]=rng()%20;
        std::function<float(unsigned,unsigned)> reference=[&](unsigned g,unsigned used) {
            if(g==profile.count)return 0.f;float best=reference(g+1,used);
            for(unsigned a=0;a<actors;++a)for(unsigned b=a;b<actors;++b) {
                const unsigned crew=(1u<<a)|(1u<<b);if(crew&used)continue;
                best=std::max(best,profile.rates[g][a][b]+reference(g+1,used|crew));
            }
            return best;
        };
        const auto result=profile.score(roster);assert(result.complete&&result.value==reference(0,0));
        assert(profile.score(roster|16).value>=result.value);
        assert(!profile.score(roster,[]{return false;}).complete);
    }
    draft_value::Portfolio p;p.count=1;p.rates[0][0][0]=10;p.rates[0][1][1]=9;p.rates[0][0][1]=12;
    assert(p.score(3).value==12); // One job cannot pay both solos and the pair.
    p.count=2;p.rates[1][1][1]=8;assert(p.score(3).value==18);
    assert(!p.score(8191).complete);p.count=9;assert(!p.score(1).complete);
    std::cout<<"600 exhaustive static draft portfolios; disjoint solos/pairs, linked identities and budget fallback passed\n";
}
