#include "crew_market.h"
#include <cassert>
#include <iostream>
#include <random>
using namespace dz;
int main() {
    using namespace economy;
    std::array<crew::Unit,3> units{{{0,0,{1,1},1000,1000,50,1,1,10},
        {1,1,{2,1},1000,1000,20,1,1,10},{2,2,{3,1},1000,1000,100,1,1,10}}};
    CrewMarket market;const CrewEpoch key{4,1,7,12};
    auto review=[&](const CrewMarket& m,std::array<unsigned,2> primary,std::span<const crew::Unit> pool,int now) {
        return m.review(key,primary,pool,0,now,1000,2000,12,120,false,.2f,1);
    };
    auto primary=market.primary(key,units,0,10,2000);assert(primary[0]==5&&primary[1]==7);
    const std::array<crew::Unit,2> pair{units[0],units[2]};
    market.put(key,5,pair,10,1000,110,10,true);
    auto menu=review(market,primary,units,10);assert(menu.complete&&!menu.ready&&menu.request==7);
    market.put(key,7,units,11,1000,80,10,true);
    menu=review(market,primary,units,11);assert(menu.complete&&menu.ready&&menu.request==0);
    std::vector<Bid> bids(menu.bids.begin(),menu.bids.begin()+menu.count);
    assert(bids.size()==2);auto result=allocate(bids,7);assert(result[0].crew==7);
    bids.push_back({5,2,1,100,10});result=allocate(bids,7);
    assert(result[0].crew==5&&result[1].objective==5); // Actual useful work makes splitting win.
    auto travelled=units;for(auto& u:travelled)u.arrival=25;
    auto quote=market.get(key,5,travelled,12,1000);assert(quote&&CrewMarket::duration(*quote,travelled)==125);
    travelled[0].hp=999;assert(!market.get(key,5,travelled,12,1000));
    travelled=units;travelled[2].damage=101;assert(!market.get(key,5,travelled,12,1000));
    assert(!market.get({4,2,7,12},5,units,12,1000));
    assert(!market.get({4,1,8,12},5,units,12,1000));
    assert(!market.get({4,1,7,13},5,units,12,1000));
    assert(market.get(key,5,units,200,1000)); // Same observed inputs still validate a completed static quote.
    unsigned budget_checks=0;
    menu=market.review(key,primary,units,0,11,1000,2000,12,120,false,.2f,1,[&]{return ++budget_checks<=6;});
    assert(menu.complete&&menu.ready&&menu.count==2&&budget_checks<=6);
    menu=market.review(key,primary,units,0,11,1000,2000,12,120,false,.2f,1,[]{return false;});
    assert(!menu.complete&&!menu.ready&&!menu.count&&!menu.request);
    market.decline(4,5,210);assert(!market.get(key,5,units,211,1000));
    auto bad=units;bad[0].slot=32;assert((market.primary(key,bad,0,12,2000)==std::array<unsigned,2>{}));
    bad=units;bad[1].slot=0;assert(!review(market,primary,bad,12).complete);
    // Failed pair/triple admission opens the remaining bounded frontier. A
    // negative cache never prevents a newly healthier/closer body being tried.
    CrewMarket fallback;auto priorities=fallback.primary(key,units,0,0,2000);
    fallback.put(key,5,pair,0,1000,10,10,false);fallback.put(key,7,units,0,1000,10,10,false);
    assert(review(fallback,priorities,units,1).request==3);
    auto healed=units;healed[0].hp=healed[0].max_hp=1100;
    assert(!fallback.get(key,5,healed,1,1000));
    auto closer=units;for(auto& u:closer)u.arrival=1;
    assert(!fallback.get(key,5,closer,1,1000));
    // Independent exhaustive reference for the optimistic candidate ordering.
    std::mt19937 rng(4001);unsigned checks=0;
    for(unsigned trial=0;trial<300;++trial) {
        std::array<crew::Unit,6> actors{};const unsigned n=2+rng()%5,self=rng()%n;
        for(unsigned u=0;u<n;++u)actors[u]={u,u,{1,1},1000,1000,float(10+rng()%200),1,1,int(rng()%30)};
        const auto pool=std::span<const crew::Unit>(actors.data(),n);CrewMarket m;const auto selected=m.primary(key,pool,self,0,3000);
        for(unsigned size=2;size<=3;++size) {
            float best=-1;unsigned winner=0;
            for(unsigned mask=1;mask<(1u<<n);++mask)if(static_cast<unsigned>(std::popcount(mask))==size&&(mask&(1u<<self))) {
                float damage=0;int arrival=0;
                for(unsigned u=0;u<n;++u)if(mask&(1u<<u)){damage+=actors[u].damage;arrival=std::max(arrival,actors[u].arrival);}
                const float score=1.f/(arrival+std::ceil(3000/damage)+6);
                if(score>best){best=score;winner=mask;}
            }
            assert(selected[size-2]==winner);++checks;
        }
    }
    std::cout<<checks<<" independent crew-frontier order references; pair/triple competition, disjoint work, quote invalidation and fallback passed\n";
}
