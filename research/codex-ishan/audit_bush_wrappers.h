// Diagnostic draft fixture. Exercise each snapshot's production World::bush_cluster.
#include <cstdio>
#include <memory>
#include "world.h"

static void audit_bush_wrappers() {
    auto world = std::make_unique<World>();
    world->width = bc::map::width();
    world->height = bc::map::height();
    world->bushes = bc::map::bushes();
    world->bush_labeled.clear();
    const int tiles = world->width * world->height;
    world->bush_label = std::make_unique<std::uint16_t[]>(tiles);
    std::uint64_t digest = 14695981039346656037ULL;
    const auto start = bc::fuel_remaining();
    for (int y = 0; y < world->height; ++y) {
        for (int x = 0; x < world->width; ++x) {
            digest ^= static_cast<std::uint64_t>(world->bush_cluster({x, y}) + 1);
            digest *= 1099511628211ULL;
        }
    }
    const auto cost = start - bc::fuel_remaining();
    std::printf("CODEX_BUSH_WRAPPER tiles=%d components=%d mask_equal=%d labels=%llu fuel=%llu\n",
                tiles, world->bush_clusters, (world->bushes ^ world->bush_labeled).is_empty() ? 1 : 0,
                static_cast<unsigned long long>(digest), static_cast<unsigned long long>(cost));
}
