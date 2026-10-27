// Six tagged bytes alternate intentions and positions; a timed focus uses the remaining 16 bits.
#pragma once
#include <cstdint>
namespace team67 {
constexpr int kSlots=6, kFocusShift=48, kPayloadShift=51, kTimeShift=61;
constexpr std::uint64_t kSlotsMask=(std::uint64_t{1}<<48)-1;
inline unsigned byte(std::uint64_t m,int s) { return s>=0&&s<6 ? unsigned((m>>(8*s))&255) : 0; }
inline std::uint64_t put_byte(std::uint64_t m,int s,unsigned v) {
    if(s<0||s>=6) return m;
    return (m&~(std::uint64_t{255}<<(8*s)))|(std::uint64_t(v&255)<<(8*s));
}
inline bool position(std::uint64_t m,int s,int& x,int& y) {
    const unsigned v=byte(m,s);
    if(!(v&128)||(v&127)<1||(v&127)>100) return false;
    x=int(((v&127)-1)%10)*10+5; y=int(((v&127)-1)/10)*10+5;
    return true;
}
inline std::uint64_t put_position(std::uint64_t m,int s,int x,int y,bool alive) {
    unsigned v=0;
    if(alive&&x>=0&&y>=0&&x<100&&y<100) v=128+1+x/10+10*(y/10);
    return put_byte(m,s,v);
}
inline bool job_message(std::uint64_t m,int s) { return !(byte(m,s)&128); }
inline int job(std::uint64_t m,int s) { return job_message(m,s) ? int(byte(m,s))-1 : -1; }
inline std::uint64_t put_job(std::uint64_t m,int s,int g) { return put_byte(m,s,g>=0&&g<126 ? unsigned(g+1) : 0); }
inline int focus(std::uint64_t m) { return int((m>>48)&7)-1; }
inline int age(std::uint64_t m,int round) { return (round-int(m>>61))&7; }
inline int rally(std::uint64_t m) { return focus(m)<0 ? int((m>>51)&1023)-1 : -1; }
inline std::uint64_t put_plan(std::uint64_t m,int target,int group,int round=0) {
    const unsigned f=target>=0&&target<6 ? unsigned(target+1) : 0;
    const unsigned payload=group>=0&&group<1023 ? unsigned(group+1) : 0;
    return (m&kSlotsMask)|(std::uint64_t(f)<<48)|(std::uint64_t(payload)<<51)|(std::uint64_t(round&7)<<61);
}
inline std::uint64_t put_battle(std::uint64_t m,int target,int x,int y,int round) {
    if(target<0||target>=6||x<0||y<0||x>=100||y>=100) return m;
    return put_plan(m,target,x/4+25*(y/4),round);
}
inline bool battle(std::uint64_t m,int round,int& target,int& x,int& y) {
    target=focus(m); const int payload=int((m>>51)&1023)-1;
    if(target<0||age(m,round)>3||payload<0||payload>=625) return false;
    x=(payload%25)*4+2; y=(payload/25)*4+2; return true;
}
}
