// Compact policy-v2 legal observation glue. No legacy RawTurn/capture, teacher scoring, fields or fog queries.
#include "nn_policy_config.h"
#if NN_POLICY_V2
#include "bot.h"
#include "nn_policy_observation.h"
#include "nn_policy_state.h"

namespace {
namespace d=cambc::detail;
struct Frame { bool ready=false,fx=false,fy=false; int w=0,h=0,team=0,spawn_x=0,spawn_y=0; };
constinit Frame g_frame{};
inline bool inside(vec2 q,int w,int h) { return q.x>=0&&q.y>=0&&q.x<w&&q.y<h; }
inline int dx(int x) { return g_frame.fx?-x:x; }
inline int dy(int y) { return g_frame.fy?-y:y; }
inline vec2 canonical(vec2 q) { return {g_frame.fx?g_frame.w-1-q.x:q.x,g_frame.fy?g_frame.h-1-q.y:q.y}; }
template<class Rec,int Max>
void insert_nearest(const Rec& r,const Rec* (&out)[Max],int& n,vec2 self) {
    for(int i=0;i<n;++i)if(out[i]->id==r.id)return;
    const int distance=cheb(r.pos,self);int at=0;
    while(at<n) {
        const int previous=cheb(out[at]->pos,self);
        if(distance<previous||(distance==previous&&r.id<out[at]->id))break;
        ++at;
    }
    if(at>=Max)return;
    const int last=n<Max?n:Max-1;
    for(int i=last;i>at;--i)out[i]=out[i-1];
    out[at]=&r;if(n<Max)++n;
}
}

