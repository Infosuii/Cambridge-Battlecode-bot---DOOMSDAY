#include <cambc.h>
#include "varg_group_geometry.h"
#include <cstdio>
#include <limits>
#include <vector>
namespace bc=cambc;
static char buf[8192];
static char* text(char* p,const char* s){while(*s)*p++=*s++;return p;}
static char* num(char* p,long long v){*p++=' ';if(v<0){*p++='-';v=-v;}char d[24];int n=0;do{d[n++]=static_cast<char>('0'+v%10);v/=10;}while(v);while(n)*p++=d[--n];return p;}
static void emit(char* p){*p++='\n';std::fwrite(buf,1,static_cast<std::size_t>(p-buf),stdout);}
int main(){
 bool done=false;
 for(;;){
  if(bc::is_draft()){
   const auto picks=bc::draft::current_draft(bc::team::ally);
   if(picks.empty())bc::draft::pick(bc::champion_draft::varg);
   else for(int i=0;i<11;++i){const auto p=static_cast<bc::champion_draft>(i);if(std::find(picks.begin(),picks.end(),p)==picks.end()){bc::draft::pick(p);break;}}
  }else if(!done&&bc::round_number()>=2&&bc::self().champion_name()==bc::champion_type::varg){
   done=true;
   const auto groups=bc::map::camp_groups();
   bc::end_turn(); // the first measured group also starts with a fresh normal100k turn
   for(const auto& g:groups){
    const auto start=bc::fuel_remaining();const auto round=bc::round_number();
    const auto members=g.camps();std::array<codex_varg::Point,12> points{};std::array<float,12> original{};
    if(members.size()>12){bc::end_turn();std::fputs("GEOM_OVERSIZE\n",stdout);bc::resign();}
    for(unsigned i=0;i<members.size();++i){const auto p=members[i].spawn_position();points[i]={p.x,p.y};original[i]=members[i].base_stats().base_health;}
    const auto shape=codex_varg::build(points.data(),members.size());
    struct Result{unsigned variant,damage,valid,attacks,factor,errors;};std::array<Result,12> rows{};unsigned index=0;
    for(unsigned variant=0;variant<4;++variant)for(float damage:{12.5f,50.0f,93.75f}){
     std::array<float,12> hp{};unsigned alive=0,errors=0;
     for(unsigned i=0;i<members.size();++i){hp[i]=variant==0?original[i]:variant==1?original[i]*.5f:variant==2?(i%2?0:original[i]):0;if(hp[i]>0)alive|=1u<<i;}
     for(unsigned i=0;i<members.size();++i){unsigned expected=0;for(unsigned j=0;j<members.size();++j)if(i!=j&&hp[j]>0&&std::max(std::abs(points[i].x-points[j].x),std::abs(points[i].y-points[j].y))<=1)++expected;if(expected!=codex_varg::neighbours(shape,i,alive))++errors;}
     const auto c=codex_varg::capability(shape,hp.data(),damage);
     rows[index++]={variant,std::bit_cast<unsigned>(damage),c.valid,c.attacks,std::bit_cast<unsigned>(c.factor),errors};
    }
    unsigned refusals=0;std::array<float,12> invalid=original;invalid[0]=-1;
    refusals+=!codex_varg::capability(shape,invalid.data(),50).valid;
    refusals+=!codex_varg::capability(shape,original.data(),0).valid;
    refusals+=!codex_varg::build(points.data(),13).valid;
    invalid[0]=std::numeric_limits<float>::quiet_NaN();refusals+=!codex_varg::capability(shape,invalid.data(),50).valid;
    const auto end_round=bc::round_number();const auto spent=100000ull*(end_round-round)+start-bc::fuel_remaining();
    bc::end_turn();char* p=text(buf,"VARG_GEOMETRY");for(auto v:{static_cast<unsigned>(static_cast<bc::handle_camp_group_t>(g)),static_cast<unsigned>(shape.n),static_cast<unsigned>(shape.components),static_cast<unsigned>(shape.cliques),refusals})p=num(p,v);p=num(p,spent);p=num(p,end_round-round);emit(p);
    for(unsigned i=0;i<shape.n;++i){p=text(buf,"VARG_POINT");p=num(p,i);p=num(p,points[i].x);p=num(p,points[i].y);p=num(p,std::bit_cast<unsigned>(original[i]));p=num(p,shape.adjacent[i]);emit(p);}
    for(unsigned i=0;i<shape.components;++i){p=text(buf,"VARG_COMPONENT");p=num(p,shape.component[i]);emit(p);}
    for(const auto& r:rows){p=text(buf,"VARG_CAPABILITY");for(auto v:{r.variant,r.damage,r.valid,r.attacks,r.factor,r.errors})p=num(p,v);emit(p);}bc::end_turn();
   }
   std::fputs("VARG_GEOMETRY_DONE\n",stdout);bc::resign();
  }
  bc::end_turn();
 }
}
