#include <cambc.h>
#include <algorithm>
#include <array>
#include <bit>
#include <cstdio>
#include <optional>
#include <stdexcept>
#include <vector>
#ifndef SELECT_MULTI
#define SELECT_MULTI 0
#endif
namespace bc=cambc;
static int dist(bc::vec2 a,bc::vec2 b){return std::max(std::abs(a.x-b.x),std::abs(a.y-b.y));}
static bool bit(const bc::bitboard& board,bc::vec2 p){const auto stride=bc::detail::layout().chunk_stride;return (board.ptr()[(p.y>>3)*stride+(p.x>>3)]>>(((p.y&7)<<3)|(p.x&7)))&1;}
struct Camp {bc::camp unit;std::uint32_t id,group;bc::vec2 pos;unsigned count;};
struct Row {std::uint32_t id,group,before,after;bc::vec2 pos;};
static char buffer[8192];
static char* text(char* p,const char* s){while(*s)*p++=*s++;return p;}
static char* number(char* p,long long v){if(v<0){*p++='-';v=-v;}char d[24];unsigned n=0;do{d[n++]=static_cast<char>('0'+v%10);v/=10;}while(v);while(n)*p++=d[--n];return p;}
static char* field(char* p,long long v){*p++=' ';return number(p,v);}
int main(){
    std::vector<Camp> camps;std::optional<std::uint32_t> chosen;
    for(;;){
        try{
            if(bc::is_draft()){
                const auto picks=bc::draft::current_draft(bc::team::ally);
                if(picks.empty())bc::draft::pick(bc::champion_draft::varg);
                else for(int i=0;i<11;++i){const auto p=static_cast<bc::champion_draft>(i);if(std::find(picks.begin(),picks.end(),p)==picks.end()){bc::draft::pick(p);break;}}
            }else if(bc::self().champion_name()==bc::champion_type::varg){
                auto& me=bc::self();
                if(bc::round_number()>=120){bc::end_turn();std::fputs("VARG_UNAVAILABLE 120\n",stdout);bc::resign();}
                if(!me.is_alive()){bc::end_turn();continue;}
                const auto pos=me.position();
                if(camps.empty()){
                    for(const auto& g:bc::map::camp_groups()){
                        const auto members=g.camps();const auto gid=static_cast<std::uint32_t>(static_cast<bc::handle_camp_group_t>(g));
                        for(const auto& c:members)camps.push_back({c,static_cast<std::uint32_t>(static_cast<bc::handle_camp_t>(c)),gid,c.spawn_position(),static_cast<unsigned>(members.size())});
                    }
                }
                if(!chosen){int nearest=100000;for(const auto& c:camps){if(SELECT_MULTI&&c.count<2)continue;const int d=dist(pos,c.pos);if(d<nearest){nearest=d;chosen=c.group;}}}
                if(!chosen){bc::end_turn();std::fputs("VARG_UNAVAILABLE no_group\n",stdout);bc::resign();}
                const auto visible=bc::vision::visible_tiles();int primary=-1,neighbours=-1,nearest=100000;bc::vec2 goal{};
                for(unsigned i=0;i<camps.size();++i){
                    const auto& c=camps[i];if(c.group!=*chosen)continue;
                    const int d=dist(pos,c.pos);if(d<nearest){nearest=d;goal=c.pos;}
                    if(d>1||!bit(visible,c.pos)||!c.unit.is_alive())continue;
                    int hits=0;for(const auto& o:camps)if(o.group==*chosen&&dist(o.pos,c.pos)<=1&&bit(visible,o.pos)&&o.unit.is_alive())++hits;
                    if(hits>neighbours){primary=static_cast<int>(i);neighbours=hits;}
                }
                if(primary>=0&&me.can_attack()){
                    const auto& target=camps[primary];std::array<Row,32> rows{};unsigned count=0;bool partial=false;
                    for(const auto& c:camps){
                        if(dist(c.pos,target.pos)>1)continue;
                        if(!bit(visible,c.pos)){partial=true;continue;}
                        if(!c.unit.is_alive())continue;
                        if(count>=rows.size())throw std::runtime_error("snapshot_capacity");
                        rows[count++]={c.id,c.group,std::bit_cast<std::uint32_t>(c.unit.health()),0,c.pos};
                    }
                    const auto round=bc::round_number(),actor=static_cast<std::uint32_t>(static_cast<bc::handle_champion_t>(me));
                    const auto strength=std::bit_cast<std::uint32_t>(me.strength());const auto start=bc::fuel_remaining();
                    me.attack(target.unit);
                    for(unsigned i=0;i<count;++i){
                        const auto c=std::find_if(camps.begin(),camps.end(),[&](const auto& c){return c.id==rows[i].id;});
                        const float hp=c->unit.is_alive()?c->unit.health():0.0f;rows[i].after=std::bit_cast<std::uint32_t>(hp);
                    }
                    const auto end_round=bc::round_number();
                    const auto spent=100000ull*(end_round-round)+start-bc::fuel_remaining();
                    const auto tpos=target.pos;const auto tid=target.id,tgroup=target.group;
                    bc::end_turn();
                    char* p=text(buffer,"VARG_ATTACK");for(auto v:{static_cast<long long>(round),static_cast<long long>(actor),static_cast<long long>(pos.x),static_cast<long long>(pos.y),static_cast<long long>(tgroup),static_cast<long long>(tid),static_cast<long long>(tpos.x),static_cast<long long>(tpos.y),static_cast<long long>(strength),static_cast<long long>(count),static_cast<long long>(partial),static_cast<long long>(spent),static_cast<long long>(end_round-round)})p=field(p,v);*p++='\n';
                    for(unsigned i=0;i<count;++i){p=text(p,"VARG_CAMP");for(auto v:{static_cast<long long>(rows[i].id),static_cast<long long>(rows[i].group),static_cast<long long>(rows[i].pos.x),static_cast<long long>(rows[i].pos.y),static_cast<long long>(rows[i].before),static_cast<long long>(rows[i].after)})p=field(p,v);*p++='\n';}
                    std::fwrite(buffer,1,static_cast<std::size_t>(p-buffer),stdout);bc::resign();
                }
                if(me.can_move()){
                    const auto blocked=bc::map::walls()|bc::map::holes()|bc::map::altars()|bc::map::spawn_region(bc::team::enemy)|bc::vision::champion_tiles()|bc::vision::camp_tiles();
                    struct Move{bc::vec2 d;int score;};std::vector<Move> options;
                    for(int dy=-1;dy<=1;++dy)for(int dx=-1;dx<=1;++dx){if(!dx&&!dy)continue;const bc::vec2 to{pos.x+dx,pos.y+dy};if(to.x<0||to.y<0||to.x>=bc::map::width()||to.y>=bc::map::height()||bit(blocked,to))continue;options.push_back({{dx,dy},dist(to,goal)});}
                    std::stable_sort(options.begin(),options.end(),[](auto&a,auto&b){return a.score<b.score;});
                    for(const auto& m:options)try{if(me.move(m.d))break;}catch(const bc::error&){}
                }
            }
        }catch(const std::exception& e){bc::end_turn();std::fputs("VARG_ERROR\n",stdout);bc::resign();}
        bc::end_turn();
    }
}
