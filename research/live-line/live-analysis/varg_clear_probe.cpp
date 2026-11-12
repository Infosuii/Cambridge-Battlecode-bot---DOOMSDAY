#include <cambc.h>
#include <algorithm>
#include <array>
#include <bit>
#include <cstdio>
#include <optional>
#include <vector>
#ifndef SELECT_ISOLATED
#define SELECT_ISOLATED 0
#endif
namespace bc=cambc;
static int dist(bc::vec2 a,bc::vec2 b){return std::max(std::abs(a.x-b.x),std::abs(a.y-b.y));}
static bool bit(const bc::bitboard& b,bc::vec2 p){return (b.ptr()[(p.y>>3)*bc::detail::layout().chunk_stride+(p.x>>3)]>>(((p.y&7)<<3)|(p.x&7)))&1;}
static unsigned bits(float f){return std::bit_cast<unsigned>(f);}
static char buf[8192];
static char* text(char* p,const char* s){while(*s)*p++=*s++;return p;}
static char* num(char* p,long long v){*p++=' ';if(v<0){*p++='-';v=-v;}char d[24];int n=0;do{d[n++]=static_cast<char>('0'+v%10);v/=10;}while(v);while(n)*p++=d[--n];return p;}
static void emit(char* p){*p++='\n';std::fwrite(buf,1,static_cast<std::size_t>(p-buf),stdout);}
struct Camp{bc::camp unit;unsigned id;bc::vec2 pos;float initial,strength;bool dead=false;};
struct Row{unsigned before=~0u,after=~0u;};
struct Frame{unsigned round,primary,strength,hp;bc::vec2 pos;std::array<Row,12> camps;};
int main(){
 std::vector<Camp> camps;std::vector<Frame> frames;std::vector<unsigned short> visits;
 bool selected=false;unsigned group=~0u,actor=~0u,first=0,last=0,initial_hp=0,final_hp=0,reason=0;
 for(;;){
  try{
   if(bc::is_draft()){
    const auto picks=bc::draft::current_draft(bc::team::ally);
    if(picks.empty())bc::draft::pick(bc::champion_draft::varg);
    else for(int i=0;i<11;++i){const auto p=static_cast<bc::champion_draft>(i);if(std::find(picks.begin(),picks.end(),p)==picks.end()){bc::draft::pick(p);break;}}
   }else if(bc::self().champion_name()==bc::champion_type::varg){
    auto& me=bc::self();actor=static_cast<unsigned>(static_cast<bc::handle_champion_t>(me));
    if(!selected){
     selected=true;frames.reserve(320);visits.resize(bc::map::width()*bc::map::height());int nearest=100000;
     const auto pos=me.position();initial_hp=bits(me.health());
     for(const auto& g:bc::map::camp_groups()){
      const auto cs=g.camps();if(SELECT_ISOLATED?(cs.size()!=1):(cs.size()<2))continue;
      for(const auto& c:cs){const int d=dist(pos,c.spawn_position());if(d<nearest){nearest=d;group=static_cast<unsigned>(static_cast<bc::handle_camp_group_t>(g));camps.clear();for(const auto& member:cs){const auto s=member.base_stats();camps.push_back({member,static_cast<unsigned>(static_cast<bc::handle_camp_t>(member)),member.spawn_position(),s.base_health,s.base_strength});}}}
     }
     if(camps.empty())reason=4;else if(camps.size()>12)reason=5;
    }
    const bool alive=me.is_alive();final_hp=alive?bits(me.health()):0;last=bc::round_number();
    if(!reason&&!alive)reason=2;
    if(!reason&&last>=300)reason=3;
    if(!reason){
     const auto pos=me.position();const auto visible=bc::vision::visible_tiles();
     std::array<float,12> hp{},strength{};std::array<bool,12> known{};unsigned live=0;
     for(unsigned i=0;i<camps.size();++i){auto& c=camps[i];if(bit(visible,c.pos)){known[i]=true;c.dead=!c.unit.is_alive();if(!c.dead){hp[i]=c.unit.health();strength[i]=c.unit.strength();}}if(!c.dead)++live;}
     if(live==0)reason=1;
     else{
      int primary=-1;float best=1e30f;
      for(unsigned i=0;i<camps.size();++i){if(!known[i]||camps[i].dead||dist(pos,camps[i].pos)>1)continue;int neighbours=0;for(unsigned j=0;j<camps.size();++j)if(i!=j&&!camps[j].dead&&dist(camps[i].pos,camps[j].pos)<=1)++neighbours;
       const float key=hp[i]-1000*strength[i]-2000*neighbours;if(key<best){best=key;primary=static_cast<int>(i);}}
      if(primary>=0&&me.can_attack()){
       if(!first)first=last;Frame f{last,camps[primary].id,bits(me.strength()),bits(me.health()),pos,{}};
       for(unsigned i=0;i<camps.size();++i)if(known[i])f.camps[i].before=bits(hp[i]);
       me.attack(camps[primary].unit);
       for(unsigned i=0;i<camps.size();++i)if(known[i]){camps[i].dead=!camps[i].unit.is_alive();f.camps[i].after=camps[i].dead?0:bits(camps[i].unit.health());}
       frames.push_back(f);if(std::all_of(camps.begin(),camps.end(),[](const auto& c){return c.dead;}))reason=1;
      }
      // A diagnostic path only: avoid repeated greedy two-tile loops, no hidden information.
      if(!reason&&primary<0&&me.can_move()){
       ++visits[pos.y*bc::map::width()+pos.x];const auto blocked=bc::map::walls()|bc::map::holes()|bc::map::altars()|bc::map::spawn_region(bc::team::enemy)|bc::vision::champion_tiles()|bc::vision::camp_tiles();
       struct Move{bc::vec2 d;int score;};std::vector<Move> options;
       for(int dy=-1;dy<=1;++dy)for(int dx=-1;dx<=1;++dx){if(!dx&&!dy)continue;const bc::vec2 to{pos.x+dx,pos.y+dy};if(to.x<0||to.y<0||to.x>=bc::map::width()||to.y>=bc::map::height()||bit(blocked,to))continue;int distance=100000;for(const auto& c:camps)if(!c.dead)distance=std::min(distance,dist(to,c.pos));options.push_back({{dx,dy},4*distance+10*visits[to.y*bc::map::width()+to.x]});}
       std::stable_sort(options.begin(),options.end(),[](const auto& a,const auto& b){return a.score<b.score;});for(const auto& m:options)try{if(me.move(m.d))break;}catch(const bc::error&){}
      }
     }
    }
    if(reason){
     bc::end_turn();char* p=text(buf,"VARG_TASK");for(auto v:{group,actor,first,last,initial_hp,final_hp,reason,static_cast<unsigned>(camps.size()),static_cast<unsigned>(frames.size())})p=num(p,v);emit(p);
     for(const auto& c:camps){p=text(buf,"VARG_DESIGN");p=num(p,c.id);p=num(p,c.pos.x);p=num(p,c.pos.y);p=num(p,bits(c.initial));p=num(p,bits(c.strength));emit(p);}bc::end_turn();
     for(const auto& f:frames){p=text(buf,"VARG_STEP");for(auto v:{f.round,f.primary,f.strength,f.hp})p=num(p,v);p=num(p,f.pos.x);p=num(p,f.pos.y);emit(p);
      for(unsigned i=0;i<camps.size();++i){p=text(buf,"VARG_HP");p=num(p,camps[i].id);p=num(p,f.camps[i].before);p=num(p,f.camps[i].after);emit(p);}bc::end_turn();}
     bc::resign();
    }
   }
  }catch(const std::exception&){reason=6;}
  bc::end_turn();
 }
}
