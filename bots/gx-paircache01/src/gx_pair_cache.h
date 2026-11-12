#pragma once

#if GX_PAIR_CACHE > 0
namespace gx_pair {
namespace d = cambc::detail;
inline constexpr unsigned kBegin = 32, kBody = 42, kEnd = 992;
inline constexpr unsigned kMax = 43;
inline constexpr std::uint16_t kMissing = 65535;

inline unsigned offset(unsigned i, unsigned j) {
    if (i > j) std::swap(i,j);
    return j * (j - 1) / 2 + i;
}
inline std::uint32_t checksum(const std::uint8_t* begin, unsigned length) {
    std::uint32_t h = 2166136261u;
    for (unsigned i = 0; i < length; ++i) h = (h ^ begin[i]) * 16777619u;
    return h;
}
inline void publish() {
    static bool done = false;
    if (done || cambc::constants::draft_memory_bytes < kEnd) return;
    done = true;
    const int width = cambc::map::width(), height = cambc::map::height();
    std::uint32_t n = 0;
    if (width < 1 || height < 1 || width > 100 || height > 100 ||
        d::sdk_map_num_camp_groups(&n) != 0 || n < 2 || n > kMax) return;
    std::vector<std::uint32_t> groups(n);
    if (d::sdk_map_camp_groups(groups.data(),n,&n) != 0 || n < 2 || n > kMax) return;
    struct Group {
        cambc::bitboard tiles;
        std::vector<vec2> points;
    };
    std::vector<Group> records(n);
    const auto terrain = cambc::map::walls() | cambc::map::holes() | cambc::map::altars() |
                         cambc::map::spawn_region(team::enemy);
    for (unsigned i = 0; i < n; ++i) {
        unsigned members = 0, handles[64];
        if (d::sdk_map_camp_group_num_camps(groups[i],&members) != 0 || members == 0 || members > 64 ||
            d::sdk_map_camp_group_camps(groups[i],handles,members,&members) != 0) return;
        records[i].tiles.clear();
        for (unsigned j = 0; j < members; ++j) {
            d::camp_info spec{};
            if (d::sdk_map_camp_info(handles[j],&spec) != 0) return;
            const vec2 p{spec.x,spec.y};
            if (p.x < 0 || p.y < 0 || p.x >= width || p.y >= height || bit(terrain,p)) return;
            records[i].points.push_back(p);
            set_bit(records[i].tiles,p);
        }
    }

    std::array<std::uint8_t,kEnd> bytes;
    if (d::sdk_read_draft_memory(0,bytes.data(),bytes.size()) != 0) return;
    cambc::distance_field field;
    cambc::bitboard reached;
    const std::uint64_t reserve = 1800000;
    for (unsigned j = 1; j < n; ++j) {
        if (cambc::fuel_remaining() < reserve) return;
        field.compute(terrain,records[j].tiles,reached);
        for (unsigned i = 0; i < j; ++i) {
            auto distance = kMissing;
            for (const vec2 p : records[i].points) distance = std::min(distance,fdist(field,p));
            // 254 represents long rows that should use the local 16-bit field.
            bytes[kBody + offset(i,j)] = distance == kMissing ? 255 : std::min<std::uint16_t>(distance,254);
        }
    }
    const unsigned length = n * (n-1) / 2;
    const auto check = checksum(bytes.data()+kBody,length);
    bytes[kBegin] = 'G';
    bytes[kBegin+1] = 'P';
    bytes[kBegin+2] = 1;
    bytes[kBegin+3] = width;
    bytes[kBegin+4] = height;
    bytes[kBegin+5] = n;
    for (unsigned i = 0; i < 4; ++i) bytes[kBegin+6+i] = check >> (i*8);
    d::sdk_bc_submit_draft_memory(bytes.data(),kBody+length);
}

inline const std::uint8_t* open(unsigned width, unsigned height, unsigned n) {
    const auto& bytes = cambc::draft_memory;
    if (n < 2 || n > kMax) return nullptr;
    const unsigned length = n * (n-1) / 2;
    if (bytes.size() < kBody+length) return nullptr;
    const auto* p = reinterpret_cast<const std::uint8_t*>(bytes.data()) + kBegin;
    if (p[0] != 'G' || p[1] != 'P' || p[2] != 1 || p[3] != width || p[4] != height || p[5] != n) return nullptr;
    std::uint32_t expect = 0;
    for (unsigned i = 0; i < 4; ++i) expect |= std::uint32_t(p[6+i]) << (8*i);
    const auto* payload = p + (kBody-kBegin);
    return expect == checksum(payload,length) ? payload : nullptr;
}
} // namespace gx_pair
#endif
