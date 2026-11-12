#pragma once
#include <cambc.h>
#include <cstdarg>
#include <cstddef>
#include <cstdint>
#include <unistd.h>
#include "config.h"
#include "trace_meter.h"

namespace dz {
// Trace output for diagnostic builds only (release builds print nothing).
// libc printf cost 10k-60k fuel per call in this runtime and distorted every
// fuel measurement taken from a trace build. dz::trace formats a small printf
// subset with integer arithmetic into a static buffer; trace_flush writes it
// with one raw write() just before end_turn, and only from fuel that would be
// discarded anyway, so the measured part of a turn pays only the cheap append.
// Supported: %d %i %u %ld %lu %lld %llu %zu %x %c %s %% and %f / %.Nf (N<=3,
// rounded toward zero). Width/flags are ignored.
struct TraceBuffer {
    static constexpr std::size_t capacity = 32768;
    char data[capacity];
    std::size_t size = 0;
    unsigned dropped = 0; // Lines discarded because the buffer was full.
};
inline TraceBuffer trace_buffer;
// Trace work is metered once for profiling, including nested trace() calls.
// The governor still uses physical fuel. Instrumented and release behavior can
// differ, so strength decisions always require an uninstrumented release pool.
inline TraceMeter trace_meter;
inline auto& trace_overhead = trace_meter.credited;
inline std::uint64_t trace_cap = 3000;
inline std::uint64_t trace_line_cost_max = 0, trace_line_cost_sum = 0, trace_lines = 0;
#if DZ_TRACE
struct TraceScope {
    TraceScope() { trace_meter.begin(cambc::fuel_remaining(),cambc::round_number()); }
    ~TraceScope() {
        trace_meter.finish(cambc::fuel_remaining(),cambc::round_number());
    }
};
// Scheduling and action gates must use physical fuel. Adding diagnostic costs
// back here can authorize work that exhausts the real budget. Compensation is
// for offline profiling only, never for spending decisions.
inline std::uint64_t fuel_left() { return cambc::fuel_remaining(); }
#else
inline std::uint64_t fuel_left() { return cambc::fuel_remaining(); }
#endif
struct FlushCost { std::size_t bytes = 0; std::uint64_t fuel = 0; };
inline FlushCost trace_flush_cost; // Last flush, reported by the next line.

namespace trace_detail {
inline void put(char c) {
    auto& b = trace_buffer;
    if (b.size < TraceBuffer::capacity) b.data[b.size++] = c;
}
inline void put_unsigned(unsigned long long v, unsigned base = 10) {
    char tmp[24]; int n = 0;
    do { const unsigned d = static_cast<unsigned>(v % base); tmp[n++] = static_cast<char>(d < 10 ? '0' + d : 'a' + d - 10); v /= base; } while (v && n < 24);
    while (n) put(tmp[--n]);
}
inline void put_signed(long long v) {
    if (v < 0) { put('-'); put_unsigned(static_cast<unsigned long long>(-(v + 1)) + 1); }
    else put_unsigned(static_cast<unsigned long long>(v));
}
inline void put_fixed(double v, int decimals) {
    if (!(v == v)) { put('n'); put('a'); put('n'); return; }
    if (v < 0) { put('-'); v = -v; }
    if (v > 1e18) v = 1e18;
    long long scale = 1; for (int i = 0; i < decimals; ++i) scale *= 10;
    const auto scaled = static_cast<unsigned long long>(v * scale);
    put_unsigned(scaled / scale);
    if (decimals) {
        put('.');
        auto frac = scaled % scale; char digits[3];
        for (int i = decimals - 1; i >= 0; --i) { digits[i] = static_cast<char>('0' + frac % 10); frac /= 10; }
        for (int i = 0; i < decimals; ++i) put(digits[i]);
    }
}
}

inline bool trace(const char* format, ...) {
    using namespace trace_detail;
#if DZ_TRACE
    TraceScope scope;
#endif
    auto& b = trace_buffer;
    // Keep whole lines: refuse a line that may not fit (lines are < 512 bytes).
    if (b.size + 512 > TraceBuffer::capacity) { ++b.dropped; return false; }
#if DZ_TRACE
    // Bound formatting work and leave physical fuel for production logic.
    // Drop lines instead; the count is reported.
    const bool line_open = b.size && b.data[b.size-1] != '\n';
    const auto real=cambc::fuel_remaining();
    const std::uint64_t minimum_real=
#if DZ_ECONOMY_V2
        std::max<std::uint64_t>(trace_cap>3000?5000:25000,config::reserve+12000);
#else
        trace_cap > 3000 ? 5000u : 25000u;
#endif
    if (!line_open && (trace_overhead+trace_meter.pending(real,cambc::round_number()) > trace_cap || real < minimum_real)) { ++b.dropped; return false; }
#endif
    const auto line_start_fuel = cambc::fuel_remaining();
    const auto line_round = cambc::round_number();
    va_list args; va_start(args, format);
    for (const char* p = format; *p; ++p) {
        if (*p != '%') { put(*p); continue; }
        ++p;
        int decimals = 6, longs = 0; bool size_t_arg = false;
        while (*p == '-' || *p == '+' || *p == ' ' || *p == '0' || (*p >= '1' && *p <= '9')) ++p;
        if (*p == '.') { ++p; decimals = 0; while (*p >= '0' && *p <= '9') { decimals = decimals * 10 + (*p - '0'); ++p; } }
        while (*p == 'l') { ++longs; ++p; }
        if (*p == 'z') { size_t_arg = true; ++p; }
        switch (*p) {
        case 'd': case 'i':
            if (longs >= 2) put_signed(va_arg(args, long long));
            else if (longs == 1) put_signed(va_arg(args, long));
            else put_signed(va_arg(args, int));
            break;
        case 'u': case 'x': {
            const unsigned base = *p == 'x' ? 16 : 10;
            if (size_t_arg) put_unsigned(va_arg(args, std::size_t), base);
            else if (longs >= 2) put_unsigned(va_arg(args, unsigned long long), base);
            else if (longs == 1) put_unsigned(va_arg(args, unsigned long), base);
            else put_unsigned(va_arg(args, unsigned), base);
            break;
        }
        case 'f': put_fixed(va_arg(args, double), decimals > 3 ? 3 : decimals); break;
        case 'c': put(static_cast<char>(va_arg(args, int))); break;
        case 's': { const char* s = va_arg(args, const char*); for (; s && *s; ++s) put(*s); break; }
        case '%': put('%'); break;
        default: put('%'); if (*p) put(*p); else --p; break;
        }
    }
    va_end(args);
    const auto remaining = cambc::fuel_remaining();
    if (cambc::round_number()!=line_round||remaining>line_start_fuel) return false;
    const auto spent = line_start_fuel - remaining;
    if (spent > trace_line_cost_max) trace_line_cost_max = spent;
    trace_line_cost_sum += spent; ++trace_lines;
    return true;
}

// Write buffered lines only from otherwise-discarded fuel: call immediately
// before end_turn. `force` empties a nearly full buffer regardless.
inline void trace_flush(std::uint64_t spare = 30000) {
    auto& b = trace_buffer;
    if (!b.size && !b.dropped) return;
    const bool force = b.size > TraceBuffer::capacity * 3 / 4;
    if (!force && cambc::fuel_remaining() < spare + b.size * 4) return;
    if (b.dropped) { const auto n = b.dropped; b.dropped = 0; trace("DZ_TRACE_DROPPED lines=%u\n", n); }
    const auto before = cambc::fuel_remaining();
    const auto bytes = b.size;
    std::size_t done = 0;
    while (done < b.size) {
        const auto written = ::write(1, b.data + done, b.size - done);
        if (written <= 0) break;
        done += static_cast<std::size_t>(written);
    }
    b.size = 0;
    trace_flush_cost = {bytes, before - cambc::fuel_remaining()};
}
}
namespace dz {
// A metered fuel reading for trace-only bookkeeping that spans blocks.
inline std::uint64_t trace_fuel_mark() {
#if DZ_TRACE
    TraceScope scope;
#endif
    return trace_meter.available(cambc::fuel_remaining(),cambc::round_number());
}
}
