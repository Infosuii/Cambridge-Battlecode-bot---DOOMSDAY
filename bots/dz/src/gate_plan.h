#pragma once
#include "siege_model.h"
#include "access_route.h"
#include <limits>

namespace dz::gate {
inline constexpr unsigned max_cuts=12;
struct Commitment {
    int altar=-1,resource=-1,bag=0,gold=0,deadline=0;
    bool ready=false,executing=false;
    bool project=false;int joint_group=-1;unsigned joint_crew=0;std::uint64_t joint_targets=0;
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
    void start_joint(int a,int group,unsigned crew,std::uint64_t targets,int carried,int cash,int now,int work) {
        const int finish=active()&&project&&altar==a?deadline:now+work+128;
        *this={};altar=a;bag=carried;gold=cash;deadline=finish;ready=executing=project=true;
        joint_group=group;joint_crew=crew;joint_targets=targets;
    }
};
enum class Quality { Building, Ready, Unsupported, Scout, Joint };
enum class Failure { None, Geometry, Capacity, Approach, Exit, Work, Window };
struct Cut {
    int group=-1,member=-1,arrival=0;
    Tile approach{},tile{};
    float hp=0,incoming=0,escape_loss=0;
    int escape_rounds=0,home=0;
    unsigned version=0;
    bool future=false;
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
    bool bank_future=false;
    Tile origin{},cursor{};
    std::array<Cut,max_cuts> cuts{};
    std::array<Work,max_cuts> solo{};
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
struct ProjectPrice { bool complete=false;int work=0,finish=0,replaced=0; };
// Replace one whole group with a checked crew quote. All other cuts retain
// their individually priced solo heal/return costs, in the original order.
// The crew pays a checked trip Home before those full-health continuations.
inline ProjectPrice replace_group(const Plan& p,int group,int joint,int home,int channel,int horizon,int until) {
    ProjectPrice q;
    if(!p.path_ready||!p.channel_ready||p.count==0||p.count>max_cuts||p.priced!=p.count||p.cuts[0].group!=group||
        joint<=0||home<0||channel<0||p.delivery<0||horizon<1||horizon>2000||until<1)return q;
    long long work=static_cast<long long>(joint)+home;int old=0;bool old_valid=true;
    for(unsigned c=0;c<p.count;++c) {
        if(p.cuts[c].group==group){old_valid&=p.solo[c].valid;if(p.solo[c].valid)old+=p.solo[c].rounds;++q.replaced;}
        else {if(!p.solo[c].valid)return {};work+=p.solo[c].rounds;}
    }
    if(old_valid&&joint+home>=old)return {}; // Extra helpers must improve the replaced leg.
    const long long finish=work+p.delivery+channel+1;
    if(work>2000||finish>std::min(horizon,until))return {};
    q.complete=true;q.work=work;q.finish=finish;return q;
}
}
