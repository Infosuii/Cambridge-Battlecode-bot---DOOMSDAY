// Direct policy SDK tactics. Compiled away in the checked-in teacher configuration.
#include "nn_policy_config.h"
#if NN_POLICY_V2
#include "bot.h"
#include "nn_policy_options.h"
#include <algorithm>
#include <cmath>
#include <limits>

namespace {
namespace d = cambc::detail;
// Bounded local candidate radii, with an explicit builder failure for unsupported designs.
constexpr int kLocalRadius = 16,kFieldCap=150,kTargetLimit=512;
struct Boards {
    bc::bitboard blocked, reach, frontier, scratch, roots, visited;
    bc::distance_field goal_distance;
    bool goal_ready=false,goal_complete=false;
    vec2 goal_key{-1,-1};
    const std::uint16_t* active_distance=nullptr;
    bool active_complete=false;
};
constinit Boards* g_boards = nullptr;
Boards& boards() { if (!g_boards) g_boards = new Boards; return *g_boards; }
int octant(vec2 delta) {
    const int x = delta.x, y = delta.y;
    if (x == 0 && y == 0) return 0;
    const int ax = std::abs(x), ay = std::abs(y);
    // Compass wedges use the canonical team frame, with deterministic boundary ties.
    if (2 * ax < ay) return y > 0 ? 0 : 4;
    if (2 * ay < ax) return x > 0 ? 2 : 6;
    return y > 0 ? (x > 0 ? 1 : 7) : (x > 0 ? 3 : 5);
}
struct MovePick { vec2 q{}; unsigned kind = 0; std::uint32_t id = 0; int distance = 0, oct = 0; };
bool move_less(const MovePick& a, const MovePick& b) {
    return a.distance < b.distance || (a.distance == b.distance && a.id < b.id);
}
struct Target {
    enum Category { enemy, ally, self, camp } category = enemy;
    std::uint32_t handle = 0;
    vec2 q{};
    float hp = 0, max_hp = 1, strength = 0;
    int gems = 0, channel = 0;
    const bc::champion* champion = nullptr;
    const bc::camp* monster = nullptr;
    bool ambiguous=false;
};
constinit Target g_targets[kTargetLimit]{};
constinit int g_visible_camps[kTargetLimit]{},g_visible_count=0;
struct CombatPick { Target target{}; unsigned kind = 0; std::uint32_t id = 0; int oct = 0; };
bool combat_less(const CombatPick& a, const CombatPick& b) {
    if ((a.target.channel > 0) != (b.target.channel > 0)) return a.target.channel > 0;
    return a.id < b.id;
}
bool active_self(d::champion_info& out) {
    return d::sdk_champion(static_cast<std::uint32_t>(static_cast<bc::handle_champion_t>(bc::self())), &out) == 0 &&
        (out.state & 1u) && out.health > 0;
}
int channel(const bc::champion& unit) {
    const auto state=unit.state();
    if(!state.contains(bc::champion_state::recalling)&&!state.contains(bc::champion_state::submitting_gems)&&
       !state.contains(bc::champion_state::teleporting))return 0;
    std::int32_t rounds=0;
    return d::sdk_champion_channel_time(static_cast<std::uint32_t>(static_cast<bc::handle_champion_t>(unit)),&rounds)==0?rounds:0;
}
}

