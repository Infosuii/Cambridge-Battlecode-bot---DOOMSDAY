#pragma once
#include "camp_threat.h"
#include <optional>

namespace dz::crew {
inline int clearance(Tile p,std::span<const Tile> workspace) {
    int result=65535;for(auto tile:workspace)result=std::min(result,cheb(p,tile));return result;
}
// A parking outsider yields out of the advertised workspace. Every accepted
// step strictly increases clearance or, at equal clearance, decreases actual
// home distance. No occupied/spawn tile or increase in observed damage is used.
template<class Open,class Home,class Danger>
std::optional<Tile> yield_step(Tile here,std::span<const Tile> workspace,int radius,Open open,Home home,Danger danger) {
    if(workspace.empty()||workspace.size()>64||radius<0)return std::nullopt;
    const int before=clearance(here,workspace),home_before=home(here);
    if(before>radius)return std::nullopt;
    const auto threat=danger(here);if(!std::isfinite(threat)||threat<0)return std::nullopt;
    std::optional<Tile> best;int gap=before,home_best=home_before;
    for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy) {
        if(!dx&&!dy)continue;const Tile p{here.x+dx,here.y+dy};if(!open(p))continue;
        const auto risk=danger(p);if(!std::isfinite(risk)||risk<0||risk>threat)continue;
        const int next=clearance(p,workspace),h=home(p);if(h<0||h>=65535)continue;
        if(next>gap||(next==gap&&h<home_best)){best=p;gap=next;home_best=h;}
    }
    return best;
}
}
