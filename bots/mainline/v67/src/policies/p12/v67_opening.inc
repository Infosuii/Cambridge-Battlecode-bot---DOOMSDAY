// A winning team's opening is adapted geometrically to our spawn. Decisions
// advance on observed captures, rather than replaying timed game inputs.
#include "bot.h"
#include "v67_meta.h"

int Bot::v67_opening_job() {
    const auto* plan = v67meta::opening();
    if (!plan || round > 150) return -1;
    const plan67::Route* route = nullptr;
    for (unsigned i = 0; i < plan->nr; ++i) if (plan->routes[i].hero == type) route = &plan->routes[i];
    if (!route || !route->n) return -1;
    if (opening_map67_.empty()) {
        auto transform = [&](vec2 p, int tr) {
            if (tr & 4) std::swap(p.x, p.y);
            if (tr & 1) p.x = w.width - 1 - p.x;
            if (tr & 2) p.y = w.height - 1 - p.y;
            return p;
        };
        int tr = 0, best = 1000000;
        for (int i = 0; i < (w.width == w.height ? 8 : 4); ++i) {
            const vec2 p = transform({plan->sx, plan->sy}, i);
            const int distance = fdist(w.spawn_field, p);
            if (distance < best) { best = distance; tr = i; }
        }
        opening_map67_.assign(w.groups.size(), -1);
        for (unsigned gi = 0; gi < w.groups.size(); ++gi) {
            const auto& g = w.groups[gi];
            if (g.camps.empty()) continue;
            const vec2 at = transform(w.camps[g.camps[0]].pos, tr);
            for (unsigned gj = 0; gj < w.groups.size(); ++gj) {
                const auto& other = w.groups[gj];
                if (g.gems != other.gems || g.gold != other.gold || g.camps.size() != other.camps.size()) continue;
                for (int ci : other.camps) if (w.camps[ci].pos == at) opening_map67_[gi] = static_cast<int>(gj);
            }
        }
    }
    while (opening_step67_ < static_cast<int>(route->n)) {
        const int raw = route->groups[opening_step67_];
        const int gi = raw >= 0 && raw < static_cast<int>(opening_map67_.size()) ? opening_map67_[raw] : -1;
        if (gi < 0) { ++opening_step67_; continue; }
        auto& g = w.groups[gi];
        if (g.state == GroupState::respawning || (g.state == GroupState::reward && group_capture_covered(g) && !bit(g.tiles,pos))) {
            ++opening_step67_;
            continue;
        }
        // A failed or interrupted opening never traps a champion indefinitely.
        if (opening_started67_ < 0) opening_started67_ = round;
        if (round - opening_started67_ > 45 || (gi < static_cast<int>(avoid_until.size()) && avoid_until[gi] > round)) {
            ++opening_step67_; opening_started67_ = -1; continue;
        }
        return gi;
    }
    return -1;
}
