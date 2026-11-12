#include <cambc.h>
#include <cstdio>
#include <algorithm>
using namespace cambc;
struct Outcome {bool ok=false;int code=0;};
template<class Work> Outcome attempt(Work work){try{return {work(),0};}catch(const error& e){return {false,static_cast<int>(e.code())};}}
int main() {
    if(is_draft()) {
        const std::array picks{champion_draft::vesper_vale,champion_draft::vendetta,champion_draft::heart_of_ruin,champion_draft::ren,champion_draft::ryth};
        for(;;){try{draft::pick(picks.at(draft::current_draft(team::ally).size()));}catch(...){}end_turn();}
    }
    bool done=false;
    for(;;) {
        const auto round=round_number();
        try {
            if(!done&&self().is_alive())for(const auto& ability:self().abilities())if(ability.is_dash()&&ability.is_ready()) {
                const auto info=std::get<ability_dash>(*ability.info());const auto origin=self().position();
                const auto blocked=map::walls()|map::holes()|map::altars()|map::spawn_region(team::enemy)|vision::champion_tiles()|vision::camp_tiles()|vision::teleport_tiles();
                std::optional<vec2> landing;
                for(int dx=-1;dx<=1&&!landing;++dx)for(int dy=-1;dy<=1&&!landing;++dy) {
                    const auto p=origin+vec2{dx,dy};if((!dx&&!dy)||!map::is_in_bounds(p)||blocked.is_set(p)||origin.chebyshev_distance(p)>info.range)continue;landing=p;
                }
                if(!landing)continue;
                const bool attack_before=self().can_attack();
                auto cast=attempt([&]{return ability.use(*landing);});const auto after=self().position();const auto cooldown=ability.cooldown();
                const bool attack_after=self().can_attack();
                Outcome again;
                for(const auto& other:self().abilities())if(!other.is_dash()&&other.info()) {again=attempt([&]{return other.use();});break;}
                auto move=attempt([&]{return self().move_absolute(origin);});
                const bool geometry=cast.ok&&after==*landing&&after!=origin;
                const bool allowance=info.exclusive_with_movement?!move.ok&&move.code==127:move.ok;
                const auto type=static_cast<int>(self().champion_name());
                std::printf("CT_DASH type=%d exclusive=%d from=%d,%d to=%d,%d cd=%d cast=%d move=%d move_code=%d second=%d second_code=%d\n",type,info.exclusive_with_movement,origin.x,origin.y,after.x,after.y,cooldown,cast.ok,move.ok,move.code,again.ok,again.code);
                std::printf("CT_CHECK name=dash_geometry_%d pass=%d\nCT_CHECK name=dash_cooldown_%d pass=%d\nCT_CHECK name=dash_allowance_%d pass=%d\nCT_CHECK name=dash_one_cast_%d pass=%d\n",type,geometry,type,cooldown>0,type,allowance,type,!again.ok&&again.code==27);
                std::printf("CT_CHECK name=dash_attack_%d pass=%d\n",type,attack_before==attack_after);
                done=true;break;
            }
        }catch(const std::exception& e){std::printf("ERROR %s\n",e.what());done=true;}
        if(round_number()!=round)continue;end_turn();
    }
}
