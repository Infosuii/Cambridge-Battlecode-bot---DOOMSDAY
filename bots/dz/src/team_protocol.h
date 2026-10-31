#pragma once
#include "protocol.h"
#include <algorithm>
#include <array>
#include <limits>

namespace dz::team {
// Six immediate 7-bit claims retain the low 42 bits. The high 22 bits hold
// either the existing crew lease, or one explicitly dated self report.
enum class Kind : unsigned { None=0, Lease=1, Cash=2, Project=3 };
enum class Intent : unsigned { Active=0, Recover=1, Released=2, Dead=3 };
inline constexpr unsigned gold_quantum=8;
constexpr unsigned lifetime(unsigned count) {return 4*count+2;}
constexpr unsigned publisher(unsigned round,unsigned count) {
    return count&&count<=protocol::slots&&round<=2047&&!(round&1)?(round/4)%count:protocol::slots;
}
constexpr Kind scheduled(unsigned round) {return (round/2)&1?Kind::Project:Kind::Cash;}
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
    if(slot>=count||slot>=protocol::slots||task>127||static_cast<unsigned>(intent)>3||publisher(now,count)!=slot||protocol::compact::lease(word,now).valid)return word;
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
struct Ledger {
    std::array<Cash,protocol::slots> cash{};
    std::array<Project,protocol::slots> projects{};
    void observe(std::uint64_t word,unsigned now,unsigned count) {
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
};
}
