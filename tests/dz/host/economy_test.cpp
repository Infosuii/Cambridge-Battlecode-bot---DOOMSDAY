#include "allocation.h"
#include <cassert>
#include <iostream>
#include <random>
using namespace dz;
int main() {
    using namespace objective;
    Actor solo{1000,1000,100,.5f};
    ClearMember wolf[]{ {300,40} };
    Encounter e{wolf,14,240};
    auto q=forecast(e,std::span<const Actor>(&solo,1),0);
    assert(q.complete()&&q.survivable&&q.clear==3&&q.capture==6&&q.finish==9);
    assert(q.loss_upper[0]==60&&q.gems==14&&q.gold_low==240);
    solo.arrival=7;e.ready_in=10;
    q=forecast(e,std::span<const Actor>(&solo,1),0);assert(q.arrival==10&&q.finish==19);
    e.horizon=18;assert(forecast(e,std::span<const Actor>(&solo,1),0).quality==Quality::BeyondHorizon);
    e.horizon=2000;e.ready_in=0;solo.arrival=0;
    Actor crew[]{solo,solo};crew[1].damage=250;crew[1].incoming_factor=.25;
    auto pair=forecast(e,crew,1);assert(pair.clear==1&&pair.loss_upper[1]<=q.loss_upper[0]);
    // Single capturer gains, not an invented full reward for every helper.
    e.cluster=true;crew[1].prospector=true;crew[1].gold_multiplier=1.33f;
    pair=forecast(e,crew,1);assert(pair.gems==17&&pair.gold_low==399&&pair.gold_high==400);
    e.contested=true;assert(forecast(e,crew,1).quality==Quality::Contested);e.contested=false;
    wolf[0].hp=-1;assert(forecast(e,crew,1).quality==Quality::Invalid);wolf[0].hp=300;
    // Compare worst-order upper exposure with every order of random small groups.
    std::mt19937 rng(105);unsigned cases=0;
    for(int test=0;test<500;++test) {
        std::array<ClearMember,5> monsters{};
        for(auto& monster:monsters)monster={float(1+rng()%500),float(rng()%80)};
        Encounter group{monsters,14,100};Actor tank{100000,100000,100,1};
        const auto upper=forecast(group,std::span<const Actor>(&tank,1),0);
        std::array<unsigned,5> order{0,1,2,3,4};
        do {
            double damage=0;int elapsed=0;
            for(auto index:order) {elapsed+=int(std::ceil(monsters[index].hp/100));damage+=monsters[index].incoming*(elapsed-1);}
            assert(damage<=upper.loss_upper[0]);++cases;
        } while(std::next_permutation(order.begin(),order.end()));
        // More health cannot reduce admission; more mitigation cannot raise loss.
        tank.incoming_factor=.5;
        auto protected_quote=forecast(group,std::span<const Actor>(&tank,1),0);
        assert(protected_quote.loss_upper[0]<=upper.loss_upper[0]);
    }
    using economy::Bid;
    const Bid bids[]{ {0,1,0,20,10}, {0,2,1,20,10}, {1,2,1,15,10}, {2,3,0,50,10,4} };
    auto assigned=economy::allocate(bids,3);
    assert(assigned[0].objective==0&&assigned[1].objective==1);
    const Bid viable_crew[]{ {0,1,0,1,10}, {1,2,1,1,10}, {2,3,1,50,10,.1f} };
    assigned=economy::allocate(viable_crew,3);
    assert(assigned[0].objective==2&&assigned[1].objective==2&&assigned[0].capturer==1);
    assigned=economy::allocate(viable_crew,1);assert(assigned[0].objective==0&&assigned[1].objective==-1);
    std::cout<<cases<<" objective exposure/order cases; crew allocation, horizon, reward and invalid-input checks passed\n";
}
