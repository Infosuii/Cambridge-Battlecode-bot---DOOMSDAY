#pragma once

#if GX_MAP_CACHE > 0
namespace gx_cache {
namespace d = cambc::detail;
inline constexpr std::size_t kBegin = 32, kPayload = 44, kEnd = 992;

inline std::uint32_t checksum(const std::uint8_t* first, const std::uint8_t* last) {
    std::uint32_t hash = 2166136261u;
    while (first != last) hash = (hash ^ *first++) * 16777619u;
    return hash;
}

inline void publish() {
    static bool done = false;
    if (done || cambc::constants::draft_memory_bytes < kEnd) return;
    done = true;
    std::array<std::uint8_t, kEnd> bytes;
    if (d::sdk_read_draft_memory(0, bytes.data(), bytes.size()) != 0) return;
    const int width = cambc::map::width(), height = cambc::map::height();
    if (width <= 0 || height <= 0 || width > 255 || height > 255 || width * height > 16384) return;
    std::uint32_t n = 0;
    if (d::sdk_map_num_camp_groups(&n) != 0 || n == 0 || n > 253) return;
    std::vector<std::uint32_t> handles(n);
    if (d::sdk_map_camp_groups(handles.data(), n, &n) != 0) return;
    std::size_t cursor = kPayload;
    auto emit = [&](std::uint32_t value, unsigned count) {
        if (cursor + count > bytes.size()) return false;
        for (unsigned i = 0; i < count; ++i)
            bytes[cursor++] = static_cast<std::uint8_t>(value >> (8 * i));
        return true;
    };
    for (const std::uint32_t h : handles) {
        d::camp_group_info g{};
        std::uint32_t members = 0, camps[64];
        if (h > 65535 || d::sdk_map_camp_group(h, &g) != 0 ||
            d::sdk_map_camp_group_num_camps(h, &members) != 0 || members > 64 ||
            g.gems > 65535 || g.gold > 65535) return;
        if (members && d::sdk_map_camp_group_camps(h, camps, members, &members) != 0) return;
        if (!emit(h, 2) || !emit(g.gems, 2) || !emit(g.gold, 2) || !emit(members, 1)) return;
        for (std::uint32_t i = 0; i < members; ++i) {
            const auto id = camps[i];
            d::camp_info info{};
            if (id >= 32768 || d::sdk_map_camp_info(id, &info) != 0 || info.type < 0 || info.type >= 16 ||
                info.x < 0 || info.y < 0 || info.x >= width || info.y >= height) return;
            const std::uint32_t encoded = id < 128 ? id : (id & 127u) | 128u | ((id >> 7) << 8);
            const std::uint32_t position = static_cast<std::uint32_t>(info.y * width + info.x);
            if (!emit(encoded, id < 128 ? 1 : 2) || !emit(position | (static_cast<std::uint32_t>(info.type) << 14), 3)) return;
        }
    }
    const auto length = cursor - kPayload;
    const auto hash = checksum(bytes.data() + kPayload, bytes.data() + cursor);
    bytes[kBegin] = 'G';
    bytes[kBegin + 1] = 'C';
    bytes[kBegin + 2] = 1;
    bytes[kBegin + 3] = static_cast<std::uint8_t>(width);
    bytes[kBegin + 4] = static_cast<std::uint8_t>(height);
    bytes[kBegin + 5] = static_cast<std::uint8_t>(n);
    bytes[kBegin + 6] = static_cast<std::uint8_t>(length);
    bytes[kBegin + 7] = static_cast<std::uint8_t>(length >> 8);
    for (unsigned i = 0; i < 4; ++i) bytes[kBegin + 8 + i] = static_cast<std::uint8_t>(hash >> (8*i));
    d::sdk_bc_submit_draft_memory(bytes.data(), cursor);
}

struct Reader {
    const std::uint8_t* p = nullptr;
    const std::uint8_t* end = nullptr;

    std::uint32_t read(unsigned n) {
        if (end - p < n) throw std::runtime_error("Camp catalog ended before its last record");
        std::uint32_t v = 0;
        for (unsigned i = 0; i < n; ++i) v |= std::uint32_t(*p++) << (8*i);
        return v;
    }

    std::uint32_t camp_id() {
        const auto low = read(1);
        return (low & 128u) ? (low & 127u) | (read(1) << 7) : low;
    }
};

inline Reader open(int width, int height, std::uint32_t n) {
    const auto& memory = cambc::draft_memory;
    if (memory.size() < kPayload) return {};
    const auto* bytes = reinterpret_cast<const std::uint8_t*>(memory.data());
    const auto* h = bytes + kBegin;
    if (h[0] != 'G' || h[1] != 'C' || h[2] != 1 || h[3] != width || h[4] != height || h[5] != n) return {};
    const std::uint32_t length = h[6] | (std::uint32_t(h[7]) << 8);
    if (length == 0 || kPayload + length > std::min(memory.size(), kEnd)) return {};
    Reader hash_reader{h + 8, h + 12};
    const auto* begin = bytes + kPayload;
    const auto* end = begin + length;
    if (hash_reader.read(4) != checksum(begin, end)) return {};
    return {begin, end};
}
} // namespace gx_cache
#endif
