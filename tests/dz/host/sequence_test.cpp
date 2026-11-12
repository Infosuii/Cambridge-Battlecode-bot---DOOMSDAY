#include "crew_sequence.h"
#include <cassert>
#include <iostream>
#include <queue>
#include <random>
using namespace dz;
int main() {
    std::mt19937 rng(1207);
    for(unsigned trial=0;trial<120;++trial) {
        std::array<bool,144> walls{};for(auto& w:walls)w=rng()%5==0;
        const Tile from{1,1},to{10,10};walls[13]=walls[130]=false;
        auto open=[&](Tile p){return p.x>=0&&p.y>=0&&p.x<12&&p.y<12&&!walls[p.y*12+p.x];};
        std::array<int,144> distance;distance.fill(-1);distance[13]=0;
        std::queue<Tile> queue;queue.push(from);
        while(!queue.empty()) {
            const auto p=queue.front();queue.pop();
            for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy) {
                const Tile q{p.x+dx,p.y+dy};if(!open(q)||distance[q.y*12+q.x]>=0)continue;
                distance[q.y*12+q.x]=distance[p.y*12+p.x]+1;queue.push(q);
            }
        }
        crew::RouteSearch route;route.begin(from,to,12,12);unsigned slices=0;
        while(route.status==crew::RouteSearch::Status::Pending&&slices++<10000) {
            unsigned ops=0;route.resume(open,[&]{return ++ops<=3;});
        }
        assert(slices<10000);
        if(distance[130]<0)assert(route.status==crew::RouteSearch::Status::Unreachable);
        else {
            assert(route.status==crew::RouteSearch::Status::Complete&&route.path.size()==static_cast<unsigned>(distance[130]));
            Tile p=from;for(auto q:route.path){assert(open(q)&&cheb(p,q)==1);p=q;}assert(p==to);
        }
    }
    std::array<crew::Unit,2> units{{{0,1,{2,2},10000,10000,100,1,1},{1,2,{3,2},10000,10000,100,1,1}}};
    const std::array<crew::Monster,2> camps{{{0,{10,10},300,20,3},{1,{15,10},500,30,3}}};
    auto open=[](Tile p,unsigned){return p.x>=0&&p.y>=0&&p.x<28&&p.y<24;};
    auto home=[](Tile p){return cheb(p,{2,2});};
    crew::SequenceSearch search;search.begin(units,camps,28,24);unsigned slices=0;
    while(search.pending()&&slices++<100000) {
        unsigned ops=0;const auto complete=search.resume(units,camps,open,home,[&]{return ++ops<=4;});
        if(search.pending())assert(!complete&&!crew::quote(units,camps,search,0,6,5,2000).complete);
    }
    assert(search.stage==crew::SequenceSearch::Stage::Done&&search.count==2&&slices>10&&slices<100000);
    const auto q=crew::quote(units,camps,search,0,6,5,2000);
    assert(q.complete&&q.finish>6+search.phases[0].approach_rounds+search.phases[1].transfer);
    const auto first=search.phases[0].formation;
    assert(!crew::forecast(units,camps,first).complete); // Old all-target fixed geometry rejects this encounter.
    for(unsigned phase=0;phase<2;++phase) {
        const auto& p=search.phases[phase];auto actual=phase?search.phases[phase-1].formation.positions:p.staging;
        unsigned steps=0;
        while(steps++<1000) {
            const auto march=phase?crew::march(search.phases[phase-1],p,std::span<const Tile>(actual.data(),units.size())):
                crew::approach(p,std::span<const Tile>(actual.data(),units.size()));
            assert(march.valid);if(march.complete)break;
            assert(cheb(actual[march.actor],march.next)==1);
            for(unsigned u=0;u<units.size();++u)if(u!=march.actor)assert(actual[u]!=march.next);
            for(unsigned c=phase;c<camps.size();++c)assert(camps[c].p!=march.next);
            actual[march.actor]=march.next;
        }
        assert(steps<1000);
        for(unsigned u=0;u<units.size();++u)assert(actual[u]==p.formation.positions[u]);
        // Independent nearest-target damage adapter, already checked against
        // native camp targeting, prices every planned serial movement phase.
        auto check_loss=[&](const auto& moves,auto positions,const auto& recorded) {
            std::array<double,crew::max_units> loss{};
            std::array<CampThreat,2> threats{};unsigned count=0;
            for(unsigned c=phase;c<camps.size();++c)threats[count++]={camps[c].p,camps[c].damage,camps[c].range};
            for(const auto& move:moves)for(auto point:move.path) {
                positions[move.actor]=point;
                for(unsigned u=0;u<units.size();++u) {
                    std::array<siege::Support,crew::max_units> allies{};unsigned n=0;
                    for(unsigned a=0;a<units.size();++a)if(a!=u)allies[n++]={positions[a],units[a].handle,100000,100000};
                    const auto hit=siege::incoming(positions[u],units[u].handle,std::span<const CampThreat>(threats.data(),count),
                        std::span<const siege::Support>(allies.data(),n));
                    assert(hit.valid);loss[u]+=hit.current*units[u].factor;
                }
            }
            assert(loss==recorded);
        };
        check_loss(p.approach,p.staging,p.approach_loss);
        if(phase)check_loss(p.moves,search.phases[phase-1].formation.positions,p.transfer_loss);
    }
    auto injured=units;for(auto& u:injured)u.hp=1;
    const auto recovery=crew::quote(injured,camps,search,0,6,5,2000);
    assert(recovery.complete&&recovery.visits>q.visits&&recovery.finish>q.finish);
    auto weak=units;for(auto& u:weak)u.hp=u.max_hp=100;
    assert(!crew::quote(weak,camps,search,0,6,5,2000).complete);
    assert(!crew::quote(units,camps,search,0,6,5,2000,[]{return false;}).complete);
    auto invalid=camps;invalid[0].hp=std::numeric_limits<float>::quiet_NaN();
    assert(!crew::quote(units,invalid,search,0,6,5,2000).complete);
    assert(!crew::quote(units,camps,search,~0u,6,5,2000).complete);
    auto changed=units;changed[0].damage+=1;assert(!crew::quote(changed,camps,search,0,6,5,2000).complete);
    crew::SequenceSearch blocked;blocked.begin(units,camps,28,24);unsigned iterations=0;
    while(blocked.pending()&&iterations++<100000) {
        unsigned ops=0;blocked.resume(units,camps,[](Tile p,unsigned){return p.x>=0&&p.y>=0&&p.x<28&&p.y<24&&p.x!=12;},home,[&]{return ++ops<=8;});
    }
    assert(blocked.stage==crew::SequenceSearch::Stage::Failed);
    // Swapping two occupied roles needs a real parking move; the controller
    // must execute the exact collision-free prefix and recognise completion.
    crew::SequenceSearch swap;swap.phase=1;swap.count=1;swap.width=swap.height=12;
    swap.stage=crew::SequenceSearch::Stage::Select;swap.phases.resize(2);swap.positions[0]={5,5};swap.positions[1]={5,6};
    swap.phases[0].formation.positions=swap.positions;
    swap.phases[1].formation.positions[0]={5,6};swap.phases[1].formation.positions[1]={5,5};
    const std::array<crew::Monster,2> harmless{{{0,{1,1},1,0,0},{1,{10,10},1,0,0}}};
    unsigned swaps=0;while(swap.pending()&&swaps++<10000){unsigned ops=0;swap.resume(units,harmless,[](Tile p,unsigned){return p.x>=0&&p.y>=0&&p.x<12&&p.y<12;},home,[&]{return ++ops<=5;});}
    assert(swap.stage==crew::SequenceSearch::Stage::Done&&swap.phases[1].moves.size()==3);
    auto positions=swap.phases[0].formation.positions;
    for(unsigned step=0;step<100;++step) {
        const auto move=crew::march(swap.phases[0],swap.phases[1],std::span<const Tile>(positions.data(),2));assert(move.valid);
        if(move.complete)break;
        assert(cheb(positions[move.actor],move.next)==1&&positions[1-move.actor]!=move.next);positions[move.actor]=move.next;
    }
    assert(positions[0]==Tile(5,6)&&positions[1]==Tile(5,5));
    positions[0]={0,0};assert(!crew::march(swap.phases[0],swap.phases[1],std::span<const Tile>(positions.data(),2)).valid);
    std::cout<<"120 independent BFS references; resumed multi-focus geometry, paid serial marches, recovery and disconnected rejection passed\n";
}
