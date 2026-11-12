#include "crew_cast.h"
#include <cassert>
#include <iostream>
#include <random>
using namespace dz;
int main() {
    std::mt19937 random(2047);
    for(unsigned trial=0;trial<600;++trial) {
        std::array<crew::Unit,3> actors{};const unsigned count=1+random()%3;
        crew::SequenceSearch plan;plan.stage=crew::SequenceSearch::Stage::Done;plan.count=1;plan.actors=count;plan.phases.resize(1);
        const float health=100+random()%4000;std::array<crew::Monster,1> monsters{{{0,{10,10},health,0,4}}};
        auto& phase=plan.phases[0];phase.target=monsters[0];
        for(unsigned u=0;u<count;++u) {
            actors[u]={u,u,{9,int(9+u)},10000,10000,float(20+random()%100),1,1};
            actors[u].kit.casts[0]={u%2?objective::CastKind::Damage:objective::CastKind::Reset,
                random()%5,1+random()%7,0,float(20+random()%150)};
            phase.formation.positions[u]=actors[u].p;plan.roster[u]=actors[u];
        }
        const auto pool=std::span(actors.data(),count);
        const auto bound=crew::quote(pool,monsters,plan,0,6,5,2000);assert(bound.complete);
        const auto work=crew::cast_work(pool,monsters,plan,0,6,5,bound.finish);assert(work.complete&&work.finish<=bound.finish);
        // Closed-form cumulative basics and reset/direct cooldown clocks.
        unsigned time=0;
        for(;time<2000;++time) {
            float damage=0;const unsigned turns=time+1;
            for(unsigned u=0;u<count;++u) {
                const auto spell=actors[u].kit.casts[0];
                const unsigned casts=turns>spell.cooldown?1+(turns-1-spell.cooldown)/spell.period:0;
                damage+=actors[u].damage*turns+casts*(spell.kind==objective::CastKind::Reset?actors[u].damage:spell.amount);
            }
            if(damage>=health)break;
        }
        assert(work.phases==static_cast<int>(time+1)&&work.finish==static_cast<int>(time+1)+1+6);
        assert(!crew::cast_work(pool,monsters,plan,0,6,5,bound.finish,-1,[]{return false;}).complete);
    }
    std::array<crew::Unit,1> actors{{{0,0,{9,10},1000,1000,100,1,1}}};
    actors[0].kit.casts={objective::Cast{objective::CastKind::Reset,0,4},objective::Cast{objective::CastKind::Shield,0,4,2,200}};
    std::array<crew::Monster,1> monsters{{{0,{10,10},500,100,4}}};
    crew::SequenceSearch plan;plan.stage=crew::SequenceSearch::Stage::Done;plan.count=plan.actors=1;plan.roster[0]=actors[0];plan.phases.resize(1);
    plan.phases[0].target=monsters[0];plan.phases[0].formation.positions[0]=actors[0].p;plan.phases[0].raw[0]=100;
    const auto bound=crew::quote(actors,monsters,plan,0,6,5,2000);assert(bound.complete);
    const auto work=crew::cast_work(actors,monsters,plan,0,6,5,bound.finish);
    const std::array<ClearMember,1> target{{{500,100}}};
    const auto reference=objective::cast_clear(target,1000,1000,100,actors[0].kit);
    assert(work.complete&&work.phases==static_cast<int>(reference.rounds)&&work.finish==static_cast<int>(reference.rounds)+7);
    assert(work.casts==reference.casts[0]+reference.casts[1]);
    actors[0].kit={};assert(!crew::cast_work(actors,monsters,plan,0,6,5,bound.finish).complete);
    std::cout<<"600 independent joint cooldown clocks; cast collisions, basic deadline bounds and budget fallback passed\n";
}
