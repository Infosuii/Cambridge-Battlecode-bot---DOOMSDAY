// NFS2 direct-policy records. Pure bounded writer; no SDK, runtime, NFS1 or model dependency.
// Queuing happens in the turn. Root runtime must fuel-gate flush_one() from leftover fuel AFTER play_turn.
// Full little-endian wire specification: agents/v2_records/WIRE.md.
#pragma once
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cmath>
#include <bit>

namespace nnp_log {
inline constexpr std::uint32_t kMagic=0x3253464eu, kNoAction=0xffffffffu;
inline constexpr std::uint16_t kVersion=2;
inline constexpr int kMaxK=16,kF=12,kMaxPayload=8192,kQueueBytes=32768;
inline constexpr int kMaxText=5+4*((kMaxPayload+2)/3)+1;
enum Kind : std::uint16_t { kContext=0,kDecision=1,kExecution=2 };
enum Source : std::uint8_t { kDirectPolicy=0,kContinuedOption=1,kTeacherFallback=2,kSafetyOverride=3 };
enum Flags : std::uint8_t { kOptionStart=1,kOptionEnd=2,kDefinedOption=4 };
enum Outcome : std::uint8_t { kPending=0,kExecuted=1,kOptionExecuted=2,kGuardRefused=3,kOverridden=4,kFailed=5 };
struct Header {
    std::uint32_t obs_hash=0,action_hash=0;
    std::int32_t round=0;
    std::uint32_t champion=0,snapshot=0;
    std::uint64_t decision_id=0; // nonzero for decisions/acks; episode identity is provided by collection metadata
};
struct Fuel { std::uint32_t candidate=0,observation=0,inference=0,log=0; };
struct ContextRec { Header h; const void* raw=nullptr; std::uint32_t bytes=0; };
struct DecisionRec {
    Header h;
    std::uint16_t head=0,K=0,F=kF;
    std::int16_t chosen=-1,teacher=-1;
    std::uint8_t context=0,sampled=0,source=kDirectPolicy,flags=0;
    std::uint16_t reason=0;
    std::uint64_t option_id=0;
    std::uint32_t selected_id=kNoAction;
    std::uint32_t teacher_id=kNoAction; // absent; or explicit computed ID outside candidates when teacher==-1
    float logp=0;
    Fuel fuel;
    const std::uint32_t* id=nullptr; // K, strictly ascending stable action IDs; teacher never affects ordering
    const std::uint8_t* legal=nullptr; // K, exactly0/1
    const float* feat=nullptr; // K*12, finite
    const float* logits=nullptr; // K, finite if legal; illegal may be finite or -inf (never +inf/NaN)
};
struct ExecutionRec {
    Header h; std::uint32_t executed_id=kNoAction;
    std::uint8_t outcome=kPending,source=kDirectPolicy;
    std::uint16_t reason=0;
    std::uint64_t option_id=0;
    std::uint32_t action_fuel=0,log_fuel=0;
};

inline unsigned char g_payload[kMaxPayload]{},g_queue[kQueueBytes]{};
inline char g_text[kMaxText]{};
inline std::uint32_t g_head=0,g_tail=0,g_bytes=0,g_queued=0,g_written=0,g_dropped=0,g_invalid=0,g_write_failed=0;
inline std::uint32_t g_text_written=0;
inline std::uint32_t checksum(const unsigned char* p,int n) {
    std::uint32_t h=2166136261u; for(int i=0;i<n;++i) h=(h^p[i])*16777619u; return h;
}
struct Writer {
    int n=0; bool bad=false;
    void bytes(const void* p,int len) {
        if (len<0 || n+len>kMaxPayload || (len && !p)) { bad=true; return; }
        if(len) std::memcpy(g_payload+n,p,static_cast<unsigned>(len)); n+=len;
    }
    void u8(std::uint8_t x) { bytes(&x,1); }
    void u16(std::uint16_t x) { u8(x&255);u8(x>>8); }
    void i16(std::int16_t x) { u16(static_cast<std::uint16_t>(x)); }
    void u32(std::uint32_t x) { u16(x&65535);u16(x>>16); }
    void i32(std::int32_t x) { u32(static_cast<std::uint32_t>(x)); }
    void u64(std::uint64_t x) { u32(static_cast<std::uint32_t>(x));u32(static_cast<std::uint32_t>(x>>32)); }
    void f32(float x) { std::uint32_t bits;std::memcpy(&bits,&x,4);u32(bits); }
    void header(Kind kind,const Header& h) {
        u32(kMagic);u16(kVersion);u16(kind);u32(0); // final total bytes patched at finish
        u32(h.obs_hash);u32(h.action_hash);i32(h.round);u32(h.champion);u32(h.snapshot);u64(h.decision_id);
    }
};
inline bool valid_header(const Header& h) { return h.obs_hash && h.action_hash && h.round>=0; }
inline bool valid_decision(const DecisionRec& r) {
    if(!valid_header(r.h)||!r.h.decision_id||r.head<1||r.head>8||r.K>kMaxK||r.F!=kF||r.context>3||r.sampled>1||r.source>3||r.flags>7||
       r.chosen<-1||r.chosen>=static_cast<int>(r.K)||r.teacher<-1||r.teacher>=static_cast<int>(r.K)||!std::isfinite(r.logp)||r.logp>0.00001f) return false;
    if(r.K && (!r.id||!r.legal||!r.feat||!r.logits)) return false;
    if(r.source==kDirectPolicy && r.chosen<0) return false;
    if(r.sampled && (r.chosen<0||r.source!=kDirectPolicy)) return false;
    if(r.chosen>=0 && (!r.legal[r.chosen]||r.selected_id!=r.id[r.chosen])) return false;
    if(r.teacher>=0 && !r.legal[r.teacher]) return false;
    if(r.teacher>=0 && r.teacher_id!=r.id[r.teacher]) return false;
    if(r.teacher<0 && r.teacher_id!=kNoAction)
        for(int i=0;i<r.K;++i)if(r.teacher_id==r.id[i])return false;
    if((r.flags&7) && !r.option_id) return false;
    for(int i=0;i<r.K;++i) {
        if(r.legal[i]>1||(i && r.id[i-1]>=r.id[i])||r.id[i]==kNoAction) return false;
        if(std::isnan(r.logits[i])||r.logits[i]==INFINITY||(r.legal[i]&&!std::isfinite(r.logits[i]))) return false;
    }
    for(int i=0;i<r.K*kF;++i) if(!std::isfinite(r.feat[i])) return false;
    return true;
}
inline void ring_write(const unsigned char* p,std::uint32_t n) {
    const std::uint32_t first=n<kQueueBytes-g_tail ? n : kQueueBytes-g_tail;
    std::memcpy(g_queue+g_tail,p,first); if(n>first) std::memcpy(g_queue,p+first,n-first);
    g_tail=(g_tail+n)%kQueueBytes;g_bytes+=n;
}
inline void ring_read(std::uint32_t offset,unsigned char* p,std::uint32_t n) {
    const auto at=(g_head+offset)%kQueueBytes;
    const auto first=n<kQueueBytes-at ? n : kQueueBytes-at;
    std::memcpy(p,g_queue+at,first);if(n>first)std::memcpy(p+first,g_queue,n-first);
}
inline bool enqueue(Writer& w) {
    if(w.bad||w.n+4>kMaxPayload) {++g_dropped;return false;}
    const auto total=static_cast<std::uint32_t>(w.n+4);
    for(int i=0;i<4;++i)g_payload[8+i]=static_cast<unsigned char>(total>>(8*i));
    // Internal queue owns a copy of the immutable payload. Finalize its wire checksum only
    // during post-turn flushing; hashing every candidate byte must not delay gameplay.
    w.u32(0);
    if(g_bytes+4+total>kQueueBytes) {++g_dropped;return false;}
    unsigned char len[4];for(int i=0;i<4;++i)len[i]=static_cast<unsigned char>(total>>(8*i));
    ring_write(len,4);ring_write(g_payload,total);++g_queued;return true;
}
inline bool enqueue_context(const ContextRec& r) {
    if(!valid_header(r.h)||r.h.decision_id||!r.raw||!r.bytes||r.bytes>kMaxPayload-48) {++g_invalid;return false;}
    Writer w;w.header(kContext,r.h);w.u32(r.bytes);w.bytes(r.raw,static_cast<int>(r.bytes));return enqueue(w);
}
inline bool enqueue_decision(const DecisionRec& r) {
    if(!valid_decision(r)) {++g_invalid;return false;}
    Writer w;w.header(kDecision,r.h);
    w.u16(r.head);w.u16(r.K);w.u16(r.F);w.i16(r.chosen);w.i16(r.teacher);
    w.u8(r.context);w.u8(r.sampled);w.u8(r.source);w.u8(r.flags);w.u16(r.reason);
    w.u64(r.option_id);w.u32(r.selected_id);w.u32(r.teacher_id);w.f32(r.logp);
    w.u32(r.fuel.candidate);w.u32(r.fuel.observation);w.u32(r.fuel.inference);w.u32(r.fuel.log);
    if constexpr(std::endian::native==std::endian::little) {
        // Arrays already have the wire's exact scalar representation. Four bounded copies avoid
        // serializing every float through four single-byte Writer calls on the competition path.
        w.bytes(r.id,r.K*4);w.bytes(r.legal,r.K);w.bytes(r.logits,r.K*4);w.bytes(r.feat,r.K*kF*4);
    } else {
        for(int i=0;i<r.K;++i)w.u32(r.id[i]);
        for(int i=0;i<r.K;++i)w.u8(r.legal[i]);
        for(int i=0;i<r.K;++i)w.f32(r.logits[i]);
        for(int i=0;i<r.K*kF;++i)w.f32(r.feat[i]);
    }
    return enqueue(w);
}
inline bool enqueue_execution(const ExecutionRec& r) {
    if(!valid_header(r.h)||!r.h.decision_id||r.outcome>kFailed||r.source>3) {++g_invalid;return false;}
    Writer w;w.header(kExecution,r.h);w.u32(r.executed_id);w.u8(r.outcome);w.u8(r.source);w.u16(r.reason);
    w.u64(r.option_id);w.u32(r.action_fuel);w.u32(r.log_fuel);return enqueue(w);
}
inline bool queue_empty() { return g_bytes==0; }
inline int next_bytes() {
    if(queue_empty())return 0;
    unsigned char p[4];ring_read(0,p,4);
    return int(std::uint32_t(p[0])|(std::uint32_t(p[1])<<8)|(std::uint32_t(p[2])<<16)|(std::uint32_t(p[3])<<24));
}
inline int next_line_bytes() { const auto n=next_bytes();return n ? 6+4*((n+2)/3) : 0; }
inline int encode_line(const unsigned char* p,int n) {
    constexpr char abc[]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    std::memcpy(g_text,"NFS2 ",5);int o=5;
    for(int i=0;i<n;i+=3) {
        const int remain=n-i;const std::uint32_t v=(std::uint32_t(p[i])<<16)|(remain>1?std::uint32_t(p[i+1])<<8:0)|(remain>2?p[i+2]:0);
        g_text[o++]=abc[v>>18];g_text[o++]=abc[(v>>12)&63];g_text[o++]=remain>1?abc[(v>>6)&63]:'=';g_text[o++]=remain>2?abc[v&63]:'=';
    }
    g_text[o++]='\n';return o;
}
inline bool flush_one(std::FILE* out=stdout) {
    if(queue_empty())return false;
    const auto n=next_bytes();ring_read(4,g_payload,n);
    const auto hash=checksum(g_payload,n-4);
    for(int i=0;i<4;++i)g_payload[n-4+i]=static_cast<unsigned char>(hash>>(8*i));
    const auto text=encode_line(g_payload,n);const auto written=std::fwrite(g_text,1,text,out);
    g_text_written+=static_cast<std::uint32_t>(written);
    g_head=(g_head+4+n)%kQueueBytes;g_bytes-=4+n;
    if(written!=static_cast<unsigned>(text)){++g_write_failed;return false;}
    ++g_written;return true;
}
inline void reset() {g_head=g_tail=g_bytes=g_queued=g_written=g_dropped=g_invalid=g_write_failed=g_text_written=0;}
} // namespace nnp_log
