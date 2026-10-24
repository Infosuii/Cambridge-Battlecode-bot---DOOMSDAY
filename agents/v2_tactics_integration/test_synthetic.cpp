// Synthetic SDK state only; includes the production builder/executor implementation.
#include "../../bot/src/common.h"
#include "../../bot/src/world.h"
#include <string>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#define private public
#include "../../bot/src/bot.h"
#undef private
#include "../../bot/src/nn_policy_tactics.cpp"

namespace synthetic {
constinit cambc::detail::champion_info champion[64]{};
constinit cambc::detail::ability_props props[2]{};
constinit int cooldown[2]{},moves=0,casts=0,attacks=0,castslot=-1;
constinit std::uint32_t attacked=0,casttarget=0;
constinit int castx=-1,casty=-1;
constinit bool refused=false,flip=false;
int checks=0;
void check(bool ok,const char* message){++checks;if(!ok){std::fprintf(stderr,"FAIL %s\n",message);std::exit(1);}}
}
namespace cambc::detail {
extern "C" {
std::int32_t sdk_get_settings(game_settings* out){*out={};out->max_rounds=2000;out->winning_gems=1000;return 0;}
std::int32_t sdk_item_info(std::uint32_t,item_info* out){*out={};return 0;}
std::int32_t sdk_consumable_info(std::uint32_t,consumable_info* out){*out={};return 0;}
std::int32_t sdk_shared_memory_size(std::uint32_t* out){*out=8;return 0;}
std::int32_t sdk_draft_memory_size(std::uint32_t* out){*out=0;return 0;}
std::int32_t sdk_read_draft_memory(std::int32_t,void*,std::uint32_t){return 0;}
std::int32_t sdk_my_champion(){return 1;}
std::int32_t sdk_my_team(){return 0;}
std::int32_t sdk_champion_design(std::int32_t,champion_design* out){*out={};return 0;}
std::int32_t sdk_champion_ability_props(std::uint32_t,std::uint32_t slot,ability_props* out){*out=synthetic::props[slot];return 0;}
std::int32_t sdk_champion(std::uint32_t id,champion_info* out){if(id>=64)return 1;*out=synthetic::champion[id];return 0;}
std::int32_t sdk_champion_identity(std::uint32_t id,champion_identity* out){*out={synthetic::champion[id].team,synthetic::champion[id].type};return 0;}
std::int32_t sdk_champion_cooldown(std::uint32_t,std::uint32_t slot,std::int32_t* out){*out=synthetic::cooldown[slot];return 0;}
std::int32_t sdk_champion_gems(std::uint32_t,std::uint32_t* out){*out=7;return 0;}
std::int32_t sdk_champion_channel_time(std::uint32_t,std::int32_t* out){*out=4;return 0;}
std::int32_t sdk_champion_ability_damage(std::uint32_t,std::uint32_t slot,float* out){*out=42+slot;return 0;}
std::int32_t sdk_champion_ability_damage_against(std::uint32_t,std::uint32_t slot,std::uint32_t,float* out){*out=42+slot;return 0;}
std::int32_t sdk_bc_get_last_error(char*,std::uint32_t){return 0;}
std::int32_t sdk_bc_metadata(metadata* out){*out={8,8,1,1,1,8,128};return 0;}
std::int32_t sdk_camp_design(std::int32_t,camp_design* out){*out={};return 0;}
std::int32_t sdk_bc_map_mask(std::int32_t,std::uint64_t* out){*out=0;return 0;}
std::int32_t sdk_bc_map_symmetry(std::int32_t* out){*out=0;return 0;}
std::int32_t sdk_spawn_region(std::int32_t team,aabb* out){*out=team?aabb{7,7,8,8}:aabb{0,0,1,1};return 0;}
std::int32_t sdk_Bitboard_Set(std::uint64_t* out,std::int32_t x,std::int32_t y,std::int32_t value){
    if(value)*out|=1ull<<(y*8+x);else *out&=~(1ull<<(y*8+x));return 0;}
std::int32_t sdk_Bitboard_ImportRawBuffer(std::uint64_t* out,const std::uint8_t* bytes,std::size_t size){std::memcpy(out,bytes,size);return 0;}
std::int32_t sdk_Bitboard_Zero(std::uint64_t* out){*out=0;return 0;}
std::int32_t sdk_Bitboard_Union(const std::uint64_t* a,const std::uint64_t* b,std::uint64_t* out){*out=*a|*b;return 0;}
std::int32_t sdk_Bitboard_IsZero(const std::uint64_t* a,std::int32_t* out){*out=*a==0;return 0;}
std::int32_t sdk_DistanceField_ComputeWithExpansionCount(const std::uint64_t* walls,const std::uint64_t* roots,std::uint64_t* visited,
    std::uint16_t* distances,std::uint16_t max,std::uint16_t* count){
    for(int i=0;i<64;++i)distances[i]=65535;
    int queue[64],read=0,write=0;*visited=0;*count=0;
    for(int i=0;i<64;++i)if((*roots>>i)&1u)distances[i]=0,queue[write++]=i,*visited|=1ull<<i;
    while(read<write){int at=queue[read++];if(distances[at]>=max)continue;
        for(int dy=-1;dy<=1;++dy)for(int dx=-1;dx<=1;++dx){int x=at%8+dx,y=at/8+dy;if(x<0||y<0||x>=8||y>=8)continue;
            int next=y*8+x;if(((*walls>>next)&1u)||distances[next]!=65535)continue;
            distances[next]=distances[at]+1;queue[write++]=next;*visited|=1ull<<next;*count=std::max(*count,distances[next]);}}
    return 0;
}
std::int32_t sdk_Bitboard_ReachableMaskWithScratch(const std::uint64_t* walls,std::int32_t x,std::int32_t y,std::uint64_t* out,
    std::uint16_t radius,std::uint64_t*,std::uint64_t*){std::uint16_t distances[64],count;std::uint64_t roots=1ull<<(y*8+x);
    return sdk_DistanceField_ComputeWithExpansionCount(walls,&roots,out,distances,radius,&count);}
std::int32_t sdk_move_to(std::int32_t x,std::int32_t y,std::int32_t* success){++synthetic::moves;*success=!synthetic::refused;
    if(*success)synthetic::champion[1].x=x,synthetic::champion[1].y=y,synthetic::champion[1].state&=~(1<<3);return 0;}
std::int32_t sdk_cast(std::uint32_t slot,std::uint32_t,std::uint32_t target,std::int32_t x,std::int32_t y,std::int32_t* success){
    ++synthetic::casts;synthetic::castslot=slot;synthetic::casttarget=target;synthetic::castx=x;synthetic::casty=y;*success=!synthetic::refused;
    if(*success){synthetic::champion[1].state&=~(1<<11);if(synthetic::props[slot].kind==1)synthetic::champion[1].state|=1<<4;
        if(synthetic::props[slot].kind==6)synthetic::champion[1].x=x,synthetic::champion[1].y=y;}return 0;}
std::int32_t sdk_attack(std::uint32_t,std::uint32_t target){++synthetic::attacks;synthetic::attacked=target;
    synthetic::champion[1].state&=~(1<<4);synthetic::champion[target].health=0;return 0;}
std::int32_t sdk_is_visible(std::int32_t,std::int32_t,std::int32_t* out){*out=1;return 0;}
std::int32_t sdk_camp(std::uint32_t,camp_state* out){*out={};out->health=100;return 0;}
}
}
namespace nnp { vec2 canonical(const Bot&,vec2 q){return synthetic::flip?vec2{7-q.x,7-q.y}:q;} }

