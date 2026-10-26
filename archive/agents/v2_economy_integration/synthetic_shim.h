// Synthetic SDK host for the unchanged production economy implementation.
#pragma once
#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <queue>
#include <vector>
#include "nn_policy_candidates.h"
struct vec2 { int x,y; };
constexpr int kUnreach=65535;
inline int cheb(vec2 a,vec2 b) { return std::max(std::abs(a.x-b.x),std::abs(a.y-b.y)); }
namespace cambc {
enum class error_code { api_not_found=98,api_not_in_vision=97 };
namespace constants { inline int submit_gems_range=1,submit_gem_base_duration=0,submit_gem_minimum_duration=1; inline double submit_gem_duration_multiplier=.1; inline unsigned max_rounds=2000,winning_gems=1000; }
namespace detail {
struct metadata { int width=32,height=32; unsigned board_bytes=128,field_bytes=2048,chunked_width=4,chunked_height=4; };
struct champion_info { int team=0,type=0,x=2,y=2; float health=100,max_health=200; int state=1; };
struct stats { float health_growth=100,strength_growth=10,focus_growth=15; };
struct champion_design { stats base_stats; };
struct item_info { unsigned cost=0,purchasable=0; int health_points=0,strength_points=0,focus_points=0; unsigned combine_count=0,result=0; };
struct consumable_info { unsigned cost=10,carry_limit=1; };
struct altar_lock_info {};
inline metadata meta;inline champion_info me;inline unsigned gold=100,gems=20,score=100,counts[42]{},consumables[4]{};
inline unsigned last_item=999,last_consumable=999,last_cap=0;inline int can_items=1,can_consumables=1,lock=0,submit_error=0,buy_error=0,submit_calls=0,buy_calls=0,fields=0;inline std::uint8_t restrictions=0;
inline const metadata& layout() { return meta; }
inline int sdk_my_team() { return 0; }
inline int sdk_champion(unsigned,champion_info* out) { *out=me;return 0; }
inline int sdk_champion_gems(unsigned,unsigned* out) { *out=gems;return 0; }
inline int sdk_champion_gold(unsigned,unsigned* out) { *out=gold;return 0; }
inline int sdk_bc_submitted_gems(int,unsigned* out) { *out=score;return 0; }
inline int sdk_champion_restrictions(unsigned,std::uint8_t* out) { *out=restrictions;return 0; }
inline int sdk_champion_items(unsigned,unsigned* out) { std::copy_n(counts,42,out);return 0; }
inline int sdk_champion_consumables(unsigned,unsigned* out) { std::copy_n(consumables,4,out);return 0; }
inline int sdk_champion_can_shop(unsigned,int consumable,int* out) { *out=consumable?can_consumables:can_items;return 0; }
inline int sdk_champion_design(int,champion_design* out) { *out={};return 0; }
inline int sdk_item_info(unsigned id,item_info* out) {
    if(id>=42)return 1;
    *out={};out->cost=id%2?150:30;out->purchasable=id%2==0;
    const int points=id%2?((id/6==1)?6:5):1;
    switch((id%6)/2) { case 0:out->strength_points=points;break;case 1:out->focus_points=points;break;case 2:out->health_points=points;break; }
    if(id%2==0)out->combine_count=5,out->result=id+1;
    return 0;
}
inline int sdk_consumable_info(unsigned id,consumable_info* out) { if(id!=0&&id!=2)return 1;*out={};return 0; }
inline int sdk_altar_lock(int,int,int,altar_lock_info*) { return lock==1?0:lock==0?98:97; }
inline int sdk_submit_gems(int,int) { ++submit_calls;if(submit_error)return submit_error;me.state|=1<<7;return 0; }
inline int sdk_buy_item(unsigned id,unsigned count) { ++buy_calls;if(buy_error)return buy_error;assert(count==1);last_item=id;gold-=30;return 0; }
inline int sdk_buy_consumable(unsigned id) { ++buy_calls;if(buy_error)return buy_error;assert(id==0||id==2);last_consumable=id;gold-=10;++consumables[id];return 0; }
inline int sdk_Bitboard_Zero(std::uint64_t* p) { std::memset(p,0,meta.board_bytes);return 0; }
inline int sdk_Bitboard_Set(std::uint64_t* p,int x,int y,int value) { const int i=y*meta.width+x;if(value)p[i/64]|=1ull<<(i%64);else p[i/64]&=~(1ull<<(i%64));return 0; }
inline bool board_test(const std::uint64_t* p,int x,int y) { const int i=y*meta.width+x;return (p[i/64]>>(i%64))&1; }
inline int sdk_DistanceField_Get(const std::uint16_t* p,int x,int y,std::uint16_t* out) { *out=p[y*meta.width+x];return 0; }
inline int sdk_DistanceField_ComputeWithExpansionCount(const std::uint64_t* walls,const std::uint64_t* roots,std::uint64_t*,std::uint16_t* out,std::uint16_t cap,std::uint16_t* expanded) {
    ++fields;last_cap=cap;*expanded=0;std::fill_n(out,meta.width*meta.height,65535);std::queue<vec2> q;
    for(int y=0;y<meta.height;++y)for(int x=0;x<meta.width;++x)if(board_test(roots,x,y))out[y*meta.width+x]=0,q.push({x,y});
    while(!q.empty()) { const auto p=q.front();q.pop();*expanded=std::max(*expanded,out[p.y*meta.width+p.x]);if(out[p.y*meta.width+p.x]>=cap)continue;for(int dy=-1;dy<=1;++dy)for(int dx=-1;dx<=1;++dx) {
        const int x=p.x+dx,y=p.y+dy;if(x<0||y<0||x>=meta.width||y>=meta.height||board_test(walls,x,y)||out[y*meta.width+x]!=65535)continue;
        out[y*meta.width+x]=out[p.y*meta.width+p.x]+1;q.push({x,y});
    }}return 0;
}
}}
namespace bc=cambc;
struct Board { std::uint64_t data[16]{};const std::uint64_t* ptr()const { return data; } };
inline bool bit(const Board& b,vec2 p) { return bc::detail::board_test(b.data,p.x,p.y); }
struct EnemyRec { float hp=10,strength=20; unsigned state=1; vec2 pos; int range=1; };
struct World { int width=32,height=32;Board static_blocked,visible;std::vector<vec2> altars;std::vector<EnemyRec> enemies; };
struct Bot { World w;vec2 pos{2,2};unsigned my_id=1;int round=1,refreshed=0;bool refresh_error=false;void refresh_self(){++refreshed;if(refresh_error)throw 1;} };
namespace nnp {
struct OptionsState { int intent=0,role=0,objective=-1,altar=-1;vec2 goal{-1,-1}; };
struct Execution { bool legal=false,executed=false,changed=false; };
inline bool flip=false;
inline vec2 canonical(const Bot& b,vec2 p) { return {flip?b.w.width-1-p.x:p.x,p.y}; }
}
