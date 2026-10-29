#pragma once
#include <array>
#include <algorithm>

namespace dz {
// A failed engine move reveals an obstruction without revealing its identity.
// Remember only the tile, briefly. Never infer enemy/ally identity or keep a
// permanent wall after a body has moved away. Constant storage and scan cost.
struct FailedMoves {
    struct Entry { int tile=-1,until=0; };
    std::array<Entry,8> entries{};
    int pending_tile=-1,pending_round=-2,pending_count=0;
    bool persistent_failure(int tile,int round) {
        pending_count=tile==pending_tile&&round==pending_round+1?pending_count+1:1;
        pending_tile=tile;pending_round=round;
        return pending_count>=3;
    }
    bool blocks(int tile,int round) const {
        return std::any_of(entries.begin(),entries.end(),[&](auto e){return e.tile==tile&&e.until>round;});
    }
    void clear(int tile) { for (auto& e:entries) if(e.tile==tile) e={}; }
    void remember(int tile,int round,int ttl=6) {
        auto* selected=&entries.front();
        for (auto& e:entries) {
            if (e.tile==tile||e.until<=round) { selected=&e;break; }
            if (e.until<selected->until) selected=&e;
        }
        *selected={tile,round+ttl};
    }
};
}
