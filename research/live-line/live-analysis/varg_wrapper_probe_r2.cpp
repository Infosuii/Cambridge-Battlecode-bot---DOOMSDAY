#include "bot.h"
#include <bit>
#include <cstdio>
static char buffer[8192];
static char* text(char* p,const char* s){while(*s)*p++=*s++;return p;}
static char* num(char* p,long long v){*p++=' ';if(v<0){*p++='-';v=-v;}char d[24];int n=0;do{d[n++]=static_cast<char>('0'+v%10);v/=10;}while(v);while(n)*p++=d[--n];return p;}
static void emit(char* p){*p++='\n';std::fwrite(buffer,1,static_cast<std::size_t>(p-buffer),stdout);}
void codex_varg_probe(Bot& bot,bool setup){
 if(setup){
  for(const auto& group:bc::map::camp_groups()){
   auto& g=bot.w.groups.emplace_back();g.handle=static_cast<unsigned>(static_cast<bc::handle_camp_group_t>(group));
   for(const auto& c:group.camps()){
    const auto s=c.base_stats();g.camps.push_back(bot.w.camps.size());
    bot.w.camps.push_back({c,c.spawn_position(),c.kind(),s.base_health,s.base_strength,s.base_health,false,s.base_attack_range});
   }
  }
  bot.type=bc::champion_type::varg;bot.range=1;return;
 }
 for(auto& g:bot.w.groups){
  char* p=text(buffer,"VARG_WRAPPER_GROUP");p=num(p,g.handle);p=num(p,g.camps.size());emit(p);
  for(int ci:g.camps){const auto& c=bot.w.camps[ci];p=text(buffer,"VARG_WRAPPER_CAMP");p=num(p,ci);p=num(p,c.pos.x);p=num(p,c.pos.y);p=num(p,std::bit_cast<unsigned>(c.max_hp));p=num(p,std::bit_cast<unsigned>(c.strength));emit(p);}bc::end_turn();
  for(unsigned variant=0;variant<12;++variant){
   const auto start=bc::fuel_remaining();const auto round=bc::round_number();
   bot.strength=variant==4?12.5f:variant==5?93.75f:50.0f;bot.camp_dealt_mult=variant==10?1.5f:1.0f;
#if V55_HEART_MODEL
   bot.cached_dps=bot.strength;
#endif
   g.state=variant==8?GroupState::respawning:GroupState::alive;
   for(unsigned i=0;i<g.camps.size();++i){auto& c=bot.w.camps[g.camps[i]];
    c.dead=(variant==2&&(i%2))||variant==3||(variant==11&&i+1==g.camps.size());
    c.hp=variant==1?c.max_hp*.5f:variant==7?bot.w.camps[g.camps[g.camps.size()-1-i]].max_hp:variant==8?0:((variant==9||variant==10)&&i==0)?1:c.max_hp;
   }
   const float factor=bot.varg_capability(g);const auto after=bc::fuel_remaining();
   const float hot=bot.varg_capability(g);const auto hot_end=bc::fuel_remaining();
   const float dps=bot.my_dps(&g);
   bot.w.visible.clear();for(unsigned i=0;i<g.camps.size();++i)if(variant%3!=1||i%2==0)bot.w.visible.set(bot.w.camps[g.camps[i]].pos,true);
   bot.pos=bot.w.camps[g.camps[variant%g.camps.size()]].pos;--bot.pos.x;bot.pos.y+=static_cast<int>(variant%3)-1;
   int expected=-1;float best=1e30f;
   for(int ci:g.camps){const auto& c=bot.w.camps[ci];if(c.dead||!bit(bot.w.visible,c.pos)||cheb(c.pos,bot.pos)>bot.range)continue;
    float key=c.hp-c.strength*1000.0f;int neighbours=0;for(int other:g.camps)if(other!=ci&&!bot.w.camps[other].dead&&cheb(bot.w.camps[other].pos,c.pos)<=1)++neighbours;
    key-=neighbours*2000.0f;if(key<best){best=key;expected=ci;}}
   const int selected=bot.varg_target(g);
   const auto end_round=bc::round_number();const auto total=100000ull*(end_round-round)+start-bc::fuel_remaining();
   bc::end_turn();p=text(buffer,"VARG_WRAPPER");p=num(p,g.handle);p=num(p,variant);p=num(p,std::bit_cast<unsigned>(factor));p=num(p,std::bit_cast<unsigned>(hot));p=num(p,std::bit_cast<unsigned>(dps));p=num(p,selected);p=num(p,expected);p=num(p,start-after);p=num(p,after-hot_end);p=num(p,total);p=num(p,end_round-round);emit(p);bc::end_turn();
  }
 }
 std::fputs("VARG_WRAPPER_DONE\n",stdout);bc::resign();
}
int main(){
 Bot bot;bool setup=false;
 for(;;){
  if(bc::is_draft()){
   const auto picks=bc::draft::current_draft(bc::team::ally);
   if(picks.empty())bc::draft::pick(bc::champion_draft::varg);
   else for(int i=0;i<11;++i){const auto p=static_cast<bc::champion_draft>(i);if(std::find(picks.begin(),picks.end(),p)==picks.end()){bc::draft::pick(p);break;}}
  }else if(bc::self().champion_name()==bc::champion_type::varg){
   if(!setup){codex_varg_probe(bot,true);setup=true;bc::end_turn();char* p=text(buffer,"VARG_WRAPPER_SETUP");p=num(p,bc::round_number());emit(p);}
   if(bc::round_number()>=2)codex_varg_probe(bot,false);
  }
  bc::end_turn();
 }
}
