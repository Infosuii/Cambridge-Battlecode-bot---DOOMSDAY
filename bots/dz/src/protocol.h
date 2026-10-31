#pragma once
#include <cstdint>
#include "config.h"

namespace dz::protocol {
inline constexpr unsigned slots = 6;
inline constexpr std::uint8_t shop = 120, retreat = 121, dead = 126, idle = 127;
struct Slot { std::uint8_t objective; bool onsite; };
constexpr bool is_group_code(unsigned code) { return code<112; }
constexpr std::uint8_t group_code(unsigned index) { return index < 112 ? static_cast<std::uint8_t>(index) : idle; }
namespace compact {
// Six 7-bit objectives leave 22 bits. A crew lease uses an EXACT 11-bit game
// round (not parity/TTL modulo), six members, three capturer bits and validity.
// On-site is established from legal visible positions instead of a stale bit.
constexpr Slot slot(std::uint64_t word,unsigned index) {
    return index<slots ? Slot{static_cast<std::uint8_t>((word>>(index*7))&127),false} : Slot{idle,false};
}
constexpr std::uint64_t with_slot(std::uint64_t word,unsigned index,Slot value) {
    if(index>=slots)return word;
    return (word&~(std::uint64_t{127}<<(index*7)))|(std::uint64_t{value.objective&127u}<<(index*7));
}
struct Lease { unsigned members=0,capturer=0,round=0,leader=slots;int objective=-1;bool valid=false; };
constexpr Lease lease(std::uint64_t word,unsigned now,unsigned maximum_age=3) {
    Lease result;
    if((word&(std::uint64_t{1}<<63))||!(word&(std::uint64_t{1}<<62)))return result;
    result.members=(word>>42)&63;result.capturer=(word>>48)&7;result.round=(word>>51)&2047;
    // The recipient coordinates this offer. Its own task claim names the job,
    // so any member can initiate a crew without waiting for a lower slot to
    // publish an objective it has not yet accepted. Joined crews can hand off.
    result.leader=result.capturer;
    result.objective=result.leader<slots?slot(word,result.leader).objective:idle;
    result.valid=(word&(std::uint64_t{1}<<62))&&now<=2047&&result.round<=now&&now-result.round<=maximum_age&&
        result.leader<slots&&result.capturer<slots&&(result.members&(1u<<result.capturer))&&is_group_code(result.objective);
    return result;
}
constexpr std::uint64_t with_lease(std::uint64_t word,unsigned members,unsigned capturer,unsigned round,bool valid=true) {
    constexpr auto mask=~((std::uint64_t{1}<<42)-1);
    word&=~mask;
    if(!valid||round>2047||members==0||members>63||capturer>=slots||!(members&(1u<<capturer)))return word;
    return word|(std::uint64_t{members}<<42)|(std::uint64_t{capturer}<<48)|(std::uint64_t{round}<<51)|(std::uint64_t{1}<<62);
}
}
constexpr Slot slot(std::uint64_t word, unsigned index) {
#if DZ_ECONOMY_V2
    return compact::slot(word,index);
#else
    if (index >= slots) return {idle, false};
    auto value = static_cast<std::uint8_t>(word >> (index * 8));
    return {static_cast<std::uint8_t>(value & 127), (value & 128) != 0};
#endif
}
constexpr std::uint64_t with_slot(std::uint64_t word, unsigned index, Slot value) {
#if DZ_ECONOMY_V2
    return compact::with_slot(word,index,value);
#else
    if (index >= slots) return word;
    const auto shift = index * 8;
    const auto byte = static_cast<std::uint64_t>((value.objective & 127) | (value.onsite ? 128 : 0));
    return (word & ~(std::uint64_t{255} << shift)) | (byte << shift);
#endif
}
constexpr std::uint64_t empty_word() {
    std::uint64_t word = 0;
    for (unsigned i = 0; i < slots; ++i) word = with_slot(word, i, {idle, false});
    return word;
}
// Team messages are preserved but not interpreted in v0: the sketch's parity/TTL
// cannot independently establish age. Do not infer freshness from unchanged bits.
}
