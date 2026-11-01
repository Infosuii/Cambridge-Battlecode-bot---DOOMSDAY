#include "siege_model.h"
#include "access_route.h"
#include <array>
#include <cassert>
#include <iostream>
#include <random>
using namespace dz;
int main() {
    assert(siege::bridge_affordable(1000,1000,120,60,100,200));
    assert(!siege::bridge_affordable(650,1000,120,60,100,200));
    assert(!siege::bridge_affordable(1000,1000,120,0,100,200));
    assert(!siege::bridge_affordable(1000,1000,120,60,100,600));
    auto wave=siege::quote(1000,1000,5000,50,120,240);
    assert(wave.valid&&wave.attacks<100&&wave.waves>1);
    assert(1000-wave.attacks*120>wave.reserve);
    assert(!siege::quote(400,1000,5000,50,120,240).valid);
    assert(!siege::quote(1000,1000,5000,0,120,240).valid);
    assert(!siege::quote(1000,1000,5000,50,120,240,0).valid);
    assert(!siege::quote(1000,1000,5000,50,-1,240).valid);
    auto resource=siege::quote(1000,1000,120,50,0,0);assert(resource.valid&&resource.attacks==3);
    std::mt19937 rng(106);unsigned visits=0;
    // Independent step-by-step health accounting: repeated visits must reduce
    // persistent target HP, retain the reserved escape HP, and eventually clear.
    for(unsigned test=0;test<2000;++test) {
        float target=100+float(rng()%12000),health=800+float(rng()%1000),damage=30+float(rng()%100);
        const float incoming=20+float(rng()%100),escape=2*incoming;
        const auto first=siege::quote(health,health,target,damage,incoming,escape);
        if(!first.valid)continue;
        int loop=0;
        while(target>0&&loop<2000) {
            auto current=siege::quote(health,health,target,damage,incoming,escape);assert(current.valid);
            float hp=health,old=target;
            for(int attack=0;attack<current.attacks;++attack){target=std::max(0.f,target-damage);hp-=incoming;}
            hp-=incoming;hp-=escape;
            assert(hp>.15f*health);assert(target<old);++visits;++loop;
        }
        assert(target==0);
    }
    siege::Task task;task.start(4,2,20,10,5000);
    assert(task.active()&&task.progress(25,9,5000));
    assert(task.progress(54,9,4950));assert(!task.progress(85,9,4950));
    task.reset(90,20);assert(!task.active()&&task.retry_after==110);
    std::array threats{CampThreat{{0,0},120,4}};
    auto route=camp_escape(Tile{1,0},threats,[](Tile,int){return true;});
    assert(route.found&&route.damage==360&&camp_damage(route.exit,threats)==0);
    std::array directions{Tile{-1,0},Tile{1,0}};
    auto fast=siege::escape_route({1,0},threats,directions,[](Tile){return true;});
    assert(fast.found&&camp_damage(fast.exit,threats)==0);
    const Tile direction{(fast.exit.x>1)-(fast.exit.x<1),(fast.exit.y>0)-(fast.exit.y<0)};
    float sum=0;for(int step=1;step<=fast.steps;++step)sum+=camp_damage({1+step*direction.x,step*direction.y},threats);
    assert(sum==fast.damage&&fast.damage==360);
    // Frozen native death geometry: a recovering body at(20,15) must take the
    // checked diagonal to zero exposure, not bounce toward the occupied east tile.
    const std::array native_camps{CampThreat{{14,15},120,4},CampThreat{{16,15},120,4}};
    auto native_open=[](Tile p) {
        return p.x>=0&&p.y>=0&&p.x<31&&p.y<31&&p!=Tile{21,15}&&
            !((p.y==14||p.y==16)&&p.x>=12&&p.x<=18);
    };
    const std::array native_directions{Tile{1,1},Tile{1,-1},Tile{1,0},Tile{-1,1},Tile{-1,0},Tile{-1,-1},Tile{0,1},Tile{0,-1}};
    const auto native_exit=siege::escape_route({20,15},native_camps,native_directions,native_open);
    assert((native_exit.found&&native_exit.exit==Tile{21,16}&&native_exit.damage==0));
    siege::EscapeStep certified;assert(certified.arm(1230,{20,15},native_exit));
    assert((certified.round==1230&&certified.origin==Tile{20,15}&&certified.next==Tile{21,16}));
    assert(!certified.arm(1231,{20,15},{{22,16},0,2,true,false})); // Non-ray endpoint cannot authorize a direct step.
    const auto kept=siege::retained_escape({16,15},{21,15},native_camps,[](Tile){return true;});
    assert(kept.found&&kept.damage==720&&kept.steps==5);
    assert(!siege::retained_escape({16,15},{21,15},native_camps,[](Tile p){return p!=Tile{19,15};}).found);
    assert(!siege::retained_escape({16,15},{21,16},native_camps,[](Tile){return true;}).found);
    const auto cut=siege::retained_escape({16,15},{21,15},native_camps,[](Tile){return true;},[]{return false;});
    assert(!cut.found&&cut.truncated);
    assert(!siege::withdrawal_safe(530,0,120)); // Observed R1377 safe-cell re-entry.
    assert(siege::withdrawal_safe(530,0,0)&&siege::withdrawal_safe(530,240,120));
    assert(!siege::withdrawal_safe(120,240,120)&&!siege::withdrawal_safe(530,120,240));
    int calls=0;
    auto interrupted=siege::escape_route({1,0},threats,directions,[](Tile){return true;},[&]{return ++calls<3;});
    assert(interrupted.found&&interrupted.truncated&&camp_damage(interrupted.exit,threats)==0);
    assert(!siege::quote(850,850,5000,50,240,720).valid); // Cannot fund one hit plus exit.
    std::array two{CampThreat{{0,0},120,4},CampThreat{{2,0},120,4}};
    std::array ally{siege::Support{{-1,0},0,1000,1000}};
    auto protected_damage=siege::incoming({-1,-1},1,two,ally);
    assert(protected_damage.valid&&protected_damage.raw==240&&protected_damage.current==0&&protected_damage.protected_camps==2);
    auto tie=siege::incoming({-1,-1},0,two,std::array{siege::Support{{-1,0},1,1000,1000}});
    assert(tie.current==240); // Equal distance: lower native handle takes the hits.
    ally[0].hp=100;auto unsupported=siege::incoming({-1,-1},1,two,ally);assert(unsupported.current==240);
    auto rear=siege::quote(1000,1000,5000,50,0,480,2000,240);
    assert(rear.valid&&rear.reserve==990); // One full surprise phase plus SOLO escape remains reserved.
    assert(!siege::incoming({-1,-1},1,two,ally,.5f).valid);
    assert(!siege::quote(1000,1000,5000,50,0,480,2000,-2).valid);
    const auto shielded=siege::quote(1000,1000,5000,50,240,480,2000,240,240);
    assert(shielded.valid&&shielded.attacks==1);
    assert(!siege::quote(1000,1000,5000,50,240,480,2000,240,241).valid);
    float hp=1000;float shield=240;
    for(int attack=0;attack<shielded.attacks;++attack){const float absorbed=std::min(shield,240.f);shield-=absorbed;hp-=240-absorbed;}
    hp-=240+480;assert(hp>150); // Independent shield absorption, surprise, and escape accounting.
    bool outer=true,inner=true;
    auto distance=[](Tile p){return p.y==0&&p.x>=0&&p.x<=6?6-p.x:65535;};
    auto blocking=[&](Tile p) {
        if(p.x==2&&outer)return access::Blocker{0,0,1};
        if(p.x==4&&inner)return access::Blocker{1,0,100};
        return access::Blocker{};
    };
    auto path=access::inspect({0,0},distance,blocking);assert(path.status==access::Status::Blocked&&path.blocker.group==0);
    outer=false;path=access::inspect({0,0},distance,blocking);assert(path.status==access::Status::Blocked&&path.blocker.group==1);
    inner=false;path=access::inspect({0,0},distance,blocking);assert(path.status==access::Status::Clear&&path.steps==6);
    path=access::inspect({0,0},distance,blocking,access::Unlimited{},2);assert(path.status==access::Status::Unknown);
    path=access::inspect({-1,0},distance,blocking);assert(path.status==access::Status::Unreachable);
    std::cout<<visits<<" simulated heal-return visits; siege reserve, completion and contract checks passed\n";
}
