#pragma once
#include <cambc.h>
#include <array>
#include <bit>
#include <cstdint>
#include <vector>

namespace dz {
// Set once at boot after LocalMask::agrees_with confirms the linear layout.
inline bool local_masks_valid = false;
// In-Wasm copy of a map bitboard. Every cambc::bitboard test/set is an SDK
// host call (bc_Bitboard_Test / bc_Bitboard_Set); tile loops built on them
// cost tens of thousands of fuel per turn. A whole mask crosses the boundary
// in one call through the packed row-major linear buffer (LSB first).
class LocalMask {
    std::vector<std::uint8_t> bits_;
    int width_ = 0, height_ = 0;
public:
    void resize() {
        width_ = cambc::map::width(); height_ = cambc::map::height();
        bits_.assign(cambc::bitboard::linear_buffer_size(), 0);
    }
    void load(const cambc::bitboard& board) {
        if (bits_.size() != cambc::bitboard::linear_buffer_size()) resize();
        board.export_linear_buffer(bits_);
    }
    void store(cambc::bitboard& board) const { board.import_linear_buffer(bits_); }
    void clear() { std::fill(bits_.begin(), bits_.end(), 0); }
    bool in_bounds(cambc::vec2 p) const { return p.x >= 0 && p.y >= 0 && p.x < width_ && p.y < height_; }
    bool test(cambc::vec2 p) const {
        if (!in_bounds(p)) return false;
        const auto i = static_cast<std::size_t>(p.y) * width_ + p.x;
        return (bits_[i >> 3] >> (i & 7)) & 1;
    }
    void set(cambc::vec2 p, bool value = true) {
        if (!in_bounds(p)) return;
        const auto i = static_cast<std::size_t>(p.y) * width_ + p.x;
        if (value) bits_[i >> 3] |= static_cast<std::uint8_t>(1u << (i & 7));
        else bits_[i >> 3] &= static_cast<std::uint8_t>(~(1u << (i & 7)));
    }
    bool empty() const { for (auto b : bits_) if (b) return false; return true; }
    unsigned count() const { unsigned c = 0; for (auto b : bits_) c += std::popcount(b); return c; }
    // Verify the assumed linear layout against the SDK once: same population
    // and every sampled SDK position set locally. Callers fall back if false.
    bool agrees_with(const cambc::bitboard& board) const {
        if (count() != board.count()) return false;
        // Bounded sample: a full positions() list of every wall exhausted the
        // boot turn on 00vault.
        std::array<cambc::vec2,16> sample{};
        const auto n = board.positions_into(sample);
        for (std::uint32_t i = 0; i < n && i < sample.size(); ++i) if (!test(sample[i])) return false;
        return true;
    }
};
// Distance-field roots built locally and handed to the SDK in one import.
// Falls back to per-tile bitboard calls if the layout check failed.
class RootSet {
    LocalMask mask_; cambc::bitboard board_; bool board_mode_ = false, any_ = false;
public:
    RootSet() { if (local_masks_valid) mask_.resize(); }
    void set(cambc::vec2 p) {
        any_ = true;
        if (local_masks_valid && !board_mode_) mask_.set(p); else board_.set(p);
    }
    RootSet& operator=(const cambc::bitboard& b) { board_ = b; board_mode_ = true; any_ = !b.is_empty(); return *this; }
    bool is_empty() const { return !any_; }
    unsigned count() const { return local_masks_valid && !board_mode_ ? mask_.count() : board_.count(); }
    const cambc::bitboard& board() { if (local_masks_valid && !board_mode_) mask_.store(board_); return board_; }
};
}
