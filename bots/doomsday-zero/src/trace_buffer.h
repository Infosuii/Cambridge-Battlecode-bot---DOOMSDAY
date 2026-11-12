#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <span>

namespace dz {
// Retain unwritten bytes without copying a large suffix on a busy turn.
struct TraceBuffer {
    static constexpr std::size_t capacity=32768;
    std::array<char,capacity> data{};
    std::size_t head=0,size=0;
    unsigned dropped=0;
    bool put(char c) {
        if(size==capacity)return false;
        data[(head+size)&(capacity-1)]=c;++size;return true;
    }
    char last() const {return size?data[(head+size-1)&(capacity-1)]:0;}
    std::span<const char> contiguous() const {return {data.data()+head,std::min(size,capacity-head)};}
    bool consume(std::size_t count) {
        if(count>size)return false;
        head=(head+count)&(capacity-1);size-=count;return true;
    }
};
// Include import/formatting slack and keep every write small even when the
// buffer is nearly full. A full buffer never overrides the physical budget.
inline std::size_t trace_chunk(std::size_t contiguous,std::uint64_t fuel,std::uint64_t spare) {
    if(fuel<=spare||fuel-spare<=4096)return 0;
    const auto limit=std::min<std::uint64_t>(4096,(fuel-spare-4096)/8);
    return std::min(contiguous,static_cast<std::size_t>(limit));
}
}
