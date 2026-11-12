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
    for(unsigned trial=0;trial<1000;++trial) {
        std::array<ClearMember,4> compressed{};std::array<unsigned,4> counts{};
        std::array<ClearMember,64> expanded{};unsigned size=0;
        for(unsigned type=0;type<4;++type) {
            compressed[type]={float(1+rng()%300),float(rng()%70)};counts[type]=1+rng()%8;
            for(unsigned k=0;k<counts[type];++k)expanded[size++]=compressed[type];
        }
        Encounter one{compressed,14,240};one.multiplicities=counts;
        Encounter many{std::span<const ClearMember>(expanded.data(),size),14,240};
        const auto a=forecast(one,std::span<const Actor>(&solo,1),0),b=forecast(many,std::span<const Actor>(&solo,1),0);
        assert(a.clear==b.clear&&a.loss_upper==b.loss_upper&&a.survivable==b.survivable);
    }
    ClearMember resource[]{ {1,0} };unsigned hundred[]{100};
    Encounter large{resource,100,100};large.multiplicities=hundred;
    const auto cluster=forecast(large,std::span<const Actor>(&solo,1),0);assert(cluster.clear==100&&cluster.loss_upper[0]==0);
    const Bid bids[]{ {0,1,0,20,10}, {0,2,1,20,10}, {1,2,1,15,10}, {2,3,0,50,10,4} };
    auto assigned=economy::allocate(bids,3);
    assert(assigned[0].objective==0&&assigned[1].objective==1);
    const Bid viable_crew[]{ {0,1,0,1,10}, {1,2,1,1,10}, {2,3,1,50,10,.1f} };
    assigned=economy::allocate(viable_crew,3);
    assert(assigned[0].objective==2&&assigned[1].objective==2&&assigned[0].capturer==1);
    assigned=economy::allocate(viable_crew,1);assert(assigned[0].objective==0&&assigned[1].objective==-1);
    // No solo can clear the opening camp. All healthy bodies fell back Home;
    // that state must still supply a publishable crew instead of being absorbing.
    auto word=protocol::empty_word();unsigned free=0;
    for(unsigned slot=0;slot<3;++slot) {
        word=protocol::with_slot(word,slot,{protocol::shop,false});
        if(economy::available_for_offer(protocol::slot(word,slot).objective,true))free|=1u<<slot;
    }
    const Bid opening[]{{2,7,0,40,100}};
    assigned=economy::allocate(opening,free);
    assert(assigned[0].crew==7&&assigned[1].objective==2&&assigned[2].objective==2);
    assert(!economy::available_for_offer(protocol::shop,false)&&!economy::available_for_offer(protocol::retreat,false));
    assert(!economy::starved(200,0,180)&&economy::starved(151,0,0)&&!economy::starved(151,100,0));
    const Bid scarce[]{{0,1,0,10,20},{0,2,1,10,20},{0,4,2,10,20},{0,3,0,10,10}};
    assigned=economy::allocate(scarce,7);assert(assigned[0].crew==3&&assigned[1].crew==3&&assigned[2].objective==-1);
    const Bid split[]{{0,1,0,9,10},{1,2,1,9,10},{2,3,0,15,10}};
    assigned=economy::allocate(split,3);assert(assigned[0].objective==0&&assigned[1].objective==1);
    assigned=economy::allocate(split,3,[]{return false;});assert(assigned[0].objective==-1&&assigned[1].objective==-1);
    const Bid sparse[]{{2,48,5,20,10},{3,4,2,9,10}};
    assigned=economy::allocate(sparse,52);
    assert(assigned[4].objective==2&&assigned[5].crew==48&&assigned[2].objective==3&&assigned[0].objective==-1);
    for(unsigned trial=0;trial<200;++trial) {
        std::array<Bid,12> choices{};
        for(unsigned g=0;g<3;++g)for(unsigned option=0;option<4;++option) {
            const unsigned mask=option<3?1u<<option:7u;
            choices[g*4+option]={static_cast<int>(g),mask,option<3?option:0,static_cast<float>(1+rng()%100),static_cast<float>(1+rng()%20)};
        }
        const unsigned free=rng()%8;float reference=0;
        for(int a=-1;a<4;++a)for(int b=-1;b<4;++b)for(int c=-1;c<4;++c) {
            unsigned used=0;float value=0;bool valid=true;const std::array<int,3> pick{{a,b,c}};
            for(unsigned g=0;g<3;++g)if(pick[g]>=0) {
                const auto& bid=choices[g*4+pick[g]];
                if((bid.crew&~free)||(used&bid.crew)){valid=false;break;}
                used|=bid.crew;value+=bid.utility();
            }
            if(valid)reference=std::max(reference,value);
        }
        assigned=economy::allocate(choices,free);float value=0;unsigned seen=0;
        for(const auto& job:assigned)if(job.objective>=0&&!(seen&(1u<<job.objective))){seen|=1u<<job.objective;value+=job.utility;}
        assert(std::abs(reference-value)<.0001f);
    }
    std::cout<<cases<<" objective exposure/order cases; crew allocation, horizon, reward and invalid-input checks passed\n";
}
