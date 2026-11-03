#pragma once

#if GX_TRIPRATE > 0
namespace gx {
inline float bank_tail(const World& w, const GroupRec& g, bool has_gems) {
    // The ordinary altar field is already built for banking. Do not start a field search here.
    if (!w.altar_ready || w.no_bank || !has_gems || g.camps.empty()) return 0.0f;
    const int d = fdist(w.altar_field, w.camps[g.camps.front()].pos);
    if (d == kUnreach) return 0.0f;
    // A single return serves several captures. Cap the estimate so it cannot make distant
    // camps permanently uncompetitive on a large or gated map.
    return (GX_TRIPRATE * 0.01f) * static_cast<float>(std::min(d, 32));
}
} // namespace gx
#endif