struct nn_policy_tactics_access {
    static int capacity(const Bot&,nncfg::H head) {
        if(head!=nncfg::H::move)return 16;
        d::champion_info me{};if(!active_self(me)||me.move_speed<0||me.move_speed>kLocalRadius)return 16;
        int n=1;
        if(me.state&(1u<<3))n+=(2*me.move_speed+1)*(2*me.move_speed+1)-1;
        for(const auto& ability:bc::self().abilities())if(ability.is_dash()&&ability.is_ready()) {
            const auto props=ability.get<bc::ability_dash>();
            if(!std::isfinite(props.range)||props.range<0||props.range>kLocalRadius)return 16;
            const int width=2*static_cast<int>(props.range)+1;n+=width*width-1;
        }
        return std::min(16,n);
    }
    static bool combat_has_choice(const Bot& b) {
        d::champion_info me{};if(!active_self(me))return false;
        float range=(me.state&(1u<<4))?static_cast<float>(me.attack_range):-1.0f;
        for(const auto& ability:bc::self().abilities())if(ability.info()&&ability.is_ready()&&!ability.is_dash()) {
            if(ability.is_heal()||ability.is_shield()||ability.is_attack_reset())return true;
            std::visit([&](const auto& props) {
                using A=std::decay_t<decltype(props)>;
                if constexpr(std::is_same_v<A,bc::ability_damage>||std::is_same_v<A,bc::ability_cc>||std::is_same_v<A,bc::ability_aoe_damage>)
                    range=std::max(range,props.range);
            },*ability.info());
        }
        if(range<0)return false;
        const auto p=live_position(me);
        for(const auto& e:b.w.enemies)if(e.hp>0&&visible(b,e.pos)&&cheb(p,e.pos)<=range)return true;
        for(const auto& c:b.w.camps)if(!c.dead&&c.hp>0&&visible(b,c.pos)&&cheb(p,c.pos)<=range)return true;
        return false;
    }
    static void prepare(const Bot& b,const nnp::OptionsState& s,std::uint64_t reserve) {
        const auto& l=d::layout();const auto chunks=std::uint64_t(l.chunked_width)*l.chunked_height;
        const auto cost=chunks*(kFieldCap+24)+(std::uint64_t(l.field_bytes)*2+std::uint64_t(l.board_bytes)*6)/16+6000;
        if(bc::fuel_remaining()>cost+reserve) {
            auto& x=boards();goal_field(b,s,b.pos,x);
        }
    }
    static std::uint64_t bound(const Bot& b,const nnp::OptionsState& state,nncfg::H head) {
        const auto& l=d::layout();
        if(l.width!=b.w.width||l.height!=b.w.height||!l.chunked_width||!l.chunked_height)
            return std::numeric_limits<std::uint64_t>::max();
        const auto entities=std::uint64_t(b.w.enemies.size()+b.w.allies.size()+b.w.camps.size()+1);
        if(entities>kTargetLimit)return std::numeric_limits<std::uint64_t>::max();
        const auto bodies=std::uint64_t(b.w.enemies.size()+b.w.allies.size());
        std::uint64_t visible_camps=0;
        for(std::size_t i=0;i<b.w.camps.size();++i)if(!b.w.camps[i].dead&&b.w.camps[i].hp>0&&visible(b,b.w.camps[i].pos))++visible_camps;
        if(head==nncfg::H::engage)return 8000+bodies*500+kFieldCap*180;
        if(head==nncfg::H::combat)return 25000+b.w.camps.size()*60+visible_camps*1600+bodies*2200;
        if(head!=nncfg::H::move)return std::numeric_limits<std::uint64_t>::max();
        // One live speed read and immutable ability descriptors bound enumeration before construction.
        d::champion_info me{};if(!active_self(me)||me.move_speed<0||me.move_speed>kLocalRadius)return UINT64_MAX;
        std::uint64_t endpoints=std::uint64_t(2*me.move_speed+1)*(2*me.move_speed+1);
        for(const auto& ability:bc::self().abilities())if(ability.is_dash()) {
            const auto props=ability.get<bc::ability_dash>();
            if(!std::isfinite(props.range)||props.range<0||props.range>kLocalRadius)return UINT64_MAX;
            const auto diameter=2*static_cast<int>(props.range)+1;endpoints+=diameter*diameter;
        }
        const auto goal=inside(b,state.goal)?state.goal:b.pos;
        const bool inherited=!b.w.bridges_on&&inside(b,goal)&&(bit(b.w.ally_spawn,goal)||
            (state.objective>=0&&state.objective<static_cast<int>(b.w.groups.size())&&b.w.has_field(state.objective)&&
             bit(b.w.groups[state.objective].tiles,goal)));
        const bool warm=inherited||(g_boards&&g_boards->goal_ready&&g_boards->goal_key==goal);
        const auto chunks=std::uint64_t(l.chunked_width)*l.chunked_height;
        return (warm?0:chunks*(kFieldCap+24)+(std::uint64_t(l.field_bytes)*2+std::uint64_t(l.board_bytes)*6)/16)+
            (g_boards?8000:22000)+b.w.camps.size()*60+visible_camps*1000+bodies*500+endpoints*100+
            std::min<std::uint64_t>(16,endpoints)*1700;
    }
    static bool inside(const Bot& b, vec2 q) { return q.x>=0&&q.y>=0&&q.x<b.w.width&&q.y<b.w.height; }
    static bool visible(const Bot& b, vec2 q) { return inside(b,q) && bit(b.w.visible,q); }
    static std::uint8_t context(const nnp::OptionsState& s) {
        return s.engagement == 1 ? 2 : s.engagement == 0 ? 1 : 0;
    }
    static vec2 live_position(const d::champion_info& me) { return {me.x,me.y}; }
    static void blocking(const Bot& b, vec2 p, Boards& x) {
        // static_blocked includes walls, holes, altars and the enemy spawn. unit_tiles includes reservations.
        x.blocked = b.w.static_blocked;
        x.blocked |= b.w.unit_tiles;
        clear_bit(x.blocked,p);
    }
    static bool goal_field(const Bot& b, const nnp::OptionsState& state, vec2 p, Boards& x) {
        vec2 goal = inside(b,state.goal) ? state.goal : p;
        // Finite values in capped inherited fields are exact for their declared target set.
        // Bridge shortcuts are not walking paths and must never populate these features.
        if(!b.w.bridges_on) {
            if(inside(b,goal)&&bit(b.w.ally_spawn,goal)) {
                x.active_distance=b.w.spawn_field.ptr();x.active_complete=true;return true;
            }
            const int gi=state.objective;
            if(gi>=0&&gi<static_cast<int>(b.w.groups.size())&&b.w.has_field(gi)&&
               bit(b.w.groups[gi].tiles,goal)) {
                x.active_distance=b.w.group_dist[static_cast<std::size_t>(b.w.field_slot[gi])].ptr();
                x.active_complete=false;return true;
            }
        }
        if(x.goal_ready&&x.goal_key==goal) {
            x.active_distance=x.goal_distance.ptr();x.active_complete=x.goal_complete;return true;
        }
        x.roots.clear();
        if (!bit(b.w.static_blocked,goal)) set_bit(x.roots,goal);
        else for (vec2 dir:kDirs) {
            const vec2 q = goal + dir;
            if (inside(b,q) && !bit(b.w.static_blocked,q)) set_bit(x.roots,q);
        }
        // A blocked objective denotes its adjacent reachable approach ring.
        const auto expansions=x.goal_distance.compute_with_expansion_count(b.w.static_blocked,x.roots,x.visited,kFieldCap);
        x.goal_key=goal;x.goal_ready=true;x.goal_complete=expansions<kFieldCap;
        x.active_distance=x.goal_distance.ptr();x.active_complete=x.goal_complete;
        return true;
    }
    static int path_distance(const Boards& x,vec2 q) {return x.active_distance[field_index(q)];}
    static void proximity(const Bot& b, vec2 q, int& attackers, int& camps, int& enemy_distance, int& ally_distance) {
        attackers=camps=0;enemy_distance=ally_distance=10000;
        for (const auto& e:b.w.enemies) if (e.hp>0 && visible(b,e.pos)) {
            const int distance=cheb(q,e.pos);enemy_distance=std::min(enemy_distance,distance);
            attackers += distance<=e.range;
        }
        for(int j=0;j<g_visible_count;++j) {
            const auto& c=b.w.camps[g_visible_camps[j]];
            camps += cheb(q,c.pos)<=c.range;
        }
        for (const auto& a:b.w.allies) if (a.hp>0 && visible(b,a.pos)) ally_distance=std::min(ally_distance,cheb(q,a.pos));
    }
    static nnpc::Candidate move_row(const Bot& b,const nnp::OptionsState& state,const MovePick& pick,vec2 p) {
        nnpc::Candidate row{};row.id=pick.id;row.legal=1;
        const vec2 a=nnp::canonical(b,p),q=nnp::canonical(b,pick.q);
        const vec2 goal=inside(b,state.goal)?state.goal:p;
        int attackers,camps,enemy_distance,ally_distance;
        proximity(b,pick.q,attackers,camps,enemy_distance,ally_distance);
        float cooldown=0;
        if (pick.kind==1||pick.kind==2) {
            const auto ability=bc::self().abilities()[pick.kind-1];
            const auto& info=ability.info();
            if (info) cooldown=std::visit([](const auto& props) {return static_cast<float>(props.max_cooldown);},*info);
        }
        row.raw[0]=static_cast<float>(q.x-a.x);row.raw[1]=static_cast<float>(q.y-a.y);
        row.raw[2]=static_cast<float>(pick.distance);row.raw[3]=static_cast<float>(cheb(pick.q,goal));
        row.raw[4]=static_cast<float>(attackers);row.raw[5]=static_cast<float>(camps);
        row.raw[6]=bit(b.w.bushes,pick.q);row.raw[7]=static_cast<float>(enemy_distance);
        row.raw[8]=static_cast<float>(ally_distance);row.raw[9]=static_cast<float>(pick.kind);
        row.raw[10]=cooldown;row.raw[11]=static_cast<float>(b.gems);return row;
    }
    static bool move(const Bot& b,const nnp::OptionsState& state,nnpc::Decision& out) {
        out.K=0;d::champion_info me{};if(!active_self(me))return false;
        const vec2 p=live_position(me);if(!inside(b,p))return false;
        g_visible_count=0;
        for(int i=0;i<static_cast<int>(b.w.camps.size());++i) {
            const auto& c=b.w.camps[i];
            if(!c.dead&&c.hp>0&&c.strength>0&&visible(b,c.pos)) {
                if(g_visible_count==kTargetLimit)return false;
                g_visible_camps[g_visible_count++]=i;
            }
        }
        auto& x=boards();blocking(b,p,x);goal_field(b,state,p,x);
        bool missing_distance=false;
        MovePick small[nnpc::kMaxK]{};int total=0;
        MovePick bucket[3][8]{};bool have[3][8]{};
        auto add=[&](vec2 q,unsigned kind) {
            MovePick pick{};pick.q=q;pick.kind=kind;const vec2 c=nnp::canonical(b,q);
            if (!nnpc::move_id(kind,c.x,c.y,pick.id))return;
            pick.oct=octant(c-nnp::canonical(b,p));pick.distance=path_distance(x,q);
            if(pick.distance==kUnreach&&!x.active_complete)missing_distance=true;
            if(total<nnpc::kMaxK)small[total]=pick;
            ++total;
            if(!have[kind][pick.oct] || move_less(pick,bucket[kind][pick.oct]))
                bucket[kind][pick.oct]=pick,have[kind][pick.oct]=true;
        };
        if(bc::self().can_move()) {
            if(me.move_speed<0||me.move_speed>kLocalRadius)return false;
            x.blocked.reachable_tiles_into(p,static_cast<std::uint16_t>(me.move_speed),x.frontier,x.scratch,x.reach);
            for(int dy=-me.move_speed;dy<=me.move_speed;++dy)for(int dx=-me.move_speed;dx<=me.move_speed;++dx) {
                const vec2 q{p.x+dx,p.y+dy};if(q!=p&&inside(b,q)&&bit(x.reach,q))add(q,0);
            }
        }
        const auto abilities=bc::self().abilities();
        for(int s=0;s<2;++s) {
            const auto& ability=abilities[s];
            if(!ability.is_dash()||!ability.is_ready())continue;
            const auto props=ability.get<bc::ability_dash>();
            if(!props.valid_targets.contains(bc::ability_target_mask::ground)||(props.exclusive_with_movement&&b.walked))continue;
            if(!std::isfinite(props.range)||props.range<0||props.range>kLocalRadius)return false;
            const int radius=static_cast<int>(props.range);
            // Conservative known-legal path subset: no hole-crossing or paths through occupied tiles.
            x.blocked.reachable_tiles_into(p,static_cast<std::uint16_t>(radius),x.frontier,x.scratch,x.reach);
            for(int dy=-radius;dy<=radius;++dy)for(int dx=-radius;dx<=radius;++dx) {
                const vec2 q{p.x+dx,p.y+dy};if(q!=p&&inside(b,q)&&bit(x.reach,q))add(q,static_cast<unsigned>(s+1));
            }
        }
        nnpc::Candidate rows[nnpc::kMaxK]{};int n=0;
        MovePick hold{};hold.q=p;hold.kind=3;hold.distance=path_distance(x,p);
        if(hold.distance==kUnreach&&!x.active_complete)missing_distance=true;
        // Schema requires all legal adjacent steps and hold. Capped unknown is not unreachable:
        // refuse the entire decision rather than silently prune or fabricate those feature rows.
        if(missing_distance)return false;
        const vec2 c=nnp::canonical(b,p);if(!nnpc::move_id(3,c.x,c.y,hold.id))return false;
        rows[n++]=move_row(b,state,hold,p);
        if(total<=nnpc::kMaxK-1)for(int i=0;i<total;++i)rows[n++]=move_row(b,state,small[i],p);
        else for(int oct=0;oct<8&&n<nnpc::kMaxK;++oct)for(int kind=0;kind<3&&n<nnpc::kMaxK;++kind)
            if(have[kind][oct])rows[n++]=move_row(b,state,bucket[kind][oct],p);
        return nnpc::build(nncfg::H::move,rows,n,context(state),out)==nnpc::Error::ok;
    }
    template<class Fn>static bool targets(const Bot& b,const d::champion_info& me,Fn emit,std::uint32_t wanted=0xffffffffu) {
        // Gather once, then sort public handles. Collision detection is O(N log N), not a
        // full world rescan for every target. No hidden entity is queried or ranked.
        int n=0;bool overflow=false;
        auto add=[&](const Target& t){if(n==kTargetLimit){overflow=true;return;}g_targets[n++]=t;};
        for(const auto& e:b.w.enemies)if((wanted==0xffffffffu||wanted==e.id)&&e.hp>0&&visible(b,e.pos)) {
            d::champion_info live{};if(d::sdk_champion(e.id,&live)!=0||!(live.state&1u)||live.health<=0)continue;
            Target t{};t.category=Target::enemy;t.handle=e.id;t.q={live.x,live.y};t.hp=live.health;
            t.max_hp=live.max_health;t.strength=live.strength;t.gems=e.gems;t.champion=&e.unit;
            if(live.state&((1u<<1)|(1u<<2)|(1u<<12)))t.channel=channel(e.unit);add(t);
        }
        for(const auto& a:b.w.allies)if((wanted==0xffffffffu||wanted==a.id)&&a.hp>0&&visible(b,a.pos)) {
            d::champion_info live{};if(d::sdk_champion(a.id,&live)!=0||!(live.state&1u)||live.health<=0)continue;
            Target t{};t.category=Target::ally;t.handle=a.id;t.q={live.x,live.y};t.hp=live.health;
            t.max_hp=live.max_health;t.strength=live.strength;t.champion=&a.unit;
            if(live.state&((1u<<1)|(1u<<2)|(1u<<12)))t.channel=channel(a.unit);
            std::uint32_t gems=0;if(d::sdk_champion_gems(a.id,&gems)!=0)continue;t.gems=static_cast<int>(gems);add(t);
        }
        Target self{};self.category=Target::self;self.handle=b.my_id;self.q=live_position(me);self.hp=me.health;
        self.max_hp=me.max_health;self.strength=me.strength;self.gems=b.gems;self.champion=&bc::self();
        if(wanted==0xffffffffu||wanted==b.my_id)add(self);
        for(const auto& c:b.w.camps)if((wanted==0xffffffffu||wanted==static_cast<std::uint32_t>(static_cast<bc::handle_camp_t>(c.camp)))&&
                                                       !c.dead&&c.hp>0&&visible(b,c.pos)&&c.camp.is_visible()) {
            Target t{};t.category=Target::camp;t.handle=static_cast<std::uint32_t>(static_cast<bc::handle_camp_t>(c.camp));
            t.hp=c.camp.health();if(t.hp<=0)continue;
            t.q=c.pos;t.max_hp=c.max_hp;t.strength=c.strength;t.monster=&c.camp;add(t);
        }
        if(overflow)return false;
        std::sort(g_targets,g_targets+n,[](const Target& a,const Target& b){return a.handle<b.handle;});
        for(int i=0;i<n;++i)if(!(i&&g_targets[i-1].handle==g_targets[i].handle)&&
                               !(i+1<n&&g_targets[i+1].handle==g_targets[i].handle))emit(g_targets[i]);
        return true;
    }
    static bool combat_legal(const Bot& b,const d::champion_info& me,const Target& t,unsigned kind,bool readiness_checked=false) {
        const vec2 p=live_position(me);const bool hostile=t.category==Target::enemy||t.category==Target::camp;
        if(kind==0)return hostile&&(readiness_checked||bc::self().can_attack())&&cheb(p,t.q)<=me.attack_range;
        if(kind>2)return false;
        const auto ability=bc::self().abilities()[kind-1];
        if(!ability.info()||(!readiness_checked&&!ability.is_ready()))return false;
        return std::visit([&](const auto& props) {
            using A=std::decay_t<decltype(props)>;
            if(props.exclusive_with_movement&&b.walked)return false;
            const bool permits=props.valid_targets.contains(t.category==Target::enemy?bc::ability_target_mask::enemies:
                t.category==Target::camp?bc::ability_target_mask::camps:t.category==Target::self?bc::ability_target_mask::self:bc::ability_target_mask::allies);
            if constexpr(std::is_same_v<A,bc::ability_dash>)return false; // Endpoints belong to the movement head.
            else if constexpr(std::is_same_v<A,bc::ability_attack_reset>)return t.category==Target::self&&permits;
            else if constexpr(std::is_same_v<A,bc::ability_shield>)return t.category==Target::self&&permits;
            else if constexpr(std::is_same_v<A,bc::ability_heal>)return !hostile&&permits&&cheb(p,t.q)<=props.range;
            else return hostile&&permits&&cheb(p,t.q)<=props.range;
        },*ability.info());
    }
    static nnpc::Candidate combat_row(const Bot& b,const d::champion_info& me,const CombatPick& pick) {
        nnpc::Candidate row{};row.id=pick.id;row.legal=1;const auto& t=pick.target;
        row.raw[0]=static_cast<float>(pick.kind);row.raw[1]=t.hp;row.raw[2]=t.max_hp;
        row.raw[3]=static_cast<float>(t.gems);row.raw[4]=static_cast<float>(cheb(live_position(me),t.q));
        row.raw[5]=me.health/std::max(1.0f,me.max_health);row.raw[6]=me.strength;row.raw[7]=t.strength;
        if(pick.kind==0)row.raw[8]=me.strength*(t.category==Target::camp?b.camp_dealt_mult:1.0f);
        else {
            const auto ability=bc::self().abilities()[pick.kind-1];
            row.raw[9]=std::visit([](const auto& props){return static_cast<float>(props.max_cooldown);},*ability.info());
            if(ability.is_damage()||ability.is_cc()||ability.is_aoe_damage())
                row.raw[8]=t.champion?ability.damage_amount(*t.champion):ability.damage_amount()*b.camp_dealt_mult;
        }
        row.raw[10]=static_cast<float>(t.channel);
        if(pick.kind>0&&bc::self().abilities()[pick.kind-1].is_aoe_damage()) {
            const auto props=bc::self().abilities()[pick.kind-1].get<bc::ability_aoe_damage>();
            for(const auto& e:b.w.enemies)if(e.hp>0&&visible(b,e.pos)&&cheb(t.q,e.pos)<=props.radius)row.raw[11]+=1;
        } else row.raw[11]=t.category==Target::enemy?1.0f:0.0f;
        return row;
    }
    static bool combat(const Bot& b,const nnp::OptionsState& state,nnpc::Decision& out) {
        out.K=0;d::champion_info me{};if(!active_self(me))return false;
        static constinit CombatPick bucket[3][8][nnpc::kMaxK];int count[3][8]{};
        const vec2 origin=nnp::canonical(b,live_position(me));
        unsigned ready=bc::self().can_attack()?1u:0u;
        const auto abilities=bc::self().abilities();
        for(int i=0;i<2;++i)if(abilities[i].info()&&abilities[i].is_ready())ready|=2u<<i;
        if(ready&&!targets(b,me,[&](const Target& target) {
            for(unsigned kind=0;kind<3;++kind)if((ready&(1u<<kind))&&combat_legal(b,me,target,kind,true)) {
                CombatPick pick{};pick.target=target;pick.kind=kind;
                if(!nnpc::combat_id(kind,target.handle,pick.id))continue;
                pick.oct=octant(nnp::canonical(b,target.q)-origin);
                auto* list=bucket[kind][pick.oct];int& n=count[kind][pick.oct];int at=0;
                while(at<n&&!combat_less(pick,list[at]))++at;
                if(at>=nnpc::kMaxK)continue;
                for(int i=std::min(n,nnpc::kMaxK-1);i>at;--i)list[i]=list[i-1];
                list[at]=pick;n=std::min(n+1,nnpc::kMaxK);
            }
        }))return false;
        nnpc::Candidate rows[nnpc::kMaxK]{};int n=1;rows[0].id=3;rows[0].legal=1;rows[0].raw[0]=3;
        rows[0].raw[5]=me.health/std::max(1.0f,me.max_health);rows[0].raw[6]=me.strength;
        for(int depth=0;depth<nnpc::kMaxK&&n<nnpc::kMaxK;++depth)
            for(int oct=0;oct<8&&n<nnpc::kMaxK;++oct)for(int kind=0;kind<3&&n<nnpc::kMaxK;++kind)
                if(depth<count[kind][oct])rows[n++]=combat_row(b,me,bucket[kind][oct][depth]);
        return nnpc::build(nncfg::H::combat,rows,n,context(state),out)==nnpc::Error::ok;
    }
    static vec2 retreat_goal(const Bot& b,vec2 p) {
        // Trace an already exact static walking field; never issue a new cold full-map SDK search.
        // Long/unavailable bridge-based paths are explicit executor refusals, not guessed destinations.
        if(b.w.bridges_on)return {-1,-1};
        int distance=fdist(b.w.spawn_field,p);
        if(distance==kUnreach||distance>kFieldCap)return {-1,-1};
        while(distance>0) {
            vec2 best{-1,-1};std::uint32_t best_id=0;
            for(vec2 dir:kDirs) {
                const vec2 q=p+dir;
                if(!inside(b,q)||bit(b.w.static_blocked,q)||fdist(b.w.spawn_field,q)!=distance-1)continue;
                const vec2 c=nnp::canonical(b,q);std::uint32_t id=0;
                if(!nnpc::move_id(0,c.x,c.y,id))continue;
                if(best.x<0||id<best_id)best=q,best_id=id;
            }
            if(best.x<0)return {-1,-1};
            p=best;--distance;
        }
        return bit(b.w.ally_spawn,p)?p:vec2{-1,-1};
    }
    static bool engage(const Bot& b,const nnp::OptionsState& state,nnpc::Decision& out) {
        out.K=0;d::champion_info me{};if(!active_self(me))return false;
        const vec2 p=live_position(me);float ally_hp=me.health,enemy_hp=0,ally_damage=me.strength,enemy_damage=0,incoming=0;
        const EnemyRec* nearest=nullptr;int nearest_distance=10000;
        for(const auto& a:b.w.allies)if(a.hp>0&&visible(b,a.pos))ally_hp+=a.hp,ally_damage+=a.strength;
        for(const auto& e:b.w.enemies)if(e.hp>0&&visible(b,e.pos)) {
            enemy_hp+=e.hp;enemy_damage+=e.strength;const int distance=cheb(p,e.pos);
            if(distance<nearest_distance||(distance==nearest_distance&&(!nearest||e.id<nearest->id)))nearest=&e,nearest_distance=distance;
            if(distance<=e.range)incoming+=e.strength;
        }
        int ready=0;
        for(const auto& a:bc::self().abilities())if(a.info()&&a.is_ready()) {
            const bool exclusive=std::visit([](const auto& props){return props.exclusive_with_movement;},*a.info());
            ready+=!exclusive||!b.walked;
        }
        // The inherited field is exact walking geometry only without heuristic bridge shortcuts.
        if(b.w.bridges_on)return false;
        const int escape=fdist(b.w.spawn_field,p);
        nnpc::Candidate rows[3]{};
        for(int verdict=0;verdict<3;++verdict) {
            auto& row=rows[verdict];row.id=static_cast<std::uint32_t>(verdict);row.legal=1;
            row.raw[0]=static_cast<float>(verdict);row.raw[1]=me.health/std::max(1.0f,me.max_health);
            row.raw[2]=nearest?nearest->hp/std::max(1.0f,nearest->max_hp):0;
            row.raw[3]=ally_hp;row.raw[4]=enemy_hp;row.raw[5]=ally_damage;row.raw[6]=enemy_damage;
            row.raw[7]=static_cast<float>(nearest_distance);row.raw[8]=static_cast<float>(escape);
            row.raw[9]=static_cast<float>(b.gems);row.raw[10]=static_cast<float>(ready);row.raw[11]=incoming;
        }
        return nnpc::build(nncfg::H::engage,rows,3,context(state),out)==nnpc::Error::ok;
    }
    static nnp::Execution execute_move(Bot& b,nnp::OptionsState&,std::uint32_t id) {
        nnp::Execution result{};d::champion_info me{};if(!active_self(me))return result;
        const unsigned kind=id>>30;const vec2 canonical{static_cast<int>(id&0x7fffu),static_cast<int>((id>>15)&0x7fffu)};
        const vec2 q=nnp::canonical(b,canonical),p=live_position(me);
        if(!inside(b,q))return result;
        if(kind==3) {result.legal=q==p;result.executed=result.legal;return result;}
        if(q==p)return result;
        auto& x=boards();blocking(b,p,x);if(bit(x.blocked,q))return result;
        if(kind==0) {
            if(!bc::self().can_move()||me.move_speed<0||me.move_speed>kLocalRadius)return result;
            x.blocked.reachable_tiles_into(p,static_cast<std::uint16_t>(me.move_speed),x.frontier,x.scratch,x.reach);
            if(!bit(x.reach,q))return result;
            result.legal=true;result.executed=bc::self().move_absolute(q);
            if(result.executed)b.pos=q,b.walked=true,result.changed=true;
        } else if(kind<=2) {
            const auto ability=bc::self().abilities()[kind-1];
            if(!ability.is_dash()||!ability.is_ready())return result;
            const auto props=ability.get<bc::ability_dash>();
            if(!props.valid_targets.contains(bc::ability_target_mask::ground)||(props.exclusive_with_movement&&b.walked)||
                !std::isfinite(props.range)||props.range<0||props.range>kLocalRadius)return result;
            x.blocked.reachable_tiles_into(p,static_cast<std::uint16_t>(props.range),x.frontier,x.scratch,x.reach);
            if(!bit(x.reach,q))return result;
            result.legal=true;result.executed=ability.use(q);
            if(result.executed)b.pos=q,b.cast_done=true,result.changed=true;
        }
        return result;
    }
    static nnp::Execution execute_combat(Bot& b,nnp::OptionsState&,std::uint32_t id) {
        nnp::Execution result{};d::champion_info me{};if(!active_self(me))return result;
        if(id==3){result.legal=result.executed=true;return result;}
        const unsigned kind=id&3u;if(kind==3)return result;const std::uint32_t handle=id>>2;
        Target selected{};bool found=false;
        // Resolve and recheck before issuing an action. Enumeration must never continue querying a
        // unit after an SDK attack killed it, or turn a completed action into an apparent refusal.
        if(!targets(b,me,[&](const Target& target) {
            if(target.handle==handle)selected=target,found=true;
        },handle))return result;
        if(!found||!combat_legal(b,me,selected,kind))return result;
        result.legal=true;
        if(kind==0) {
            if(selected.champion)bc::self().attack(*selected.champion);else bc::self().attack(*selected.monster);
            result.executed=result.changed=true;
        } else {
            const auto ability=bc::self().abilities()[kind-1];
            if(ability.is_shield()||ability.is_attack_reset())result.executed=ability.use();
            else if(ability.is_aoe_damage()&&ability.can_target_ground())result.executed=ability.use(selected.q);
            else if(selected.champion)result.executed=ability.use(*selected.champion);
            else result.executed=ability.use(*selected.monster);
            if(result.executed)b.cast_done=true,result.changed=true;
        }
        return result;
    }
    static nnp::Execution execute_engage(Bot& b,nnp::OptionsState& state,std::uint32_t id) {
        nnp::Execution result{};d::champion_info me{};if(id>2||!active_self(me))return result;
        const int previous=state.engagement;
        const vec2 previous_goal=state.goal;
        state.engagement=static_cast<int>(id);
        if(id==1) {
            const vec2 destination=retreat_goal(b,live_position(me));
            if(!inside(b,destination)){state.engagement=previous;return result;}
            state.goal=destination;
        }
        else if(id==0) {
            // Preserve a committed objective. A missing goal gets the nearest visible enemy, with handle ties.
            if(!inside(b,state.goal)||previous==1) {
                const EnemyRec* target=nullptr;int distance=std::numeric_limits<int>::max();
                for(const auto& e:b.w.enemies)if(e.hp>0&&visible(b,e.pos)) {
                    const int current=cheb(live_position(me),e.pos);
                    if(current<distance||(current==distance&&(!target||e.id<target->id)))target=&e,distance=current;
                }
                if(target)state.goal=target->pos;
            }
        }
        result.legal=result.executed=true;
        // Goal and engagement changes affect the next head's input even without a physical SDK action.
        result.changed=previous!=state.engagement||previous_goal!=state.goal;
        return result;
    }
};

