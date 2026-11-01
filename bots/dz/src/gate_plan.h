#pragma once
#include "siege_model.h"
#include "access_route.h"
#include <limits>

namespace dz::gate {
inline constexpr unsigned max_cuts=12;
struct Commitment {
    int altar=-1,resource=-1,bag=0,gold=0,deadline=0;
    bool ready=false,executing=false;
    bool active() const { return altar>=0; }
    void start(int a,int job,int carried,int cash,int finish) { *this={a,job,carried,cash,finish+128,job<0,false}; }
    void begin(int a,int round,int work) {
        if(executing)return; // Later layers cannot slide the project's deadline.
        altar=a;resource=-1;ready=true;executing=true;deadline=round+work+128;
    }
    bool advance(int round,int carried,int cash,bool resource_done) {
        if(!active())return false;
        if(round>deadline){*this={};return false;}
        ready|=resource_done||carried>bag||cash>gold;
        return ready;
    }
};
enum class Quality { Building, Ready, Unsupported, Scout };
enum class Failure { None, Geometry, Capacity, Approach, Exit, Work, Window };
struct Cut {
    int group=-1,member=-1,arrival=0;
    Tile approach{},tile{};
    float hp=0,incoming=0,escape_loss=0;
    int escape_rounds=0,home=0;
    unsigned version=0;
};
struct Work { bool valid=false;int attacks=0,visits=0,rounds=0; };
// A full-health, solo, basic-attack itinerary. Every visit ends with a checked
// escape, walking Home and one healing tick. No permanent ally tank, future
// shield/reset cast, death-as-transport or equal damage share is credited.
// Geometry and arrival are adapter estimates; this is NOT strike admission.
inline Work price(const Cut& cut,float hp,float max_hp,float damage,int horizon=2000) {
    if(cut.arrival<0||cut.escape_rounds<0||cut.home<0||horizon<1||horizon>2000)return {};
    const auto wave=siege::quote(hp,max_hp,cut.hp,damage,cut.incoming,cut.escape_loss,horizon);
    if(!wave.valid)return {};
    const long long recovery=static_cast<long long>(cut.escape_rounds)+cut.home+1;
    const long long rounds=static_cast<long long>(cut.arrival)+wave.needed+wave.waves*recovery+
        static_cast<long long>(wave.waves-1)*cut.home;
    if(rounds>horizon)return {};
    return {true,wave.needed,wave.waves,static_cast<int>(rounds)};
}
struct Plan {
    Quality quality=Quality::Building;
    Failure failure=Failure::None;
    int altar=-1,started=-1,expires=-1,travel=0,rounds=0,visits=0,delivery=0;
    unsigned revision=~0u,count=0,priced=0;
    float max_hp=-1,damage=-1,factor=-1;
    int range=-1;
    Tile origin{},cursor{};
    std::array<Cut,max_cuts> cuts{};
    struct Dependency { int group=-1,member=-1,ready=0;bool alive=false,respawning=false; };
    static bool dependency_matches(const Dependency& d,bool alive,bool respawning,int ready) {
        return alive==d.alive&&respawning==d.respawning&&(!respawning||ready==d.ready);
    }
    std::array<Dependency,128> dependencies{};
    unsigned dependency_count=0;
    bool path_ready=false,origin_ready=false,channel_ready=false;
    access::ApproachSearch approach_search;
    int approach_group=-1,approach_member=-1;Tile channel_approach{};
    void reset(int round,unsigned topology,float health,float dps,float mitigation,int attack_range) {
        *this={};started=round;expires=round+128;revision=topology;max_hp=health;damage=dps;factor=mitigation;range=attack_range;
    }
    bool matches(int round,unsigned topology,float health,float dps,float mitigation,int attack_range) const {
        (void)topology; // Only path dependencies invalidate geometry; distant farming must not restart it.
        return round<expires&&max_hp==health&&damage==dps&&factor==mitigation&&range==attack_range;
    }
};
}