using synthetic::check;
void reset(Bot& b){
    std::memset(synthetic::champion,0,sizeof synthetic::champion);std::memset(synthetic::props,0,sizeof synthetic::props);
    synthetic::cooldown[0]=synthetic::cooldown[1]=0;synthetic::moves=synthetic::casts=synthetic::attacks=0;
    synthetic::refused=synthetic::flip=false;synthetic::castslot=-1;synthetic::casttarget=0;synthetic::castx=synthetic::casty=-1;
    synthetic::champion[1]={0,0,3,3,500,1000,50,100,1,3,1|(1<<3)|(1<<4)|(1<<11)};
    b.w.width=b.w.height=8;b.my_id=1;b.pos={3,3};b.hp=500;b.max_hp=1000;b.strength=50;b.focus=100;b.gems=7;
    b.walked=b.cast_done=false;b.w.enemies.clear();b.w.allies.clear();b.w.camps.clear();b.w.spawn_tiles={{0,0}};
    *b.w.static_blocked.ptr()=0;*b.w.unit_tiles.ptr()=0;*b.w.visible.ptr()=~0ull;*b.w.bushes.ptr()=0;
    *b.w.ally_spawn.ptr()=1;
    if(g_boards)g_boards->goal_ready=g_boards->home_ready=false;
    cambc::detail::cached_self=cambc::detail::handle_access::make_champion(static_cast<bc::handle_champion_t>(1));
    bc::bitboard visited;b.w.spawn_field.compute(b.w.static_blocked,b.w.ally_spawn,visited);
}
void rebuild_self(){cambc::detail::cached_self=cambc::detail::handle_access::make_champion(static_cast<bc::handle_champion_t>(1));}
void enemy(Bot& b,int handle,int x,int y,int state=1){
    synthetic::champion[handle]={1,0,x,y,100,200,30,100,1,1,state};
    auto unit=cambc::detail::handle_access::make_champion(static_cast<bc::handle_champion_t>(handle));
    b.w.enemies.push_back({unit,{x,y},100,200,30,100,1,bc::champion_type::ryth,5,static_cast<std::uint32_t>(handle),static_cast<std::uint32_t>(state)});
    *b.w.unit_tiles.ptr()|=1ull<<(y*8+x);
}
int find(const nnpc::Decision& decision,std::uint32_t id){for(int i=0;i<decision.K;++i)if(decision.id[i]==id)return i;return -1;}
std::uint32_t moveid(unsigned kind,int x,int y){std::uint32_t id=0;check(nnpc::move_id(kind,x,y,id),"valid move ID");return id;}
std::uint32_t combatid(unsigned kind,std::uint32_t handle){std::uint32_t id=0;check(nnpc::combat_id(kind,handle,id),"valid combat ID");return id;}
int main(){Bot b;nnp::OptionsState state{};state.goal={7,7};nnpc::Decision out{};
    reset(b);check(nnp::build_move(b,state,out)&&out.K==9,"eight adjacent walk choices and hold");
    for(int i=1;i<out.K;++i)check(out.id[i-1]<out.id[i],"canonical ascending movement IDs");
    const auto right=moveid(0,4,3);int row=find(out,right);check(row>=0,"east step generated");
    check(out.feat[row*12]==0.125f&&out.feat[row*12+2]==0.08f,"F12 displacement and static goal distance");
    *b.w.unit_tiles.ptr()|=1ull<<(3*8+4);check(nnp::build_move(b,state,out)&&find(out,right)<0,"occupied endpoint excluded");
    check(!nnp::execute_move(b,state,right).executed&&synthetic::moves==0,"execution rechecks occupancy");
    *b.w.unit_tiles.ptr()=0;synthetic::refused=true;auto ack=nnp::execute_move(b,state,right);
    check(ack.legal&&!ack.executed&&!ack.changed&&!b.walked,"hidden obstruction refusal preserves state");
    synthetic::refused=false;ack=nnp::execute_move(b,state,right);check(ack.executed&&ack.changed&&b.walked&&b.pos==vec2{4,3},"walk executes exact endpoint");
    check(!nnp::execute_move(b,state,moveid(0,5,3)).executed,"consumed move allowance rejected");
    ack=nnp::execute_move(b,state,moveid(3,4,3));check(ack.executed&&!ack.changed,"hold accepted without state mutation");
    check(!nnp::execute_move(b,state,moveid(3,3,3)).executed,"stale hold position rejected");
    reset(b);synthetic::flip=true;check(nnp::build_move(b,state,out)&&find(out,moveid(0,3,4))>=0,"rotated canonical movement ID");
    ack=nnp::execute_move(b,state,moveid(0,3,4));check(ack.executed&&b.pos==vec2{4,3},"rotated ID executes world endpoint");
    reset(b);synthetic::props[1].kind=6;synthetic::props[1].targets=d::ability_target_ground;synthetic::props[1].cooldown=8;
    synthetic::props[1].payload.dash={2,1,1.5f,1};rebuild_self();check(nnp::build_move(b,state,out)&&out.K<=16,"dash choices bounded with diversity");
    bool hasdash=false;for(int i=0;i<out.K;++i)hasdash|=(out.id[i]>>30)==2;check(hasdash,"dash kind retained in narrowing");
    ack=nnp::execute_move(b,state,moveid(2,5,3));check(ack.executed&&b.cast_done&&!b.walked&&b.pos==vec2{5,3},"dash executes selected slot and endpoint");
    reset(b);enemy(b,2,4,3);check(nnp::build_combat(b,state,out)&&find(out,combatid(0,2))>=0,"explicit visible enemy basic attack");
    ack=nnp::execute_combat(b,state,combatid(0,2));check(ack.executed&&ack.changed&&synthetic::attacked==2,"attack exact handle once");
    check(!nnp::execute_combat(b,state,combatid(0,2)).executed,"killed stale target rejected");
    reset(b);enemy(b,2,7,7);check(nnp::build_combat(b,state,out)&&out.K==1&&out.id[0]==3,"out of range combat contains hold only");
    ack=nnp::execute_combat(b,state,3);check(ack.legal&&ack.executed&&!ack.changed,"combat hold is intentional execution");
    check(!nnp::execute_combat(b,state,7).executed,"invalid nonzero-handle hold rejected");
    reset(b);enemy(b,2,4,3);synthetic::props[0].kind=3;synthetic::props[0].targets=d::ability_target_enemies|d::ability_target_camps|d::ability_target_ground;
    synthetic::props[0].attributes=d::ability_attribute_exclusive_with_movement;synthetic::props[0].cooldown=8;
    synthetic::props[0].payload.aoe_damage={4,1,2,1};rebuild_self();
    check(nnp::build_combat(b,state,out)&&find(out,combatid(1,2))>=0,"target centered AoE generated");
    row=find(out,combatid(1,2));check(out.feat[row*12+8]==42*0.001f&&out.feat[row*12+9]==0.4f,"SDK direct damage and configured cooldown F12");
    b.walked=true;check(!nnp::execute_combat(b,state,combatid(1,2)).executed,"exclusive cast rejected after movement");
    b.walked=false;synthetic::cooldown[0]=1;check(!nnp::execute_combat(b,state,combatid(1,2)).executed,"live cooldown recheck");
    synthetic::cooldown[0]=0;ack=nnp::execute_combat(b,state,combatid(1,2));
    check(ack.executed&&synthetic::castslot==0&&synthetic::castx==4&&synthetic::casty==3&&synthetic::casttarget==0,"AoE uses exact represented ground center");
    reset(b);synthetic::props[0].kind=1;synthetic::props[0].targets=d::ability_target_self;rebuild_self();
    check(nnp::build_combat(b,state,out)&&find(out,combatid(1,1))>=0,"self attack reset generated");
    ack=nnp::execute_combat(b,state,combatid(1,1));check(ack.executed&&synthetic::casttarget==0&&synthetic::castx==-1,"attack reset is untargeted cast");
    reset(b);synthetic::props[0].kind=7;synthetic::props[0].targets=d::ability_target_self;rebuild_self();
    check(nnp::build_combat(b,state,out)&&find(out,combatid(1,1))>=0,"self shield generated");
    reset(b);synthetic::props[0].kind=5;synthetic::props[0].targets=d::ability_target_allies;synthetic::props[0].payload.heal={4,3};rebuild_self();
    synthetic::champion[3]={0,0,4,3,100,200,30,100,1,1,1};auto ally=d::handle_access::make_champion(static_cast<bc::handle_champion_t>(3));
    b.w.allies.push_back({ally,{4,3},100,200,30,1,3,100,bc::champion_type::willow});
    check(nnp::build_combat(b,state,out)&&find(out,combatid(1,3))>=0&&find(out,combatid(1,1))<0,"heal respects ally vs self mask");
    ack=nnp::execute_combat(b,state,combatid(1,3));check(ack.executed&&synthetic::casttarget==3,"heal executes explicit ally");
    reset(b);enemy(b,2,4,3);auto monster=d::handle_access::make_camp(static_cast<bc::handle_camp_t>(2),static_cast<bc::handle_camp_group_t>(1),bc::camp_type::wolf,{2,3});
    b.w.camps.push_back({monster,{2,3},bc::camp_type::wolf,100,10,100,false,1});
    check(nnp::build_combat(b,state,out)&&find(out,combatid(0,2))<0,"entity namespace collision omitted");
    reset(b);for(int id=2;id<20;++id)enemy(b,id,4+(id%3),1+(id%5),1|((id==18)?(1<<2):0));
    synthetic::props[0].kind=2;synthetic::props[0].targets=d::ability_target_enemies;synthetic::props[0].payload.damage={8,1};rebuild_self();
    check(nnp::build_combat(b,state,out)&&out.K==16,"combat narrowing bounded to sixteen including hold");
    check(find(out,combatid(1,18))>=0,"channeling target retained in geometric bucket");
    for(int i=1;i<out.K;++i)check(out.id[i-1]<out.id[i],"canonical ascending narrowed combat IDs");
    const auto first=out;std::reverse(b.w.enemies.begin(),b.w.enemies.end());
    check(nnp::build_combat(b,state,out)&&out.K==first.K,"permuted candidate build succeeds");
    check(std::memcmp(out.id,first.id,out.K*sizeof(out.id[0]))==0&&std::memcmp(out.feat,first.feat,out.K*12*sizeof(float))==0,
        "combat features and narrowing invariant to target iteration order");
    reset(b);enemy(b,2,4,3);state.engagement=-1;check(nnp::build_engage(b,state,out)&&out.K==3,"all engage verdicts available");
    state.intent=5;ack=nnp::execute_engage(b,state,1);check(ack.executed&&ack.changed&&state.engagement==1&&state.intent==5&&state.goal==vec2{0,0},"disengage commits and invalidates goal observation without replacing mode");
    ack=nnp::execute_engage(b,state,1);check(ack.executed&&!ack.changed,"unchanged disengage does not invalidate observation");
    check(nnp::build_move(b,state,out)&&out.context==2,"retreat move context");
    ack=nnp::execute_engage(b,state,0);check(ack.changed&&state.engagement==0&&state.goal==vec2{4,3},"fight invalidates and replaces retreat goal with visible target");
    check(nnp::build_move(b,state,out)&&out.context==1,"fight move context");
    ack=nnp::execute_engage(b,state,2);check(ack.changed&&state.engagement==2,"hold verdict committed and context invalidated");
    ack=nnp::execute_engage(b,state,2);check(ack.executed&&!ack.changed,"repeated hold leaves context unchanged");
    check(!nnp::execute_engage(b,state,3).executed,"invalid engage verdict rejected");
    synthetic::champion[1].health=0;check(!nnp::build_combat(b,state,out)&&out.K==0,"dead self refuses decision");
    std::printf("synthetic tactics: %d checks passed\n",synthetic::checks);return 0;
}