namespace nnp {
bool combat_has_choice(const Bot& b) {return nn_policy_tactics_access::combat_has_choice(b);}
int tactics_candidate_capacity(const Bot& b,nncfg::H h) {return nn_policy_tactics_access::capacity(b,h);}
void prepare_tactics(const Bot& b,const OptionsState& s,std::uint64_t reserve) {
    nn_policy_tactics_access::prepare(b,s,reserve);
}
std::uint64_t tactics_candidate_bound(const Bot& b,const OptionsState& s,nncfg::H h) {
    return nn_policy_tactics_access::bound(b,s,h);
}
bool build_move(const Bot& b,const OptionsState& s,nnpc::Decision& out) {
    try{return nn_policy_tactics_access::move(b,s,out);}catch(...){out.K=0;return false;}
}
bool build_combat(const Bot& b,const OptionsState& s,nnpc::Decision& out) {
    try{return nn_policy_tactics_access::combat(b,s,out);}catch(...){out.K=0;return false;}
}
bool build_engage(const Bot& b,const OptionsState& s,nnpc::Decision& out) {
    try{return nn_policy_tactics_access::engage(b,s,out);}catch(...){out.K=0;return false;}
}
Execution execute_move(Bot& b,OptionsState& s,std::uint32_t id) {
    try{return nn_policy_tactics_access::execute_move(b,s,id);}catch(...){return {};}
}
Execution execute_combat(Bot& b,OptionsState& s,std::uint32_t id) {
    try{return nn_policy_tactics_access::execute_combat(b,s,id);}catch(...){return {};}
}
Execution execute_engage(Bot& b,OptionsState& s,std::uint32_t id) {
    try{return nn_policy_tactics_access::execute_engage(b,s,id);}catch(...){return {};}
}
}
#endif
