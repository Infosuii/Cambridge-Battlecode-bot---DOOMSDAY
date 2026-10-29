#pragma once
#include <cambc.h>
#include <cstdarg>
#include <cstddef>
#include <cstdint>
#include <unistd.h>
#include "config.h"

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
// Fuel-neutral tracing: trace-only work is metered and added back, so bot
// logic reading fuel_left() makes the same budget decisions as a release
// build. Reset at every turn start (TurnContext::begin).
inline std::uint64_t trace_overhead = 0;
inline std::uint64_t trace_cap = 3000;
inline std::uint64_t trace_line_cost_max = 0, trace_line_cost_sum = 0, trace_lines = 0; // Measured formatting cost. // Per-turn credited trace budget; raised in the trace window.
#if DZ_TRACE
inline std::uint64_t fuel_query_cost() {
    static std::uint64_t cost = [] {
        const auto a = cambc::fuel_remaining(); const auto b = cambc::fuel_remaining();
        return a > b ? a - b : 0;
    }();
    return cost;
}
struct TraceScope {
    std::uint64_t start;
    TraceScope() : start(cambc::fuel_remaining()) {}
    ~TraceScope() {
        const auto end = cambc::fuel_remaining();
        // Credit only the measured span: over-crediting let trace builds
        // spend fuel they did not have (30 fuel-outs, dz-parity-trace-v65-03).
        if (start > end) trace_overhead += start - end;
    }
};
// Bot logic reads real fuel plus this turn's metered trace work, so its budget
// decisions match a release build. A trace build still fuel-outs where release
// had less spare than the (capped, <=3k) trace overhead: treat those as
// warnings that the release turn ran close to the limit.
inline std::uint64_t fuel_left() { return cambc::fuel_remaining() + trace_overhead; }
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

inline void trace(const char* format, ...) {
    using namespace trace_detail;
#if DZ_TRACE
    TraceScope scope;
#endif
    auto& b = trace_buffer;
    // Keep whole lines: refuse a line that may not fit (lines are < 512 bytes).
    if (b.size + 512 > TraceBuffer::capacity) { ++b.dropped; return; }
#if DZ_TRACE
    // Overhead is credited back to bot logic, so it must stay well inside the
    // 12k reserve or trace builds exhaust real fuel (110 fuel-outs in
    // dz-parity-trace-v65-01). Drop lines instead; the count is reported.
    const bool line_open = b.size && b.data[b.size-1] != '\n';
    if (!line_open && (trace_overhead > trace_cap || cambc::fuel_remaining() < (trace_cap > 3000 ? 5000u : 25000u))) { ++b.dropped; return; }
#endif
    const auto line_start_fuel = cambc::fuel_remaining();
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
    const auto spent = line_start_fuel - cambc::fuel_remaining();
    if (spent > trace_line_cost_max) trace_line_cost_max = spent;
    trace_line_cost_sum += spent; ++trace_lines;
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
    return fuel_left(); // Compensated: trace work never shows up in fuel deltas.
}
}
