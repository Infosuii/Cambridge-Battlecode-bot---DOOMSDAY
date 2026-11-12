#pragma once
#include <cstdint>

namespace dz {
// Trace scopes may nest (a diagnostic block calls trace()). Only the outer
// interval is credited. Inside it, compensated fuel stays at the outer entry:
// diagnostic work must not appear as bot work or create fuel by double credit.
struct TraceMeter {
    std::uint64_t credited=0,anchor=0;
    std::uint32_t round=0;
    unsigned depth=0;
    void reset() { credited=0; anchor=0; round=0; depth=0; }
    void begin(std::uint64_t fuel,std::uint32_t current_round) {
        if (depth++==0) { anchor=fuel; round=current_round; }
    }
    std::uint64_t pending(std::uint64_t fuel,std::uint32_t current_round) const {
        return depth&&current_round==round&&anchor>=fuel?anchor-fuel:0;
    }
    std::uint64_t available(std::uint64_t fuel,std::uint32_t current_round,std::uint64_t limit=~std::uint64_t{0}) const {
        const auto overhead=credited+pending(fuel,current_round);
        return fuel+(overhead<limit?overhead:limit);
    }
    void finish(std::uint64_t fuel,std::uint32_t current_round) {
        if (!depth) return;
        const auto spent=pending(fuel,current_round);
        if (--depth==0) credited+=spent;
    }
};
}
