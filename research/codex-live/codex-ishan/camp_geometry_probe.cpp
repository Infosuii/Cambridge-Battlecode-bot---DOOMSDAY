#include <cambc.h>
#include <algorithm>
#include <cstdio>
#include <vector>
namespace bc=cambc;
int main() {
    bool printed=false;
    for(;;) {
        if(!bc::is_draft())bc::resign();
        if(!printed) {
            const auto start=bc::fuel_remaining();
            const auto groups=bc::map::camp_groups();
            std::printf("GEOMETRY %d %d %zu\n",bc::map::width(),bc::map::height(),groups.size());
            for(const auto& g:groups) {
                const auto handle=static_cast<std::uint32_t>(static_cast<bc::handle_camp_group_t>(g));
                std::printf("GROUP %u %u %u %d %zu\n",handle,g.gold_value(),g.gem_value(),g.max_respawn_timer(),g.camps().size());
                for(const auto& c:g.camps()) {
                    const auto p=c.spawn_position();const auto s=c.base_stats();
                    std::printf("CAMP %u %u %d %d %d %.9g %.9g %d\n",handle,
                        static_cast<std::uint32_t>(static_cast<bc::handle_camp_t>(c)),static_cast<int>(c.kind()),p.x,p.y,
                        s.base_health,s.base_strength,s.base_attack_range);
                }
            }
            std::printf("GEOMETRY_COST %llu\n",static_cast<unsigned long long>(start-bc::fuel_remaining()));
            printed=true;
        }
        const auto picks=bc::draft::current_draft(bc::team::ally);
        for(int i=0;i<11;++i) {
            const auto p=static_cast<bc::champion_draft>(i);
            if(std::find(picks.begin(),picks.end(),p)==picks.end()){bc::draft::pick(p);break;}
        }
        bc::end_turn();
    }
}
