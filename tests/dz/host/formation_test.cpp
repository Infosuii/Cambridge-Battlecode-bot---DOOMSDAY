#include "formation.h"
#include "formation_search.h"
#include "core.h"
#include "allocation.h"
#include <cassert>
#include <iostream>
#include <random>
using namespace dz;
int main() {
    assert(requested_navigation_fits(50000,30000,true));
    assert(!requested_navigation_fits(50000,30000,false));
    assert(!requested_navigation_fits(44000,30000,true));
    std::array<crew::Unit,3> units{{{0,10,{0,0},1000,1000,50,1,3},
        {1,11,{0,0},1000,1000,30,1,1},{2,12,{0,0},2000,2000,20,.5f,1}}};
    const crew::Monster monster[]{{0,{0,0},4000,20,3}};
    auto open=[](Tile p){return std::abs(p.x)<=20&&std::abs(p.y)<=20;};
    auto home=[](Tile p){return cheb(p,{-10,-10});};
    auto f=crew::arrange(units,monster,0,open,home);
    crew::FormationSearch search;search.begin(units,monster);crew::Formation resumed;
    unsigned slices=0;
    while(search.pending()&&slices<1000) {
        unsigned ops=0;resumed=search.resume(units,monster,open,home,[&]{return ++ops<=2;});++slices;
        if(search.pending())assert(!resumed.valid);
    }
    assert(resumed.valid&&slices>2&&slices<1000);
    assert(crew::camp_target(monster[0],units,resumed)==static_cast<int>(resumed.tank));
    assert(crew::forecast(units,monster,resumed).complete);
    const auto done=search.resume(units,monster,open,home,[]{return false;});assert(done.positions==resumed.positions);
    search.begin(units,monster);
    unsigned turns=0;while(search.pending()&&turns++<1000){unsigned ops=0;search.resume(units,monster,[](Tile){return false;},home,[&]{return ++ops<=1;});}
    assert(!search.pending()&&!search.result.valid&&search.stage==crew::FormationSearch::Stage::Failed);
    assert(f.valid&&f.tank==2&&(f.active&5)==5&&!(f.active&2));
    assert(crew::camp_target(monster[0],units,f)==2);
    assert(cheb(f.positions[0],monster[0].p)<=units[0].range&&cheb(f.positions[2],monster[0].p)==1);
    const auto start=f.positions[f.tank];const int dx=(f.exit.x>start.x)-(f.exit.x<start.x),dy=(f.exit.y>start.y)-(f.exit.y<start.y);
    for(int step=0;step<=f.escape_steps;++step)assert(f.positions[0]!=Tile(start.x+step*dx,start.y+step*dy));
    auto q=crew::forecast(units,monster,f);
    assert(q.complete&&q.survivable&&q.clear==58&&q.loss[0]==0&&q.loss[2]==570);
    const auto original=f.positions;
    auto reordered=units;std::swap(reordered[0],reordered[2]);
    const auto r=crew::arrange(reordered,monster,0,open,home);
    assert(r.valid&&r.positions[0]==original[2]&&r.positions[2]==original[0]);
    units[2].hp=1000;const auto stable=crew::arrange(units,monster,0,open,home);
    assert(stable.tank==2&&stable.positions==original);
    assert(!crew::forecast(units,monster,stable).survivable); // Withdraw/reform; do not oscillate roles on HP every turn.
    unsigned budget=0;assert(!crew::arrange(units,monster,0,open,home,[&]{return ++budget<3;}).valid);
    units[2].hp=2000;units[0].damage=std::numeric_limits<float>::quiet_NaN();
    assert(!crew::forecast(units,monster,f).complete);units[0].damage=50;
    // A two-quote budget must eventually try four/five-body crews, rather than
    // repeating only the same failing sizes on every planning turn.
    const std::array<crew::Unit,5> coalition{{{0,0,{},1000,1000,5,1,3},
        {1,1,{},500,500,5,1,1},{2,2,{},500,500,5,1,1},{3,3,{},3000,3000,100,1,1},{4,4,{},1000,1000,50,1,3}}};
    const crew::Monster boss[]{{0,{0,0},5000,20,3}};
    unsigned next=2,accepted=0,attempts=0;
    for(unsigned planning_turn=0;planning_turn<3&&!accepted;++planning_turn)for(unsigned allowance=0;allowance<2&&!accepted;++allowance) {
        const unsigned count=next;const auto group=std::span<const crew::Unit>(coalition.data(),count);
        auto formation=crew::arrange(group,boss,0,open,home);auto quote=crew::forecast(group,boss,formation);
        ++attempts;next=economy::next_coalition_size(count,coalition.size());
        if(quote.complete&&quote.survivable)accepted=count;
    }
    assert(accepted==4&&attempts==3);
    std::array<crew::Unit,2> melee{{{0,1,{},1000,1000,100,1,1},{1,2,{},2000,2000,20,1,1}}};
    const crew::Monster strong[]{{0,{0,0},4000,10,3}};
    const auto discarded=crew::arrange(melee,strong,0,open,home);
    assert(!(discarded.active&1u)&&!crew::forecast(melee,strong,discarded).survivable);
    auto selected=crew::choose(melee,strong,0,open,home);
    assert(selected.valid&&selected.tank==0&&selected.active==3&&crew::forecast(melee,strong,selected).survivable);
    melee[0].hp=400;const auto fixed_role=crew::choose(melee,strong,0,open,home);
    auto moving=melee;moving[0].p={12,12};moving[0].arrival=20;moving[0].hp=200;
    assert(crew::same_roles(moving,melee));moving[0].damage+=1;assert(!crew::same_roles(moving,melee));
    const crew::Monster wounded[]{{0,{0,0},200,10,3}};assert(crew::same_scene(wounded,strong));
    const crew::Monster dead[]{{0,{0,0},0,10,3}};assert(!crew::same_scene(dead,strong));
    assert(fixed_role.positions==selected.positions&&fixed_role.tank==selected.tank&&!crew::forecast(melee,strong,fixed_role).survivable);
    melee={{{0,1,{},1000,1000,30,1,1},{1,2,{},1000,1000,30,1,1}}};
    const crew::Monster elk[]{{0,{0,0},2400,60,3}};
    selected=crew::choose(melee,elk,0,open,home);assert(selected.valid&&!crew::forecast(melee,elk,selected).survivable);
    auto visit=crew::visit(melee,elk,selected,5,open,home);
    assert(visit.complete&&visit.attacks>0&&visit.waves>1&&visit.ready==3&&visit.finish>crew::forecast(melee,elk,selected).finish);
    melee[0].hp=200;visit=crew::visit(melee,elk,selected,5,open,home);
    assert(visit.complete&&visit.attacks==0&&visit.ready==2); // Only the exhausted actor must heal.
    assert(!crew::visit(melee,elk,selected,5,[](Tile){return false;},home).complete);
    assert(!crew::visit(melee,elk,selected,5,open,home,[]{return false;}).complete);
    // Exact independent camp-phase simulator for every order of three targets.
    // The closed form uses a different worst order for each actor; every actual
    // order must stay below all those actor bounds.
    std::mt19937 rng(202611);unsigned cases=0;
    for(unsigned trial=0;trial<200;++trial) {
        std::array<crew::Monster,3> camps{{{0,{1,0},float(1+rng()%300),float(1+rng()%30),3},
            {1,{1,1},float(1+rng()%300),float(1+rng()%30),3},{2,{2,0},float(1+rng()%300),float(1+rng()%30),3}}};
        std::array<crew::Unit,2> actors{{{0,2,{0,0},10000,10000,20,.5f,3},{1,1,{0,1},10000,10000,30,1,3}}};
        crew::Formation fixed;fixed.valid=true;fixed.active=3;fixed.positions[0]=actors[0].p;fixed.positions[1]=actors[1].p;
        auto bound=crew::forecast(actors,camps,fixed);assert(bound.complete&&bound.survivable);
        std::array<unsigned,3> order{0,1,2};
        do {
            std::array<float,3> hp;for(unsigned c=0;c<3;++c)hp[c]=camps[c].hp;
            std::array<double,2> loss{};int ticks=0;
            for(auto focus:order)while(hp[focus]>0) {
                for(const auto& actor:actors)if(cheb(actor.p,camps[focus].p)<=actor.range)hp[focus]-=actor.damage;
                ++ticks;
                for(unsigned c=0;c<3;++c)if(hp[c]>0) {
                    int nearest=4,target=-1;
                    for(unsigned u=0;u<2;++u) {
                        const int d=cheb(actors[u].p,camps[c].p);
                        if(d<nearest||(d==nearest&&(target<0||actors[u].handle<actors[target].handle))){target=u;nearest=d;}
                    }
                    if(nearest<=3)loss[target]+=camps[c].damage*actors[target].factor;
                }
            }
            assert(ticks==bound.clear&&loss[0]<=bound.loss[0]&&loss[1]<=bound.loss[1]);++cases;
        }while(std::next_permutation(order.begin(),order.end()));
    }
    std::cout<<cases<<" stationary encounter/order references; roles, range, tank ties, reserved exits and invalid inputs passed\n";
}