struct nn_policy_observation_access {
    static bool frame(const Bot& b) {
        if(g_frame.ready)return g_frame.w==b.w.width&&g_frame.h==b.w.height;
        if(b.w.width<=0||b.w.height<=0)return false;
        const int team=d::sdk_my_team();if(team<0||team>1)return false;
        d::aabb box{};if(d::sdk_spawn_region(team,&box)!=0)return false;
        const int s2x=box.min_x+box.max_x-1,s2y=box.min_y+box.max_y-1;
        const int w=b.w.width,h=b.w.height,sym=static_cast<int>(bc::map::symmetry());
        // Exact canonical frame rule shared with legacy pure transforms; no legacy observation dependency.
        const bool flip=sym==0 ? (s2x!=w-1?s2x>w-1:team==1) :
                        sym==1 ? (s2y!=h-1?s2y>h-1:team==1) :
                        sym==2 ? (s2x!=w-1?s2x>w-1:(s2y!=h-1?s2y>h-1:team==1)) : false;
        g_frame={true,flip&&(sym==0||sym==2),flip&&(sym==1||sym==2),w,h,team,s2x/2,s2y/2};
        return true;
    }
    static int claim(const Bot& b,std::uint32_t handle) {
        const int n=std::min(b.team_size,kClaimSlots);
        for(int s=0;s<n;++s)if(b.ally_handle[s]==handle)
            return static_cast<int>((b.shared>>(s*kClaimBits))&kClaimMask);
        return static_cast<int>(kClaimCodeIdle); // absent mapping, not a fabricated group0 claim
    }
    static bool capture(const Bot& b,float* out) {
        if(!out||!b.inited||!frame(b))return false;
        d::champion_info me{};
        if(d::sdk_champion(b.my_id,&me)!=0)return false;
        const bool alive=(static_cast<std::uint32_t>(me.state)&1u)!=0;
        const vec2 pos=alive?vec2{me.x,me.y}:vec2{g_frame.spawn_x,g_frame.spawn_y};
        if(!inside(pos,b.w.width,b.w.height))return false;
        std::uint32_t gems=0,gold=0,ours=0,theirs=0;
        if(d::sdk_champion_gems(b.my_id,&gems)!=0||d::sdk_champion_gold(b.my_id,&gold)!=0||
           d::sdk_bc_submitted_gems(g_frame.team,&ours)!=0||d::sdk_bc_submitted_gems(1-g_frame.team,&theirs)!=0)return false;
        nnpobs::Raw r{};
        const float max_hp=std::max(1.0f,me.max_health);
        const int role=nnp::observation_role();if(role<0||role>4)return false;
        vec2 goal=nnp::observation_goal();if(!inside(goal,b.w.width,b.w.height))goal=pos;
        r.self[0]=alive?me.health/max_hp:0;r.self[1]=alive?me.health:0;r.self[2]=me.max_health;
        r.self[3]=static_cast<float>(gems);r.self[4]=static_cast<float>(gold);
        r.self[5]=me.strength;r.self[6]=me.focus;r.self[7]=static_cast<float>(me.attack_range);
        r.self[8]=static_cast<float>(b.round);r.self[9]=static_cast<float>(std::max(0,static_cast<int>(bc::constants::max_rounds)-b.round));
        r.self[10]=static_cast<float>(ours);r.self[11]=static_cast<float>(theirs);r.self[12]=static_cast<float>(role);
        r.self[13]=static_cast<float>(dx(goal.x-pos.x));r.self[14]=static_cast<float>(dy(goal.y-pos.y));
        const int home=fdist(b.w.spawn_field,pos);r.self[15]=home==kUnreach?10000.0f:static_cast<float>(home);
        for(int s=0;s<2;++s) {
            r.self[18+s]=b.spells[s].present;
            r.self[34+s]=b.spells[s].present?static_cast<float>(b.spells[s].kind):0.0f;
            if(b.spells[s].present) {
                std::int32_t cooldown=0;if(d::sdk_champion_cooldown(b.my_id,s,&cooldown)!=0)return false;
                r.self[16+s]=static_cast<float>(cooldown);
            }
        }
        r.self[20]=alive;r.self[21]=alive&&(me.state&(1u<<3));r.self[22]=alive&&(me.state&(1u<<4));r.self[23]=alive&&(me.state&(1u<<11));
        r.self[26]=10000.0f;
        // World sightings are this champion's legal memory, including sightings explicitly shared by its own team.
        const Sighting* newest=nullptr;vec2 newest_c{};
        for(const auto& sight:b.w.sightings) {
            if(sight.round>b.round||!inside(sight.pos,b.w.width,b.w.height))continue;
            const vec2 c=canonical(sight.pos);
            if(!newest||sight.round>newest->round||(sight.round==newest->round&&(c.x<newest_c.x||(c.x==newest_c.x&&c.y<newest_c.y))))
                newest=&sight,newest_c=c;
        }
        if(newest) {
            r.self[24]=static_cast<float>(dx(newest->pos.x-pos.x));r.self[25]=static_cast<float>(dy(newest->pos.y-pos.y));
            r.self[26]=static_cast<float>(b.round-newest->round);
        }
        r.self[27]=alive&&bit(b.w.bushes,pos);r.self[28]=bit(b.w.ally_spawn,pos);
        r.self[31]=static_cast<float>(b.w.width);r.self[32]=static_cast<float>(b.w.height);r.self[33]=static_cast<float>(me.type);
        r.self[36]=alive&&bit(b.w.hot_zone,pos);
        if(alive) {
            d::ward_resources wards{};if(d::sdk_champion_wards(b.my_id,&wards)!=0)return false;
            r.self[37]=static_cast<float>(wards.charges);r.self[38]=static_cast<float>(wards.cooldown);
        }
        // reserved self[39] and all padded entity fields/masks remain exactlyzero.
        const AllyRec* allies[nnpobs::kAllyRows]{};const EnemyRec* enemies[nnpobs::kEnemyRows]{};int na=0,ne=0;
        if(alive) {
            for(const auto& a:b.w.allies) {
                if(a.id==b.my_id||a.hp<=0||!inside(a.pos,b.w.width,b.w.height)||!bit(b.w.visible,a.pos))continue;
                r.self[29]+=cheb(a.pos,pos)<=8;insert_nearest(a,allies,na,pos);
            }
            for(const auto& e:b.w.enemies) {
                if(e.id==b.my_id||e.hp<=0||!(e.state&1u)||!inside(e.pos,b.w.width,b.w.height)||!bit(b.w.visible,e.pos))continue;
                r.self[30]+=cheb(e.pos,pos)<=8;insert_nearest(e,enemies,ne,pos);
            }
        }
        for(int i=0;i<na;++i) {
            const auto& a=*allies[i];auto* f=r.ally[i];std::uint32_t carried=0;
            // Only an already-visible ally is queried. No roster/private enemy state is read.
            if(d::sdk_champion_gems(a.id,&carried)!=0)return false;
            f[0]=static_cast<float>(dx(a.pos.x-pos.x));f[1]=static_cast<float>(dy(a.pos.y-pos.y));
            f[2]=a.hp/std::max(1.0f,a.max_hp);f[3]=a.hp;f[4]=a.strength;f[5]=a.focus;
            f[6]=static_cast<float>(a.range);f[7]=static_cast<float>(a.type);f[8]=static_cast<float>(carried);f[9]=static_cast<float>(claim(b,a.id));
            r.ally_mask[i]=1;
        }
        for(int i=0;i<ne;++i) {
            const auto& e=*enemies[i];auto* f=r.enemy[i];
            f[0]=static_cast<float>(dx(e.pos.x-pos.x));f[1]=static_cast<float>(dy(e.pos.y-pos.y));
            f[2]=e.hp/std::max(1.0f,e.max_hp);f[3]=e.hp;f[4]=e.strength;f[5]=e.focus;
            f[6]=static_cast<float>(e.range);f[7]=static_cast<float>(e.type);f[8]=static_cast<float>(e.gems);
            f[9]=e.recalling();f[10]=e.tributing();f[11]=static_cast<float>(cheb(e.pos,pos));r.enemy_mask[i]=1;
        }
        return nnpobs::encode(r,out);
    }
};

namespace nnpobs { bool capture(const Bot& b,float* out) { return nn_policy_observation_access::capture(b,out); } }
#endif // NN_POLICY_V2
