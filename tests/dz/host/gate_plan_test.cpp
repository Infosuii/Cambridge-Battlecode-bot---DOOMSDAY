#include "gate_plan.h"
#include "access_route.h"
#include "macro_value.h"
#include <cassert>
#include <iostream>
using namespace dz;
int main() {
    gate::Cut cut;cut.hp=300;cut.incoming=20;cut.escape_loss=40;cut.escape_rounds=2;cut.home=5;cut.arrival=7;
    auto work=gate::price(cut,1200,1200,50);
    assert(work.valid&&work.attacks==6&&work.visits==1&&work.rounds==21);
    cut.hp=3000;work=gate::price(cut,1200,1200,50);
    assert(work.valid&&work.attacks==60&&work.visits==2&&work.rounds==88);
    // Independent tick accounting: visit until another hit would violate the
    // HP/escape/surprise reserve, withdraw, heal, walk back, and continue.
    int hp_left=3000,visits=0,attacks=0,ticks=cut.arrival;
    while(hp_left>0) {
        int health=1200;
        while(hp_left>0&&health-20>180+50+20) {health-=20;hp_left-=50;++attacks;++ticks;}
        assert(health-40>=180);++visits;ticks+=2+5+1;
        if(hp_left>0)ticks+=5;
    }
    assert(visits==work.visits&&attacks==work.attacks&&ticks==work.rounds);
    assert(!gate::price(cut,1200,1200,50,87).valid);
    cut.hp=500;assert(gate::price(cut,1200,1200,50).rounds<work.rounds);
    cut.incoming=1000;assert(!gate::price(cut,1200,1200,50).valid);
    cut.incoming=20;cut.home=-1;assert(!gate::price(cut,1200,1200,50).valid);
    auto distance=[](Tile p){return p.y==0&&p.x>=0&&p.x<=6?6-p.x:65535;};
    auto blocking=[](Tile p){return p.x==2?access::Blocker{0,0,1}:p.x==4?access::Blocker{1,0,100}:access::Blocker{};};
    std::array<int,2> groups{};unsigned n=0,steps=0;
    auto record=[&](access::Blocker b,Tile previous,Tile tile,int) {
        ++steps;assert(tile.x==previous.x+1);
        if(b.group>=0){assert(previous.x==1||previous.x==3);groups[n++]=b.group;}
        return true;
    };
    auto path=access::itinerary({0,0},distance,blocking,record);
    assert(path.status==access::Status::Clear&&steps==6&&n==2&&groups[0]==0&&groups[1]==1);
    n=steps=0;unsigned allowance=2;
    path=access::itinerary({0,0},distance,blocking,record,[&]{return allowance-->0;});
    assert(path.status==access::Status::Unknown&&path.tile.x==2&&n==1);
    path=access::itinerary(path.tile,distance,blocking,record);
    assert(path.status==access::Status::Clear&&n==2&&steps==6);
    path=access::itinerary({0,0},distance,blocking,[](auto b,auto,auto,int){return b.group<0;});
    assert(path.status==access::Status::Unknown); // Capacity failure cannot publish a complete quote.
    gate::Plan p;p.reset(20,0,1000,100,.7f,1);
    assert(p.matches(21,999,1000,100,.7f,1)); // A distant camp update does not restart path work.
    assert(!p.matches(21,999,1200,100,.7f,1)); // Gear growth does require a new quote.
    gate::Plan::Dependency d{0,0,80,false,true};
    assert(gate::Plan::dependency_matches(d,false,true,80));
    assert(!gate::Plan::dependency_matches(d,true,true,80));
    assert(!gate::Plan::dependency_matches(d,false,true,81));
    assert(!gate::Plan::dependency_matches(d,false,false,80));
    assert(!access::member_blocks(true,true,100,99));
    assert(access::member_blocks(true,true,100,100));
    assert(access::member_blocks(true,false,100,99));
    assert(!access::member_blocks(false,false,100,99));
    // The ledger may contain design HP for a captured outer camp. It must not
    // invent an occupant on an otherwise checked retreat through its cell.
    const CampThreat golem[]{{{16,15},120,3}};
    const Tile away[]{{1,0}};
    auto corridor=[&](Tile p,int ready) {
        return p.y==15&&p.x>=18&&p.x<=22&&
            (p.x!=18||!access::member_blocks(true,true,ready,cheb({17,15},p)));
    };
    auto escape=siege::escape_route({17,15},golem,away,[&](Tile p){return corridor(p,10);});
    assert(escape.found&&escape.damage==240&&escape.steps==3);
    escape=siege::escape_route({17,15},golem,away,[&](Tile p){return corridor(p,1);});
    assert(!escape.found);
    assert(siege::backtrack_safe(1200,1200,120,120,240));
    assert(!siege::backtrack_safe(800,1200,120,120,240));
    assert(!siege::backtrack_safe(1200,1200,120,600,240));
    assert(siege::yield_lane({18,15},{17,15},1000,1000,600,1200,12,13));
    assert(!siege::yield_lane({18,15},{17,15},1000,1000,1200,1200,12,13));
    assert(!siege::yield_lane({18,15},{17,15},1000,1000,600,1200,14,13));
    assert(!siege::yield_lane({20,15},{17,15},1000,1000,600,1200,12,13));
    macro::Context context{100,40,1,.25f,2};
    macro::Option farm{macro::Kind::Farm,0,10,-1,20,40,0,0,true};
    assert(macro::value(context,farm)==55); // Gold farming can continue while delivery is closed.
    gate::Commitment commitment;commitment.start(0,3,10,30,50);
    assert(!commitment.advance(30,10,30,false));
    const int deadline=commitment.deadline;
    assert(commitment.advance(51,17,36,true)&&commitment.ready);
    assert(commitment.advance(52,17,36,false)&&commitment.deadline==deadline); // Replanning cannot move its deadline.
    assert(!commitment.advance(deadline+1,17,36,false)&&!commitment.active());
    commitment.begin(0,100,500);const int project_deadline=commitment.deadline;
    commitment.begin(0,120,700);assert(commitment.executing&&commitment.deadline==project_deadline);
    std::cout<<"Layered/resumable opening routes, repeated visits, dependency/gear invalidation and gold continuation passed\n";
}
