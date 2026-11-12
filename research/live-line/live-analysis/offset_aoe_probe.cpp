#include <cambc.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <optional>
#include <vector>
#ifndef PROBE_TYPE
#define PROBE_TYPE 0
#endif
#ifndef PROBE_DRAFT
#define PROBE_DRAFT 0
#endif
#ifndef PROBE_IDLE
#define PROBE_IDLE 0
#endif
namespace bc=cambc;
static int dist(bc::vec2 a,bc::vec2 b) { return std::max(std::abs(a.x-b.x),std::abs(a.y-b.y)); }
static bool bit(const bc::bitboard& board,bc::vec2 p) {
    const auto stride=bc::detail::layout().chunk_stride;
    return (board.ptr()[(p.y>>3)*stride+(p.x>>3)]>>(((p.y&7)<<3)|(p.x&7)))&1;
}
int main() {
    std::optional<bc::camp> target;
    for (;;) {
        try {
            if (bc::is_draft()) {
                const auto picks=bc::draft::current_draft(bc::team::ally);
                if (picks.empty()) bc::draft::pick(static_cast<bc::champion_draft>(PROBE_DRAFT));
                else for(int i=0;i<11;++i) {
                    const auto p=static_cast<bc::champion_draft>(i);
                    if(std::find(picks.begin(),picks.end(),p)==picks.end()) { bc::draft::pick(p);break; }
                }
            } else if (!PROBE_IDLE && static_cast<int>(bc::self().champion_name())==PROBE_TYPE) {
                if (bc::round_number()>=120) { std::printf("OFFSET_UNAVAILABLE 120\n");bc::resign(); }
                auto& me=bc::self();
                if (!me.is_alive()) { bc::end_turn();continue; }
                const auto pos=me.position();
                if (!target) {
                    int nearest=9999;
                    for (const auto& g:bc::map::camp_groups()) for(const auto& c:g.camps()) {
                        const int d=dist(pos,c.spawn_position());
                        if(d<nearest) { nearest=d;target=c; }
                    }
                }
                if (!target) { bc::end_turn();continue; }
                const auto at=target->spawn_position();
                const auto visible=bc::vision::visible_tiles();
                const int slot=PROBE_TYPE==0?0:1;
                const auto spell=me.abilities()[slot];
                const auto info=spell.get<bc::ability_aoe_damage>();
                if (dist(pos,at)==5 && bit(visible,at) && target->is_alive() && me.can_cast() && spell.cooldown()==0) {
                    for(int dy=-1;dy<=1;++dy) for(int dx=-1;dx<=1;++dx) {
                        const bc::vec2 aim{at.x+dx,at.y+dy};
                        if(aim.x<0||aim.y<0||aim.x>=bc::map::width()||aim.y>=bc::map::height()||dist(pos,aim)>info.range||!bit(visible,aim)) continue;
                        const float before=target->health();
                        const bool ok=spell.use(aim);
                        const float after=target->health();
                        std::printf("OFFSET_RESULT %u %d %d %d %d %d %d %d %d %d %.9g %.9g %.9g %.9g %.9g\n",
                            bc::round_number(),PROBE_TYPE,slot,pos.x,pos.y,at.x,at.y,aim.x,aim.y,ok,before,after,info.range,info.radius,info.modifier);
                        bc::resign();
                    }
                }
                if (me.can_move()) {
                    const auto blocked=bc::map::walls()|bc::map::holes()|bc::map::altars()|bc::map::spawn_region(bc::team::enemy)|bc::vision::champion_tiles();
                    struct Move{bc::vec2 delta;int value;};
                    std::vector<Move> options;
                    for(int dy=-1;dy<=1;++dy) for(int dx=-1;dx<=1;++dx) {
                        if(!dx&&!dy) continue;
                        const bc::vec2 to{pos.x+dx,pos.y+dy};
                        if(to.x<0||to.y<0||to.x>=bc::map::width()||to.y>=bc::map::height()||bit(blocked,to)) continue;
                        options.push_back({{dx,dy},std::abs(dist(to,at)-5)});
                    }
                    std::stable_sort(options.begin(),options.end(),[](const Move&a,const Move&b){return a.value<b.value;});
                    for(const auto& m:options) { try { if(me.move(m.delta))break; } catch(const bc::error&) {} }
                }
            }
        } catch(const std::exception& e) { std::printf("OFFSET_ERROR %s\n",e.what()); }
        bc::end_turn();
    }
}
