#include "engagement.h"
#include "gear_value.h"
#include "race.h"
#include "action_value.h"
#include <cassert>
#include <iostream>
using namespace dz;
int main() {
    auto open=[](int,int){return true;};
    combat::Unit me;me.hp=me.max_hp=1000;me.damage=100;
    auto enemy=me;enemy.side=1;enemy.x=1;
    std::array<combat::Unit,3> scene{me,enemy,me};
    auto actors=std::span<const combat::Unit>(scene.data(),2);
    auto result=combat::project(actors,1,false,open,4);
    assert(result.valid&&result.our_loss==400&&result.their_loss==400);
    int work=0;
    assert(!combat::project(actors,1,false,open,4,false,0,0,[&]{return ++work<2;}).valid);
    scene[0].spells[0]={combat::Kind::Reset,0,0,0,8};
    result=combat::project(actors,1,false,open,4);assert(result.their_loss==500);
    scene[0].spells[0].cooldown=8;
    result=combat::project(actors,1,false,open,4);assert(result.their_loss==400);
    scene[0].spells[0]={combat::Kind::Shield,200,0,0,8,2};
    result=combat::project(actors,1,false,open,4);assert(result.our_loss==200); // Two attacks absorbed before expiry.
    // Re-evaluate shield comparison rather than assume damage is shared.
    scene[0].spells[0]={combat::Kind::Shield,100,0,0,8,2};
    result=combat::project(actors,1,false,open,4);assert(result.our_loss==300);
    scene[0].spells[0]={};scene[1].x=6;scene[2].x=-8;scene[2].damage=1000;
    const auto alone=combat::project(std::span<const combat::Unit>(scene.data(),2),1,false,open,4);
    const auto far_support=combat::project(scene,1,false,open,4);
    assert(far_support.their_loss==alone.their_loss); // Distant ally is not instant DPS.
    scene[0].x=0;scene[1].x=2;scene[0].range=2;scene[0].ranged=true;
    scene[0].can_attack=false;scene[0].can_move=false;
    result=combat::project(actors,1,false,open,1);assert(result.their_loss==0);
    scene[0].can_attack=true;result=combat::project(actors,1,false,open,1);assert(result.their_loss==100);
    scene[0].range=1;scene[0].can_move=true;scene[0].x=0;scene[1].x=5;
    auto wall=[](int x,int){return x!=1;};
    result=combat::project(actors,1,false,wall,1);assert(result.their_loss==0);
    scene[0].hp=-1;assert(!combat::project(actors,1,false,open).valid);
    scene={me,enemy,enemy};scene[1].retaliation=20;
    result=combat::project(actors,1,false,open,1);assert(result.our_loss==120);
    scene={me,enemy,enemy};scene[0].splash=true;scene[2].x=2;
    result=combat::project(scene,1,false,open,1);assert(result.their_loss==200);
    scene={me,enemy,me};scene[2].x=-2;scene[0].hp=50;scene[0].linked=2;scene[2].linked=0;
    result=combat::project(scene,1,true,open,1);assert(result.our_dead==2&&result.self_hp==0);
    gear::Context context;gear::Project project;project.damage_growth=.1f;
    const auto long_value=gear::utility(context,project);context.remaining=20;
    assert(gear::utility(context,project)<long_value);
    context.remaining=1000;project.passive=gear::Passive::Prospector;project.magnitude=.25f;project.damage_growth=0;
    context.cluster_fraction=0;assert(gear::utility(context,project)==0);
    context.cluster_fraction=1;assert(gear::utility(context,project)>0);
    project.shards_left=0;assert(gear::utility(context,project)==0);
    RaceClock race;race.observe(0,0,0);race.observe(100,100,100);
    assert(race.remaining(100,2000,1000,0)==1900);
    race.observe(200,800,900);assert(race.remaining(200,2000,1000,0)<150);
    auto before=race.sampled;race.observe(199,10,10);assert(race.sampled==before);
    ActionValue action;action.rounds_saved=1;
    const float safe=action_value(action);action.incoming=100;action.hp=100;
    assert(action_value(action)<safe);
    std::cout<<"Combat range/support, cooldown, shield, ranged action, terrain and gear-horizon checks passed\n";
}
