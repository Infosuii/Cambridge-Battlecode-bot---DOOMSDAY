#pragma once
#include "protocol.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <limits>

namespace dz::team {
// Prefix codes use the same22 metadata bits without aliasing frame kinds:
// role/ready0, roster10, lease110, cash1110, project1111. Scheduled frames
// encode their absolute six-round index, never a modulo-age timestamp.
enum class Kind : unsigned { None=0, Lease=1, Cash=2, Project=3, Role=4, Roster=5, Ready=6, Focus=7 };
enum class Intent : unsigned { Active=0, Recover=1, Released=2, Dead=3 };
inline constexpr unsigned gold_quantum=8;
constexpr unsigned lifetime(unsigned count) {return 6*count+2;}
constexpr unsigned agreement_window(unsigned count) {return 2*lifetime(count)+6;}
constexpr unsigned publisher(unsigned round,unsigned count) {
    return count&&count<=protocol::slots&&round<=2047&&!(round&1)?(round/6)%count:protocol::slots;
}
constexpr Kind scheduled(unsigned round) {return (round/2)%3==0?Kind::Cash:(round/2)%3==1?Kind::Project:Kind::Lease;}
constexpr bool protected_lease(std::uint64_t word,unsigned now,unsigned count) {
    const auto lease=protocol::compact::lease(word,now);
    if(!lease.valid)return false;
    const bool scheduled_cohort=scheduled(lease.round)==Kind::Lease&&publisher(lease.round,count)==lease.leader;
    return !scheduled_cohort||now-lease.round<2;
}
struct Frame {
    Kind kind=Kind::None;unsigned slot=protocol::slots,round=0;
    unsigned gold=0,task=protocol::idle;Intent intent=Intent::Released;
    unsigned members=0,phase=0;int dx=0,dy=0;
    bool valid=false;
};
constexpr Frame decode(std::uint64_t word,unsigned now,unsigned count) {
    Frame f;unsigned index=0,offset=0;
    if(!count||count>protocol::slots||now>2047)return f;
    if(!(word>>63)) {
        const unsigned code=(word>>42)&63;f.phase=(word>>48)&63;index=(word>>54)&511;
        if(code==50){f.kind=Kind::Ready;offset=4;}
        else if(code==51||code==52){f.kind=Kind::Focus;offset=code==52?4:0;}
        else if(code>=1&&code<=49&&code!=25){f.kind=Kind::Role;f.dx=static_cast<int>((code-1)/7)-3;f.dy=static_cast<int>((code-1)%7)-3;}
        else return f;
    } else if((word>>62)==2) {f.kind=Kind::Roster;index=(word>>53)&511;f.phase=(word>>47)&63;offset=2;}
    else if((word>>60)>=14) {
        f.kind=(word>>60)==14?Kind::Cash:Kind::Project;index=(word>>51)&511;
        if(f.kind==Kind::Cash)f.gold=((word>>42)&511)*gold_quantum;
        else {f.task=(word>>42)&127;f.intent=static_cast<Intent>((word>>49)&3);offset=2;}
    } else return f;
    f.round=6*index+offset;
    if(f.round>now||now-f.round>lifetime(count)||publisher(f.round,count)==protocol::slots)return f;
    f.slot=publisher(f.round,count);
    if(f.kind==Kind::Focus&&protocol::compact::slot(word,f.slot).objective!=protocol::fight)return {};
    if(f.kind==Kind::Roster)f.members=protocol::compact::unpack_members((word>>42)&31,f.slot);
    if(f.kind==Kind::Role||f.kind==Kind::Roster||f.kind==Kind::Ready) {
        f.task=protocol::compact::slot(word,f.slot).objective;
        if(!protocol::is_group_code(f.task))return f;
    }
    f.valid=true;return f;
}
constexpr std::uint64_t publish(std::uint64_t word,unsigned now,unsigned count,unsigned slot,
                                unsigned gold,unsigned task,Intent intent) {
    if(slot>=count||slot>=protocol::slots||task>127||static_cast<unsigned>(intent)>3||publisher(now,count)!=slot||
        protected_lease(word,now,count)||scheduled(now)==Kind::Lease)return word;
    const auto kind=scheduled(now);
    const unsigned data=kind==Kind::Cash?std::min(511u,gold/gold_quantum):(task&127)|(static_cast<unsigned>(intent)<<7);
    constexpr auto claims=(std::uint64_t{1}<<42)-1;
    return (word&claims)|(std::uint64_t{data}<<42)|(std::uint64_t{now/6}<<51)|
        (std::uint64_t{kind==Kind::Cash?14u:15u}<<60);
}
constexpr std::uint64_t acknowledge(std::uint64_t word,unsigned now,unsigned count,unsigned slot,
                                   unsigned members,unsigned phase,int dx,int dy,bool ready) {
    const auto lease=protocol::compact::lease(word,now);
    if(slot>=count||slot>=protocol::slots||publisher(now,count)!=slot||members==0||members>=64||
        (members&~((1u<<count)-1u))||!(members&(1u<<slot))||phase>=64||
        (protected_lease(word,now,count)&&lease.leader!=slot))return word;
    constexpr auto claims=(std::uint64_t{1}<<42)-1;
    const auto low=word&claims;
    if(!protocol::is_group_code(protocol::compact::slot(word,slot).objective))return word;
    if(scheduled(now)==Kind::Project)return low|(std::uint64_t{2}<<62)|(std::uint64_t{now/6}<<53)|
        (std::uint64_t{phase}<<47)|(std::uint64_t{protocol::compact::pack_members(members,slot)}<<42);
    if(scheduled(now)==Kind::Lease&&!ready)return word;
    if(scheduled(now)==Kind::Cash&&(dx< -3||dx>3||dy< -3||dy>3||(!dx&&!dy)))return word;
    const unsigned code=scheduled(now)==Kind::Lease?50u:1u+7u*(dx+3)+(dy+3);
    return low|(std::uint64_t{now/6}<<54)|(std::uint64_t{phase}<<48)|(std::uint64_t{code}<<42);
}
constexpr std::uint64_t focus(std::uint64_t word,unsigned now,unsigned count,unsigned slot,unsigned target) {
    if(slot>=count||slot>=protocol::slots||target>=64||publisher(now,count)!=slot||
        protocol::compact::slot(word,slot).objective!=protocol::fight||scheduled(now)==Kind::Project||
        protected_lease(word,now,count))return word;
    const unsigned code=scheduled(now)==Kind::Lease?52u:51u;
    constexpr auto claims=(std::uint64_t{1}<<42)-1;
    return (word&claims)|(std::uint64_t{now/6}<<54)|(std::uint64_t{target}<<48)|(std::uint64_t{code}<<42);
}
struct Cash {
    unsigned round=0,low=0,high=0;bool valid=false;
};
struct Project {
    unsigned round=0,task=protocol::idle;Intent intent=Intent::Released;bool valid=false;
};
struct Focus {int round=-1;unsigned target=0;bool valid=false;};
struct Role {
    int dx=0,dy=0;
    bool operator==(const Role&) const=default;
};
struct Certificate {
    int round=-1,changed=-1;
    unsigned task=protocol::idle,phase=0,members=0;Role role;
    bool valid=false;
};
struct AgreementStatus {
    unsigned declared=0,ready=0;int barrier=-1;
    bool committed(unsigned members) const {return members&&declared==members&&ready==members;}
};
struct WorkRecord {
    unsigned task=protocol::idle,generation=0;
    int distance=65535,progress=-10000,capture=65535;
    float hp=0;
    // Recreating the same Contract is not work. Keep the actual best approach,
    // damage and capture evidence across local release/reselection cycles.
    bool update(unsigned job,unsigned cycle,int now,int dist,float health,int timer,bool worked,int window) {
        if(!protocol::is_group_code(job)||dist<0||!std::isfinite(health)||health<0||window<0)return false;
        if(task!=job||generation!=cycle){task=job;generation=cycle;distance=dist;hp=health;capture=timer;progress=now;}
        else if(worked||dist<distance||health+.01f<hp||timer<capture) {
            distance=std::min(distance,dist);hp=std::min(hp,health);capture=std::min(capture,timer);progress=now;
        }
        return now>=progress&&now-progress<window;
    }
};
// An allocator may OFFER an extension while the retained owner still names the
// old crew. It must preserve every incumbent and name itself as coordinator;
// this is not permission to take an unrelated camp or its completed payout.
constexpr bool extends(const protocol::compact::Lease& owner,unsigned self,unsigned crew,unsigned capturer) {
    return owner.valid&&self<protocol::slots&&crew<64&&capturer==self&&
        !(owner.members&(1u<<self))&&(crew&(1u<<self))&&!(owner.members&~crew);
}
struct Ledger {
    std::array<Cash,protocol::slots> cash{};
    std::array<Project,protocol::slots> projects{};
    std::array<Focus,protocol::slots> focuses{};
    std::array<protocol::compact::Lease,protocol::slots> cohorts{};
    std::array<bool,protocol::slots> accepted{},revoked{};
    std::array<Certificate,protocol::slots> roles{},rosters{},readies{};
    static bool current(const Certificate& c,unsigned now,unsigned count) {
        return c.valid&&c.round>=0&&static_cast<unsigned>(c.round)<=now&&now-c.round<=lifetime(count);
    }
    static void record(Certificate& c,const Frame& f,unsigned members,unsigned count) {
        if(static_cast<int>(f.round)<=c.round)return; // Changed claims cannot rename the same dated packet.
        const bool changed=!c.valid||f.round-c.round>lifetime(count)||c.task!=f.task||c.phase!=f.phase||
            c.members!=members||c.role!=Role{f.dx,f.dy};
        const int birth=changed?static_cast<int>(f.round):c.changed;
        c={static_cast<int>(f.round),birth,f.task,f.phase,members,{f.dx,f.dy},true};
    }
    void observe(std::uint64_t word,unsigned now,unsigned count) {
        const auto offer=protocol::compact::lease(word,now,lifetime(count));
        if(count&&count<=protocol::slots&&offer.valid&&offer.leader<count&&offer.capturer<count&&!(offer.members&~((1u<<count)-1))) {
            auto& c=cohorts[offer.leader];
            // Same dated packet with subsequently changed claims cannot create
            // a new objective identity. The immediate claims revoke it below.
            if(!c.valid||offer.round>c.round){c=offer;accepted[offer.leader]=revoked[offer.leader]=false;}
        }
        for(unsigned leader=0;leader<protocol::slots;++leader)if(cohorts[leader].valid) {
            const auto& c=cohorts[leader];bool consent=true;
            for(unsigned s=0;s<count&&s<protocol::slots;++s)if(c.members&(1u<<s))
                consent&=protocol::compact::slot(word,s).objective==c.objective;
            if(accepted[leader]&&!consent)revoked[leader]=true;
            if(consent&&!revoked[leader])accepted[leader]=true;
        }
        for(unsigned s=0;s<protocol::slots;++s)for(auto* c:{&roles[s],&rosters[s],&readies[s]})
            if(c->valid&&protocol::compact::slot(word,s).objective!=c->task)c->valid=false;
        for(unsigned s=0;s<protocol::slots;++s)if(protocol::compact::slot(word,s).objective!=protocol::fight)focuses[s].valid=false;
        const auto f=decode(word,now,count);if(!f.valid)return;
        if(f.kind==Kind::Cash) {
            auto& c=cash[f.slot];if(c.valid&&c.round>f.round)return;
            c={f.round,f.gold,f.gold==511*gold_quantum?std::numeric_limits<unsigned>::max():f.gold+gold_quantum-1,true};
        } else if(f.kind==Kind::Project) {
            auto& p=projects[f.slot];if(p.valid&&p.round>f.round)return;
            p={f.round,f.task,f.intent,true};
        } else if(f.kind==Kind::Focus) {
            auto& p=focuses[f.slot];if(static_cast<int>(f.round)>p.round)p={static_cast<int>(f.round),f.phase,true};
        } else if(f.kind==Kind::Role)record(roles[f.slot],f,0,count);
        else if(f.kind==Kind::Roster)record(rosters[f.slot],f,f.members,count);
        else if(f.kind==Kind::Ready) {
            const auto& roster=rosters[f.slot];
            if(current(roster,f.round,count)&&roster.task==f.task&&roster.phase==f.phase) {
                record(readies[f.slot],f,roster.members,count);
                auto& owner=cohorts[f.slot];
                bool newest=true;
                for(unsigned s=0;s<count;++s)if(s!=f.slot&&cohorts[s].valid&&cohorts[s].objective==static_cast<int>(f.task)&&
                    cohorts[s].round>owner.round)newest=false;
                if(owner.valid&&!revoked[f.slot]&&owner.objective==static_cast<int>(f.task)&&owner.members==roster.members&&
                    newest&&owner.round<f.round&&f.round-owner.round<=lifetime(count))owner.round=f.round;
            }
        }
    }
    AgreementStatus agreement(unsigned task,unsigned members,unsigned phase,const std::array<Role,protocol::slots>& expected,
                              int since,std::uint64_t word,unsigned now,unsigned count) const {
        AgreementStatus status;status.barrier=since;
        if(!count||count>protocol::slots||!members||(members&~((1u<<count)-1u))||phase>=64||since<0)return status;
        for(unsigned s=0;s<count;++s)if(members&(1u<<s)) {
            const auto& r=roles[s];const auto& c=rosters[s];
            if(protocol::compact::slot(word,s).objective==task&&current(r,now,count)&&current(c,now,count)&&
                r.round>=since&&c.round>=since&&r.task==task&&c.task==task&&r.phase==phase&&c.phase==phase&&
                r.role==expected[s]&&c.members==members) {
                status.declared|=1u<<s;status.barrier=std::max({status.barrier,r.changed,c.changed});
            }
        }
        if(status.declared!=members)return status;
        for(unsigned s=0;s<count;++s)if(members&(1u<<s)) {
            const auto& c=readies[s];
            if(current(c,now,count)&&c.round>=status.barrier&&c.task==task&&c.phase==phase&&c.members==members)status.ready|=1u<<s;
        }
        return status;
    }
    bool contradiction(unsigned task,unsigned members,unsigned phase,const std::array<Role,protocol::slots>& expected,
                       int since,unsigned now,unsigned count) const {
        for(unsigned s=0;s<count&&s<protocol::slots;++s)if(members&(1u<<s)) {
            const auto& r=roles[s];const auto& c=rosters[s];
            if(current(r,now,count)&&r.round>=since&&(r.task!=task||r.phase!=phase||r.role!=expected[s]))return true;
            if(current(c,now,count)&&c.round>=since&&(c.task!=task||c.phase!=phase||c.members!=members))return true;
        }
        return false;
    }
    Cash budget(unsigned slot,unsigned now,unsigned count) const {
        if(slot>=count||slot>=protocol::slots||!count||count>protocol::slots||now>2047)return {};
        const auto c=cash[slot];return c.valid&&c.round<=now&&now-c.round<=lifetime(count)?c:Cash{};
    }
    Project project(unsigned slot,unsigned now,unsigned count) const {
        if(slot>=count||slot>=protocol::slots||!count||count>protocol::slots||now>2047)return {};
        const auto p=projects[slot];return p.valid&&p.round<=now&&now-p.round<=lifetime(count)?p:Project{};
    }
    Focus focus(unsigned slot,std::uint64_t word,unsigned now,unsigned count) const {
        if(slot>=count||slot>=protocol::slots||!count||count>protocol::slots||now>2047)return {};
        const auto p=focuses[slot];return p.valid&&p.round>=0&&static_cast<unsigned>(p.round)<=now&&
            now-static_cast<unsigned>(p.round)<=std::min(4u,lifetime(count))&&protocol::compact::slot(word,slot).objective==protocol::fight?p:Focus{};
    }
    int reservation(unsigned slot,unsigned current_claim,unsigned now,unsigned count) const {
        const auto p=project(slot,now,count);
        return p.valid&&p.task==current_claim&&protocol::is_group_code(p.task)&&
            (p.intent==Intent::Active||p.intent==Intent::Recover)?static_cast<int>(p.task):-1;
    }
    protocol::compact::Lease cohort(unsigned task,std::uint64_t word,unsigned now,unsigned count) const {
        protocol::compact::Lease result;
        if(!protocol::is_group_code(task)||!count||count>protocol::slots||now>2047)return result;
        for(unsigned leader=0;leader<protocol::slots;++leader) {
            const auto& c=cohorts[leader];
            if(!c.valid||revoked[leader]||c.leader>=count||c.capturer>=count||(c.members&~((1u<<count)-1))||
                c.objective!=static_cast<int>(task)||c.round>now||now-c.round>lifetime(count))continue;
            bool consent=true;
            for(unsigned s=0;s<count;++s)if(c.members&(1u<<s))consent&=protocol::compact::slot(word,s).objective==task;
            if(consent&&(!result.valid||c.round>result.round||(c.round==result.round&&c.leader<result.leader)))result=c;
        }
        return result;
    }
};
}
