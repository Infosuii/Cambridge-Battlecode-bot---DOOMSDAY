#pragma once

#if GX_TRIPRATE > 0
namespace gx {
struct ReturnLeg {
    const World& world;
    int current = kUnreach;

    ReturnLeg(const World& w, vec2 here, int gems) : world(w) {
        if (gems >= 24 && w.altar_ready && !w.no_bank)
            current = fdist(w.altar_field, here);
    }

    float extra(const GroupRec& g) const {
        if (current == kUnreach || g.camps.empty()) return 0.0f;
        const int d = fdist(world.altar_field, world.camps[g.camps.front()].pos);
        if (d == kUnreach || d <= current) return 0.0f;
        return (GX_TRIPRATE * 0.01f) * static_cast<float>(std::min(d - current, 24));
    }
};
} // namespace gx
#endif
