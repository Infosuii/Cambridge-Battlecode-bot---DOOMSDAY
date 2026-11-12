#include <cambc.h>
#include <cstdio>
#include <algorithm>

using namespace cambc;
template<class F> void query(const char* name,F f) {
    try { const auto value=f(); std::printf("CT_QUERY name=%s accepted=1 value=%llu code=0\n",name,static_cast<unsigned long long>(value)); }
    catch (const error& e) { std::printf("CT_QUERY name=%s accepted=0 value=0 code=%d\n",name,static_cast<int>(e.code())); }
}
int main() {
    if (is_draft()) {
        const std::array picks{champion_draft::vesper_vale,champion_draft::marcella,champion_draft::vendetta,
            champion_draft::heart_of_ruin,champion_draft::ryth};
        for (;;) { try { draft::pick(picks.at(draft::current_draft(team::ally).size())); } catch (...) {} end_turn(); }
    }
    const bool subject=self().champion_name()==champion_type::vesper_vale;
    const auto corner=map::spawn_region(team::ally).positions().front();
    const auto park=vec2{std::clamp(corner.x+(corner.x<map::width()/2?1:-1)*
        (8+static_cast<int>(static_cast<handle_champion_t>(self()))%5),0,map::width()-1),
        corner.y<map::height()/2?0:map::height()-1};
    const auto enemy_spawn=map::spawn_region(team::enemy).positions().front();
    const auto terrain=map::walls()|map::holes()|map::altars()|map::spawn_region(team::enemy);
    bitboard ring,visited;
    for (auto p:map::spawn_region(team::enemy).positions()) for (int dx=-1;dx<=1;++dx) for (int dy=-1;dy<=1;++dy) {
        auto q=p+vec2{dx,dy};
        if (map::is_in_bounds(q)&&!terrain.is_set(q)) ring.set(q);
    }
    bool hidden_done=false,visible_done=false;
    for (;;) {
        auto round=round_number();
        try {
            if (!subject) {
                if (self().can_move()&&!vision::has_champion(park)&&round_number()==round) self().move_towards(park);
            } else {
                if (!hidden_done) {
                    for (auto& enemy:champions(team::enemy)) if (!enemy.is_visible()) {
                        query("hidden_alive",[&]{return enemy.is_alive();});
                        query("hidden_gems",[&]{return enemy.gem_count();});
                        query("hidden_items",[&]{return enemy.item_count()[item_type::monster_shard_of_strength];});
                        query("hidden_cooldown",[&]{return enemy.abilities()[0].cooldown();});
                        hidden_done=true; break;
                    }
                }
                auto enemies=vision::champions(team::enemy);
                if (!visible_done&&!enemies.empty()) {
                    const auto& enemy=enemies.front();
                    query("visible_alive",[&]{return enemy.is_alive();});
                    query("visible_gems",[&]{return enemy.gem_count();});
                    query("visible_items",[&]{return enemy.item_count()[item_type::monster_shard_of_strength];});
                    query("visible_cooldown0",[&]{return enemy.abilities()[0].cooldown();});
                    query("visible_cooldown1",[&]{return enemy.abilities()[1].cooldown();});
                    visible_done=true;
                }
                if (!visible_done&&self().can_move()) {
                    auto blocked=terrain|vision::champion_tiles()|vision::camp_tiles();
                    blocked.set(self().position(),false);
                    distance_field field; field.compute(blocked,ring&~blocked,visited);
                    auto step=field.next_move_from(self().position());
                    if (step&&round_number()==round) self().move(*step);
                }
            }
        } catch (const std::exception& e) { std::printf("ERROR %s\n",e.what()); }
        if (round_number()!=round) continue;
        end_turn();
    }
}
