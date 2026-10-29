#pragma once
#include <array>
#include <cstdint>
#include <cstdio>
#include <cambc.h>
#include "config.h"
#include "trace.h"

namespace dz {
// Trace-only fuel profile of one turn. Marks are stored during the turn and
// printed at the start of the next one, so a profile never spends the budget
// it measures. Samples that crossed a fuel suspension are discarded.
#if DZ_TRACE && DZ_TRACE_PROFILE
struct TurnProfile {
    unsigned round=0; std::uint64_t start=0; unsigned n=0;
    std::array<std::uint64_t,16> at{}; std::array<char,16> tag{};
    bool crossed=false; unsigned cross_index=0;
    std::array<std::uint64_t,4> acc{};
    void begin(unsigned r) { round=r; start=trace_fuel_mark(); n=0; crossed=false; acc={}; }
    void mark(char t) {
        TraceScope scope;
        if (n>=at.size()) return;
        const auto f=trace_fuel_mark(); // Excludes metered trace work, for reports only.
        if (!crossed && (f>(n?at[n-1]:start)+5000 || cambc::round_number()!=round)) { crossed=true; cross_index=n; }
        at[n]=f; tag[n++]=t;
    }
    // Printing costs tens of thousands of fuel, so keep only the worst sample
    // and print it once every 250 rounds.
    struct Worst { unsigned round=0; std::uint64_t start=0; unsigned n=0; std::array<std::uint64_t,16> at{}; std::array<char,16> tag{}; std::array<std::uint64_t,4> acc{}; };
    Worst worst;
    void flush(unsigned slot) {
        TraceScope scope;
        if (n && !crossed && start-at[n-1] > (worst.n ? worst.start-worst.at[worst.n-1] : 0))
            worst={round,start,n,at,tag,acc};
        if (n && crossed) {
            // The turn ran out of fuel: report the steps before the suspension
            // and the step that crossed it, immediately.
            const auto keep=worst; worst={round,start,cross_index,at,tag,acc};
            trace("DZ_PROFILE_CROSSED during=%c ", cross_index<n ? tag[cross_index] : '?');
            if (worst.n) print(slot); else trace("round=%u before-first-mark\n",round);
            worst=keep;
        }
        n=0;
        if (cambc::round_number()%250!=0 || !worst.n) return;
        print(slot); worst=Worst{};
    }
    void print(unsigned slot) {
        const auto& w=worst;
        ::dz::trace("DZ_PROFILE round=%u slot=%u total=%llu",w.round,slot,static_cast<unsigned long long>(w.start-w.at[w.n-1]));
        ::dz::trace(" acc=%llu/%llu/%llu/%llu",static_cast<unsigned long long>(w.acc[0]),static_cast<unsigned long long>(w.acc[1]),static_cast<unsigned long long>(w.acc[2]),static_cast<unsigned long long>(w.acc[3]));
        std::uint64_t prev=w.start;
        for (unsigned i=0;i<w.n;++i) { ::dz::trace(" %c=%llu",w.tag[i],static_cast<unsigned long long>(prev-w.at[i])); prev=w.at[i]; }
        ::dz::trace("\n");
    }
};
inline TurnProfile turn_profile;
#define DZ_PROF(t) ::dz::turn_profile.mark(t)
#define DZ_ACC_BEGIN(v) const auto v=::dz::trace_fuel_mark()
#define DZ_ACC_END(i,v) (::dz::turn_profile.acc[i]+=v-::dz::trace_fuel_mark())
#else
#define DZ_PROF(t) (void)0
#define DZ_ACC_BEGIN(v) (void)0
#define DZ_ACC_END(i,v) (void)0
#endif
}
