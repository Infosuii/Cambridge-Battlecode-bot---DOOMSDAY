#include "crew_progression.h"
#include <cassert>
#include <iostream>
using namespace dz;
int main() {
    constexpr crew::Shard shard{30,5,1,6};
    crew::Unit actor{0,1,{1,1},1000,1000,40,1,3};
    actor.health_growth=120;actor.damage_growth=8;actor.health_damage_growth=1.2f;actor.inventory_known=true;
    unsigned cases=0;
    for(unsigned owned=0;owned<5;++owned)for(unsigned cash=0;cash<1000;++cash)for(unsigned stat=0;stat<2;++stat) {
        auto u=actor;u.power_health=u.power_strength=owned;
        const auto q=crew::upgrade(u,stat,cash,shard);
        unsigned ingredients=owned,points=0,count=0,money=cash;
        // Transaction reference includes multiple combinations in one visit.
        while(money>=30&&count<16){money-=30;++count;++ingredients;++points;if(ingredients==5){ingredients=0;++points;}}
        assert(q.valid&&q.purchases==count&&q.unit.hp==q.unit.max_hp);
        assert(q.unit.max_hp==u.max_hp+(stat?points*120:0));
        assert(std::abs(q.unit.damage-u.damage-points*(stat?1.2f:8.f))<.001f);
        ++cases;
    }
    auto unknown=actor;unknown.inventory_known=false;unknown.power_health=4;
    assert(crew::upgrade(unknown,1,30,shard).unit.max_hp==1120); // No inferred emblem bonus.
    assert(!crew::upgrade(actor,2,100,shard).valid);
    assert(!crew::upgrade(actor,0,100,{0,5,1,6}).valid);
    auto invalid=actor;invalid.health_growth=std::numeric_limits<float>::quiet_NaN();
    assert(!crew::upgrade(invalid,1,100,shard).valid);
    std::array<crew::Unit,2> units{actor,actor};units[1].slot=1;units[1].handle=2;units[1].p={2,1};
    const std::array<crew::Monster,1> camps{{{0,{10,10},6000,20,1}}};
    crew::SequenceSearch geometry;geometry.begin(units,camps,24,24);
    auto open=[](Tile p,unsigned){return p.x>=0&&p.y>=0&&p.x<24&&p.y<24;};
    auto home=[](Tile p){return cheb(p,{1,1});};
    assert(geometry.resume(units,camps,open,home,[]{return true;}));
    auto improved=units;improved[0]=crew::upgrade(units[0],0,300,shard).unit;
    assert(!crew::quote(improved,camps,geometry,0,6,5,2000).complete);
    assert(crew::quote(improved,camps,geometry,0,6,5,2000,[]{return true;},true).complete);
    for(unsigned field=0;field<4;++field) {
        auto bad=improved;
        if(field==0)bad[0].range=2;
        if(field==1)bad[0].factor=.9f;
        if(field==2)bad[0].damage=1;
        if(field==3)bad[0].handle=99;
        assert(!crew::quote(bad,camps,geometry,0,6,5,2000,[]{return true;},true).complete);
    }
    const std::array<team::Cash,2> reports{{{0,0,7,true},{0,120,127,true}}};
    crew::Progression full,resumed;
    full.begin(units,reports,{shard,shard},0,26,1800,30,8,40,5,12,120);
    resumed=full;full.resume(units,camps,geometry);
    unsigned slices=0;
    while(resumed.pending()&&slices++<1000){unsigned calls=0;resumed.resume(units,camps,geometry,[&]{return ++calls<=8;});}
    assert(!resumed.pending()&&slices<1000);
    bool any=false;
    for(unsigned k=0;k<4;++k) {
        assert(full.choices[k].valid==resumed.choices[k].valid&&full.choices[k].gain==resumed.choices[k].gain);
        any|=full.choices[k].valid;
    }
    assert(any&&!full.best(0,27).valid);
    // Missing/saturated reports and no future bank horizon retain raw payout.
    auto missing=reports;missing[0].valid=false;missing[1].high=~0u;
    crew::Progression fallback;fallback.begin(units,missing,{shard,shard},0,26,1800,30,8,40,5,12,120);
    fallback.resume(units,camps,geometry);assert(!fallback.best(0,0).valid&&!fallback.best(1,0).valid);
    crew::Progression late;late.begin(units,reports,{shard,shard},0,26,20,30,8,40,5,12,120);
    late.resume(units,camps,geometry);assert(!late.best(0,0).valid&&!late.best(1,0).valid);
    std::cout<<cases<<" independent purchase transactions; monotone-only projection, resumed payout pricing, horizon and freshness fallbacks passed\n";
}
