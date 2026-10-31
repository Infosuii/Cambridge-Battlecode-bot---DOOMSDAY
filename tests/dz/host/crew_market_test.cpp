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
        return m.review(key,primary,pool,0,now,1000,{2000,12,120,.2f,1,false});
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
    menu=market.review(key,primary,units,0,11,1000,{2000,12,120,.2f,1,false},[&]{return ++budget_checks<=6;});
    assert(menu.complete&&menu.ready&&menu.count==2&&budget_checks<=6);
    menu=market.review(key,primary,units,0,11,1000,{2000,12,120,.2f,1,false},[]{return false;});
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
    // A baseline is a real spatial/recovery quote, including for one incumbent.
    // Its existing income is subtracted once; only the added worker is allocated.
    CrewMarket augment;const CrewEpoch fixed_key{4,1,7,12,6};
    const auto fixed_primary=augment.primary(fixed_key,units,0,0,2000);
    assert(fixed_primary[0]==7&&fixed_primary[1]==0);
    const CrewPrice price{2000,12,120,.2f,1,false,1};
    augment.put(fixed_key,7,units,0,1000,80,10,true);
    menu=augment.review(fixed_key,fixed_primary,units,0,1,1000,price);
    assert(menu.complete&&!menu.ready&&!menu.count&&menu.request==6);
    const std::array<crew::Unit,2> incumbents{units[1],units[2]};
    augment.put(fixed_key,6,incumbents,1,1000,110,10,true);
    menu=augment.review(fixed_key,fixed_primary,units,0,2,1000,price);
    assert(menu.ready&&menu.count==1&&menu.bids[0].fixed==6);
    auto absent_cap=price;absent_cap.incumbent_capturer=0;
    assert(!augment.review(fixed_key,fixed_primary,units,0,2,1000,absent_cap).complete);
    assert(std::abs(menu.bids[0].utility()-(36.f/80-36.f/110))<1e-6f);
    const std::array<int,6> held{-1,4,4,-1,-1,-1};
    result=allocate(std::span<const Bid>(menu.bids.data(),menu.count),1,UnlimitedAuction{},held);
    assert(result[0].crew==7&&result[1].objective<0&&result[2].objective<0);
    augment.put(fixed_key,6,incumbents,2,1000,40,10,true);
    menu=augment.review(fixed_key,fixed_primary,units,0,3,1000,price);
    assert(!menu.ready&&!menu.count&&!menu.request); // A helper that slows production has no gain.
    augment.put(fixed_key,6,incumbents,3,1000,10,10,false);
    menu=augment.review(fixed_key,fixed_primary,units,0,4,1000,price);
    assert(!menu.ready&&!menu.count&&!menu.request); // Unsupported baseline is not zero income.
    const CrewEpoch single_key{4,1,7,12,2};CrewMarket single;
    const auto duo=std::span<const crew::Unit>(units.data(),2);
    auto single_primary=single.primary(single_key,duo,0,0,2000);
    single.put(single_key,2,std::span<const crew::Unit>(&units[1],1),0,1000,120,10,true);
    single.put(single_key,3,duo,0,1000,60,10,true);
    menu=single.review(single_key,single_primary,duo,0,1,1000,price);
    assert(menu.ready&&menu.count==1&&menu.bids[0].fixed==2);
    std::vector<Bid> marginal{{4,3,0,100,100,.8f,0,2},{5,1,0,30,100}};
    result=allocate(marginal,1,UnlimitedAuction{},held);
    assert(result[0].objective==5&&result[1].objective<0); // No second credit for the incumbent's income.
    auto wrong=held;wrong[1]=5;
    result=allocate(std::span<const Bid>(marginal.data(),1),1,UnlimitedAuction{},wrong);assert(result[0].objective<0);
    assert((augment.primary({4,1,7,12,8},units,0,4,2000)==std::array<unsigned,2>{})); // Unseen incumbent.
    // Independent exhaustive reference for the optimistic candidate ordering.
    std::mt19937 rng(4001);unsigned checks=0;
    for(unsigned trial=0;trial<300;++trial) {
        std::array<crew::Unit,6> actors{};const unsigned n=2+rng()%5,self=rng()%n;
        for(unsigned u=0;u<n;++u)actors[u]={u,u,{1,1},1000,1000,float(10+rng()%200),1,1,int(rng()%30)};
        const auto pool=std::span<const crew::Unit>(actors.data(),n);CrewMarket m;
        auto task=key;task.fixed=trial%2?(rng()%((1u<<n)-1))&~(1u<<self):0;
        const auto selected=m.primary(task,pool,self,0,3000);
        const unsigned minimum=std::max(2,std::popcount(task.fixed)+1);
        for(unsigned size=minimum;size<=minimum+1;++size) {
            float best=-1;unsigned winner=0;
            for(unsigned mask=1;mask<(1u<<n);++mask)if(static_cast<unsigned>(std::popcount(mask))==size&&(mask&(1u<<self))&&!(task.fixed&~mask)) {
                float damage=0;int arrival=0;
                for(unsigned u=0;u<n;++u)if(mask&(1u<<u)){damage+=actors[u].damage;arrival=std::max(arrival,actors[u].arrival);}
                const float score=1.f/(arrival+std::ceil(3000/damage)+6);
                if(score>best){best=score;winner=mask;}
            }
            assert(selected[size-minimum]==winner);++checks;
        }
    }
    // Exhaust all bid combinations independently of the production subset DP.
    // Two existing jobs retain workers0/1; only slots2..5 can be sold.
    unsigned allocations=0;
    for(unsigned trial=0;trial<400;++trial) {
        const std::array<int,6> reservations{0,1,-1,-1,-1,-1};std::array<Bid,7> offers{};
        for(auto& b:offers) {
            b.objective=rng()%4;b.fixed=b.objective<2?1u<<b.objective:0;
            b.crew=((1u+(rng()%15))<<2)|b.fixed;b.capturer=std::countr_zero(b.crew&~b.fixed);
            b.value=10+rng()%100;b.duration=10+rng()%50;b.opportunity=b.fixed?.01f*(rng()%100):0;
        }
        float best=0;
        for(unsigned subset=0;subset<(1u<<offers.size());++subset) {
            unsigned workers=0,jobs=0;float score=0;bool legal=true;
            for(unsigned i=0;i<offers.size();++i)if(subset&(1u<<i)) {
                const auto& b=offers[i];const auto free=b.crew&~b.fixed;
                if((workers&free)||(jobs&(1u<<b.objective))||b.utility()<=0){legal=false;break;}
                workers|=free;jobs|=1u<<b.objective;score+=b.utility();
            }
            if(legal)best=std::max(best,score);
        }
        const auto chosen=allocate(offers,60,UnlimitedAuction{},reservations);unsigned jobs=0;float actual=0;
        assert(chosen[0].objective<0&&chosen[1].objective<0);
        for(unsigned s=2;s<6;++s)if(chosen[s].objective>=0&&!(jobs&(1u<<chosen[s].objective))) {
            actual+=chosen[s].utility;jobs|=1u<<chosen[s].objective;
        }
        assert(std::abs(actual-best)<1e-4f);++allocations;
    }
    std::cout<<checks<<" independent crew-frontier and "<<allocations<<" exhaustive fixed-worker allocations; spatial baselines, marginal income and reservation guards passed\n";
}
