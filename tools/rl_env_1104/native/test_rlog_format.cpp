// Host check that the fuel-optimised CNR1 writers (bots/claude-native-1104/src/nnrec.cpp, CLNA_RLOG) emit exactly the
// bytes of the first writer (c3ceaa4b), on edge and random integers and doubles.
// build + run (repo root): g++ -std=c++20 -O1 tools/rl_env_1104/native/test_rlog_format.cpp -o rlog_fmt && ./rlog_fmt
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <random>
#include <string>

namespace ref {  // the c3ceaa4b writer, verbatim apart from the namespace
static char clna_rbuf[1024];
static int clna_rpos = 0;
static void clna_rhex(std::uint64_t v, int digits) {
    static const char H[] = "0123456789abcdef";
    for (int i = digits - 1; i >= 0; --i) clna_rbuf[clna_rpos + i] = H[v & 15], v >>= 4;
    clna_rpos += digits;
}
static void clna_rch(char c) { clna_rbuf[clna_rpos++] = c; }
static void clna_rint(long v) {
    char t[24];
    int n = 0;
    const bool neg = v < 0;
    unsigned long u = neg ? static_cast<unsigned long>(-v) : static_cast<unsigned long>(v);
    do t[n++] = static_cast<char>('0' + u % 10), u /= 10; while (u);
    if (neg) clna_rch('-');
    while (n) clna_rch(t[--n]);
}
static void clna_rdbl(double d) {
    std::uint64_t u;
    __builtin_memcpy(&u, &d, sizeof u);
    clna_rhex(u, 16);
}
}  // namespace ref

namespace cur {  // the current writer, as in nnrec.cpp
static char clna_rbuf[1024];
struct ClnaHex2 {
    std::uint16_t t[256];
    constexpr ClnaHex2() : t{} {
        for (int i = 0; i < 256; ++i)
            t[i] = static_cast<std::uint16_t>("0123456789abcdef"[i >> 4] | ("0123456789abcdef"[i & 15] << 8));
    }
};
static constexpr ClnaHex2 clna_hex2{};
static char* clna_rint(char* o, long v) {
    char t[24];
    int n = 0;
    unsigned long u = v < 0 ? 0ul - static_cast<unsigned long>(v) : static_cast<unsigned long>(v);
    if (v < 0) *o++ = '-';
    do t[n++] = static_cast<char>('0' + u % 10), u /= 10; while (u);
    while (n) *o++ = t[--n];
    return o;
}
static char* clna_rdbl(char* o, double d) {
    std::uint64_t u;
    __builtin_memcpy(&u, &d, sizeof u);
    for (int i = 7; i >= 0; --i) __builtin_memcpy(o + 2 * i, &clna_hex2.t[u & 255u], 2), u >>= 8;
    return o + 16;
}
}  // namespace cur

int main() {
    std::mt19937_64 rng(1104);
    long ints[] = {0, 1, -1, 9, 10, -10, 1999, 2000, 123456789, -987654321, 2147483647L, -2147483647L};
    double dbls[] = {0.0, -0.0, 1.0, 0.02, 1e-300, -3.8918202981106265, std::numeric_limits<double>::infinity(),
                     std::numeric_limits<double>::denorm_min(), std::numeric_limits<double>::max()};
    int n = 0;
    auto check = [&](bool isint, long iv, double dv) {
        ref::clna_rpos = 0;
        char* o = cur::clna_rbuf;
        if (isint) ref::clna_rint(iv), o = cur::clna_rint(o, iv);
        else ref::clna_rdbl(dv), o = cur::clna_rdbl(o, dv);
        const std::string a(ref::clna_rbuf, ref::clna_rpos), b(cur::clna_rbuf, o - cur::clna_rbuf);
        if (a != b) {
            std::printf("MISMATCH %s vs %s\n", a.c_str(), b.c_str());
            std::exit(1);
        }
        ++n;
    };
    for (long v : ints) check(true, v, 0);
    for (double d : dbls) check(false, 0, d);
    for (int i = 0; i < 200000; ++i) {
        check(true, static_cast<long>(static_cast<std::int32_t>(rng())), 0);
        std::uint64_t bits = rng();
        double d;
        std::memcpy(&d, &bits, sizeof d);
        check(false, 0, d);
    }
    std::printf("OK: %d values byte-identical\n", n);
}
