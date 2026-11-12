#pragma once
#include <cstdint>
#include <span>

namespace dz {
// The official export is one uint16 per tile, in row-major order. This is an
// owning-field snapshot, never a route estimate or a dynamic occupancy cache.
inline int linear_distance(std::span<const std::uint16_t> values,int width,int height,int x,int y) {
    if(width<=0||height<=0||x<0||y<0||x>=width||y>=height||
        values.size()!=static_cast<unsigned>(width)*static_cast<unsigned>(height))return 65535;
    return values[static_cast<unsigned>(y)*width+x];
}
}
