#pragma once
#include "protocol.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <limits>

namespace dz::team {
// Six immediate 7-bit claims retain the low 42 bits. The high 22 bits hold
// either the existing crew lease, or one explicitly dated self report.
enum class Kind : unsigned { None=0, Lease=1, Cash=2, Project=3 };
enum class Intent : unsigned { Active=0, Recover=1, Released=2, Dead=3 };
inline constexpr unsigned gold_quantum=8;
constexpr unsigned lifetime(unsigned count) {return 6*count+2;}
constexpr unsigned publisher(unsigned round,unsigned count) {
    return count&&count<=protocol::slots&&round<=2047&&!(round&1)?(round/6)%count:protocol::slots;
}
constexpr Kind scheduled(unsigned round) {return (round/2)%3==0?Kind::Cash:(round/2)%3==1?Kind::Project:Kind::Lease;}
constexpr bool protected_lease(std::uint64_t word,unsigned now,unsigned count) {
    const auto lease=protocol::compact::lease(word,now);
    if(!lease.valid)return false;
    // Scheduled cohort advertisements, like reports, are held over the odd
    // round. They do not monopolise subsequent publishers' message slots.
    const bool scheduled_cohort=scheduled(lease.round)==Kind::Lease&&publisher(lease.round,count)==lease.leader;
    return !scheduled_cohort||now-lease.round<2;
}
struct Frame {
    Kind kind=Kind::None;unsigned slot=protocol::slots,round=0;
    unsigned gold=0,task=protocol::idle;Intent intent=Intent::Released;
    bool valid=false;
};
constexpr Frame decode(std::uint64_t word,unsigned now,unsigned count) {
    Frame f;f.kind=static_cast<Kind>(word>>62);f.round=(word>>51)&2047;
    if((f.kind!=Kind::Cash&&f.kind!=Kind::Project)||!count||count>protocol::slots||now>2047||
        f.round>now||now-f.round>lifetime(count)||publisher(f.round,count)==protocol::slots||scheduled(f.round)!=f.kind)return f;
    f.slot=publisher(f.round,count);
    const unsigned data=(word>>42)&511;
    if(f.kind==Kind::Cash)f.gold=data*gold_quantum;
    else {f.task=data&127;f.intent=static_cast<Intent>(data>>7);}
    f.valid=true;return f;
}
constexpr std::uint64_t publish(std::uint64_t word,unsigned now,unsigned count,unsigned slot,
                                unsigned gold,unsigned task,Intent intent) {
    // Hold each report across the intervening odd round. All turn orders can
    // observe it; a new urgent crew offer may preempt it, never the reverse.
    if(slot>=count||slot>=protocol::slots||task>127||static_cast<unsigned>(intent)>3||publisher(now,count)!=slot||
        protected_lease(word,now,count)||scheduled(now)==Kind::Lease)return word;
    const auto kind=scheduled(now);
    const unsigned data=kind==Kind::Cash?std::min(511u,gold/gold_quantum):(task&127)|(static_cast<unsigned>(intent)<<7);
    constexpr auto claims=(std::uint64_t{1}<<42)-1;
    return (word&claims)|(std::uint64_t{data}<<42)|(std::uint64_t{now}<<51)|(static_cast<std::uint64_t>(kind)<<62);
}
struct Cash {
    unsigned round=0,low=0,high=0;bool valid=false;
};
struct Project {
    unsigned round=0,task=protocol::idle;Intent intent=Intent::Released;bool valid=false;
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
struct Ledger {
    std::array<Cash,protocol::slots> cash{};
    std::array<Project,protocol::slots> projects{};
    std::array<protocol::compact::Lease,protocol::slots> cohorts{};
    std::array<bool,protocol::slots> accepted{},revoked{};
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
        const auto f=decode(word,now,count);if(!f.valid)return;
        if(f.kind==Kind::Cash) {
            auto& c=cash[f.slot];if(c.valid&&c.round>f.round)return;
            c={f.round,f.gold,f.gold==511*gold_quantum?std::numeric_limits<unsigned>::max():f.gold+gold_quantum-1,true};
        } else {
            auto& p=projects[f.slot];if(p.valid&&p.round>f.round)return;
            p={f.round,f.task,f.intent,true};
        }
    }
    Cash budget(unsigned slot,unsigned now,unsigned count) const {
        if(slot>=count||slot>=protocol::slots||!count||count>protocol::slots||now>2047)return {};
        const auto c=cash[slot];return c.valid&&c.round<=now&&now-c.round<=lifetime(count)?c:Cash{};
    }
    Project project(unsigned slot,unsigned now,unsigned count) const {
        if(slot>=count||slot>=protocol::slots||!count||count>protocol::slots||now>2047)return {};
        const auto p=projects[slot];return p.valid&&p.round<=now&&now-p.round<=lifetime(count)?p:Project{};
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
