// Direct policy economy. Candidate geometry/metadata and explicit SDK actions only.
#include "nn_policy_config.h"
#if NN_POLICY_V2
#include "bot.h"
#include "nn_policy_options.h"
#include <cmath>
#include <cstring>
#include <limits>

namespace {
namespace d=cambc::detail;
constexpr int kBankK=16,kShopK=16,kItems=42,kFamilies=7;
constexpr std::uint16_t kBankExpansionCap=64;
// The host layout is chunked, not width*height. Reject oversized layouts before host writes.
// 128KiB distance storage plus three 8KiB boards, allocated in static data without constructors.
struct BankScratch {
    bool ready=false;
    std::uint32_t owner=0;
    int round=-1,width=0,height=0,x=-1,y=-1;
    std::uint16_t expansions=0;
    std::uint64_t walls[1024],roots[1024],visited[1024];
    std::uint16_t distance[65536];
};
constinit BankScratch g_bank{};
struct Altar { std::uint32_t index=0; int distance=kUnreach,quadrant=0; vec2 goal{-1,-1}; };
bool inside(vec2 p,int width,int height) { return p.x>=0&&p.y>=0&&p.x<width&&p.y<height; }
bool equal(vec2 a,vec2 b) { return a.x==b.x&&a.y==b.y; }
bool cached_field(const World& w,vec2 pos,std::uint32_t owner,int round) {
    return g_bank.ready&&g_bank.owner==owner&&g_bank.round==round&&g_bank.width==w.width&&g_bank.height==w.height&&g_bank.x==pos.x&&g_bank.y==pos.y;
}
bool alive(const d::champion_info& me) { return (me.state&1u)!=0&&me.health>0; }
bool channel_free(const d::champion_info& me) { return alive(me)&&(me.state&((1u<<1)|(1u<<2)|(1u<<5)|(1u<<6)|(1u<<7)|(1u<<12)))==0; }
float remaining(int round) { return static_cast<float>(std::max(0,static_cast<int>(bc::constants::max_rounds)-round)); }
int channel_rounds(std::uint32_t gems) {
    const double duration=bc::constants::submit_gem_base_duration+std::ceil(gems*bc::constants::submit_gem_duration_multiplier);
    return static_cast<int>(std::max<double>(bc::constants::submit_gem_minimum_duration,std::min(duration,1000000.0)));
}
bool make_field(const World& w,vec2 pos,std::uint32_t owner,int round) {
    const auto& layout=d::layout();
    if(layout.width!=w.width||layout.height!=w.height||!inside(pos,w.width,w.height)||
       layout.board_bytes==0||layout.board_bytes>sizeof(g_bank.walls)||
       layout.field_bytes==0||layout.field_bytes>sizeof(g_bank.distance))return false;
    if(cached_field(w,pos,owner,round))return true;
    g_bank.ready=false;
    std::memcpy(g_bank.walls,w.static_blocked.ptr(),layout.board_bytes);
    // Actual walking terrain: holes remain blocked even for champions with mobility abilities.
    // Camps/champions are temporary occupancy; the movement executor rechecks those each step.
    if(d::sdk_Bitboard_Set(g_bank.walls,pos.x,pos.y,0)!=0||d::sdk_Bitboard_Zero(g_bank.roots)!=0||
       d::sdk_Bitboard_Set(g_bank.roots,pos.x,pos.y,1)!=0)return false;
    std::uint16_t expansions=0;
    if(d::sdk_DistanceField_ComputeWithExpansionCount(g_bank.walls,g_bank.roots,g_bank.visited,g_bank.distance,kBankExpansionCap,&expansions)!=0)return false;
    g_bank.expansions=expansions;
    g_bank.ready=true;g_bank.owner=owner;g_bank.round=round;g_bank.width=w.width;g_bank.height=w.height;g_bank.x=pos.x;g_bank.y=pos.y;
    return true;
}
bool altar_distance(const World& w,vec2 self,vec2 altar,Altar& result,const Bot& b) {
    const int radius=bc::constants::submit_gems_range;
    if(radius<0||radius>16)return false;
    for(int y=std::max(0,altar.y-radius);y<=std::min(w.height-1,altar.y+radius);++y)
        for(int x=std::max(0,altar.x-radius);x<=std::min(w.width-1,altar.x+radius);++x) {
            std::uint16_t distance=kUnreach;
            if(d::sdk_DistanceField_Get(g_bank.distance,x,y,&distance)!=0)return false;
            if(distance==kUnreach)continue;
            const vec2 tile{x,y},c=nnp::canonical(b,tile),previous=nnp::canonical(b,result.goal);
            if(distance<result.distance||(distance==result.distance&&(c.y<previous.y||(c.y==previous.y&&c.x<previous.x))))
                result.distance=distance,result.goal=tile;
        }
    const vec2 a=nnp::canonical(b,altar),p=nnp::canonical(b,self);
    result.quadrant=(a.x>=p.x?1:0)|(a.y>=p.y?2:0);
    return true;
}
// -1 means hidden/unavailable. Visible absence is 0; only an observed enemy lock is 1.
bool lock_state(vec2 altar,int team,float& state) {
    d::altar_lock_info lock{};
    const int code=d::sdk_altar_lock(altar.x,altar.y,1-team,&lock);
    if(code==0) { state=1;return true; }
    if(code==static_cast<int>(bc::error_code::api_not_found)) { state=0;return true; }
    if(code==static_cast<int>(bc::error_code::api_not_in_vision)) { state=-1;return true; }
    return false;
}
bool nearer(const Altar& a,const Altar& b) { return a.distance<b.distance||(a.distance==b.distance&&a.index<b.index); }
void insert(Altar* rows,int& n,int max,const Altar& value) {
    int at=0;while(at<n&&!nearer(value,rows[at]))++at;
    if(at>=max)return;
    for(int j=std::min(n,max-1);j>at;--j)rows[j]=rows[j-1];
    rows[at]=value;if(n<max)++n;
}
struct ShopSnapshot {
    std::uint32_t gold=0,counts[kItems]{},consumables[4]{};
    int items_allowed=0,consumables_allowed=0;
    d::champion_design design{};
};
bool shop_snapshot(std::uint32_t handle,int type,ShopSnapshot& s) {
    return d::sdk_champion_gold(handle,&s.gold)==0&&d::sdk_champion_items(handle,s.counts)==0&&
        d::sdk_champion_consumables(handle,s.consumables)==0&&
        d::sdk_champion_can_shop(handle,0,&s.items_allowed)==0&&
        d::sdk_champion_can_shop(handle,1,&s.consumables_allowed)==0&&d::sdk_champion_design(type,&s.design)==0;
}
// Gain from one explicit shard, including the automatic conversion on the fifth shard.
bool item_gains(int type,const d::item_info& info,const ShopSnapshot& s,float& health,float& strength,float& focus) {
    int hp=info.health_points,st=info.strength_points,fo=info.focus_points;
    if(info.combine_count&&s.counts[type]+1>=info.combine_count) {
        if(info.result>=kItems)return false;
        d::item_info result{};if(d::sdk_item_info(info.result,&result)!=0)return false;
        hp=result.health_points-static_cast<int>(info.combine_count-1)*info.health_points;
        st=result.strength_points-static_cast<int>(info.combine_count-1)*info.strength_points;
        fo=result.focus_points-static_cast<int>(info.combine_count-1)*info.focus_points;
    }
    health=hp*s.design.base_stats.health_growth;strength=st*s.design.base_stats.strength_growth;focus=fo*s.design.base_stats.focus_growth;
    return true;
}
}

struct nn_policy_economy_access {
    static std::uint64_t bank_candidate_fuel(const Bot& b) {
        // Metadata/container counts only: no live host queries, candidate construction or traversal.
        // Includes cold buffer work; a confirmed same-position/turn cache hit omits only the field term.
        const auto& layout=d::layout();const int radius=bc::constants::submit_gems_range;
        if(layout.width!=b.w.width||layout.height!=b.w.height||layout.board_bytes==0||
           layout.board_bytes>sizeof(g_bank.walls)||layout.field_bytes==0||layout.field_bytes>sizeof(g_bank.distance)||
           radius<0||radius>16)return std::numeric_limits<std::uint64_t>::max();
        const std::uint64_t ring_side=2*static_cast<std::uint64_t>(radius)+1;
        const std::uint64_t chunks=static_cast<std::uint64_t>(layout.chunked_width)*layout.chunked_height;
        const std::uint64_t field=cached_field(b.w,b.pos,b.my_id,b.round)?0:
            chunks*(kBankExpansionCap+24)+(static_cast<std::uint64_t>(layout.field_bytes)*2+
            static_cast<std::uint64_t>(layout.board_bytes)*4)/16+5000;
        return field+12000+static_cast<std::uint64_t>(b.w.altars.size())*(1200+ring_side*ring_side*96)+
            static_cast<std::uint64_t>(b.w.enemies.size())*250;
    }
    static bool bank(const Bot& b,const nnp::OptionsState&,nnpc::Decision& out) {
        out.K=0;d::champion_info me{};std::uint32_t gems=0,score=0;
        const int team=d::sdk_my_team();
        if(team<0||team>1||d::sdk_champion(b.my_id,&me)!=0||d::sdk_champion_gems(b.my_id,&gems)!=0||
           d::sdk_bc_submitted_gems(team,&score)!=0||!alive(me))return false;
        const vec2 self{me.x,me.y};if(!inside(self,b.w.width,b.w.height)||!equal(self,b.pos))return false;
        nnpc::Candidate rows[kBankK]{};int count=1;
        rows[0].id=0;rows[0].legal=1;
        int visible=0;float damage=0;
        for(const auto& e:b.w.enemies)if(e.hp>0&&(e.state&1u)&&bit(b.w.visible,e.pos)) {
            ++visible;if(cheb(e.pos,self)<=e.range+1)damage+=e.strength;
        }
        auto fill=[&](nnpc::Candidate& c,int action,vec2 altar,int distance,float lock) {
            const vec2 a=nnp::canonical(b,altar),p=nnp::canonical(b,self);
            float values[nnpc::kF]={static_cast<float>(action),static_cast<float>(a.x-p.x),static_cast<float>(a.y-p.y),
                static_cast<float>(distance),static_cast<float>(gems),static_cast<float>(bc::constants::winning_gems)-score,
                remaining(b.round),me.health/std::max(1.0f,me.max_health),static_cast<float>(visible),damage,
                static_cast<float>(channel_rounds(gems)),lock};
            std::copy_n(values,nnpc::kF,c.raw);
        };
        fill(rows[0],0,self,0,-1);
        if(gems>0&&channel_free(me)&&!b.w.altars.empty()) {
            std::uint8_t restrictions=0;if(d::sdk_champion_restrictions(b.my_id,&restrictions)!=0)return false;
            if(!(restrictions&1u)) {
                if(!make_field(b.w,self,b.my_id,b.round))return false;
                Altar nearest[kBankK-1]{},quadrants[4]{};int n=0,reachable=0;
                for(std::size_t i=0;i<b.w.altars.size();++i) {
                    if(i>(std::numeric_limits<std::uint32_t>::max()-2u)/2u)return false;
                    Altar a{};a.index=static_cast<std::uint32_t>(i);
                    if(!altar_distance(b.w,self,b.w.altars[i],a,b))return false;
                    if(a.distance==kUnreach) {
                        // A capped field cannot distinguish disconnected from farther than64. Never silently
                        // remove potentially reachable policy options: refuse this entire decision instead.
                        if(g_bank.expansions>=kBankExpansionCap)return false;
                        continue;
                    }
                    ++reachable;
                    float lock=-1;if(!lock_state(b.w.altars[i],team,lock))return false;
                    if(a.distance==0&&cheb(self,b.w.altars[i])<=bc::constants::submit_gems_range&&lock!=1&&count<kBankK) {
                        auto& c=rows[count++];c.id=2+2*a.index;c.legal=1;fill(c,2,b.w.altars[i],0,lock);
                    }
                    insert(nearest,n,kBankK-1,a);
                    if(nearer(a,quadrants[a.quadrant]))quadrants[a.quadrant]=a;
                }
                // Reserve one reachable destination per canonical quadrant, then nearest remaining.
                std::uint32_t selected[kBankK-1]{};int ns=0;
                auto append=[&](const Altar& a)->bool {
                    if(a.distance==kUnreach||count==kBankK)return true;
                    for(int j=0;j<ns;++j)if(selected[j]==a.index)return true;
                    float lock=-1;if(!lock_state(b.w.altars[a.index],team,lock))return false;
                    auto& c=rows[count++];c.id=1+2*a.index;c.legal=1;fill(c,1,b.w.altars[a.index],a.distance,lock);
                    selected[ns++]=a.index;return true;
                };
                // When no narrowing is necessary, retain every destination regardless of quadrant order.
                if(reachable<=kBankK-count) { for(int i=0;i<n;++i)if(!append(nearest[i]))return false; }
                else {
                    for(int q=0;q<4;++q)if(!append(quadrants[q]))return false;
                    for(int i=0;i<n;++i)if(!append(nearest[i]))return false;
                }
            }
        }
        return nnpc::build(nncfg::H::bank,rows,count,out.context,out)==nnpc::Error::ok;
    }
    static bool shop(const Bot& b,const nnp::OptionsState&,nnpc::Decision& out) {
        out.K=0;d::champion_info me{};if(d::sdk_champion(b.my_id,&me)!=0)return false;
        ShopSnapshot s{};if(!shop_snapshot(b.my_id,me.type,s))return false;
        nnpc::Candidate all[kItems+3]{};int n=1;
        all[0].legal=1;all[0].raw[3]=static_cast<float>(s.gold);all[0].raw[10]=remaining(b.round);
        for(int i=0;i<kItems;++i) {
            if(!s.items_allowed)break;
            d::item_info info{};if(d::sdk_item_info(i,&info)!=0)return false;
            if(!info.purchasable||info.cost>s.gold)continue;
            auto& c=all[n++];c.id=1+i;c.legal=1;c.raw[0]=1;c.raw[1]=static_cast<float>(i);
            c.raw[2]=static_cast<float>(info.cost);c.raw[3]=static_cast<float>(s.gold);c.raw[4]=static_cast<float>(s.counts[i]);
            if(!item_gains(i,info,s,c.raw[5],c.raw[6],c.raw[7]))return false;
            // No consumable in this SDK heals. Basic attack damage gains equal strength gains.
            // Inventory capacity is not exposed: zero is the documented unknown item-capacity sentinel.
            c.raw[9]=c.raw[6];c.raw[10]=remaining(b.round);
        }
        constexpr std::uint32_t raw_ids[2]={0,2};
        for(int i=0;i<2;++i) {
            if(!s.consumables_allowed)break;
            d::consumable_info info{};if(d::sdk_consumable_info(raw_ids[i],&info)!=0)return false;
            if(info.cost>s.gold||s.consumables[raw_ids[i]]>=info.carry_limit)continue;
            auto& c=all[n++];c.id=1000+raw_ids[i];c.legal=1;c.raw[0]=2;c.raw[1]=static_cast<float>(raw_ids[i]);
            c.raw[2]=static_cast<float>(info.cost);c.raw[3]=static_cast<float>(s.gold);c.raw[4]=static_cast<float>(s.consumables[raw_ids[i]]);
            c.raw[10]=remaining(b.round);c.raw[11]=static_cast<float>(info.carry_limit-s.consumables[raw_ids[i]]);
        }
        nnpc::Candidate rows[kShopK]{};int count=0;bool selected[kItems+3]{};
        auto append=[&](int i) { if(count<kShopK&&!selected[i])rows[count++]=all[i],selected[i]=true; };
        append(0);
        if(n<=kShopK) { for(int i=1;i<n;++i)append(i); }
        else {
            // One explicit affordable item from each family, then both live consumable kinds.
            for(int family=0;family<kFamilies;++family)
                for(int i=1;i<n;++i)if(all[i].id<=kItems&&static_cast<int>((all[i].id-1)/6)==family) { append(i);break; }
            for(int i=1;i<n;++i)if(all[i].id>=1000)append(i);
            // Fill by family round robin, each family's next lowest canonical item ID.
            while(count<kShopK) {
                const int before=count;
                for(int family=0;family<kFamilies;++family)
                    for(int i=1;i<n;++i)if(!selected[i]&&all[i].id<=kItems&&static_cast<int>((all[i].id-1)/6)==family) { append(i);break; }
                if(count==before)break;
            }
        }
        return nnpc::build(nncfg::H::shop,rows,count,out.context,out)==nnpc::Error::ok;
    }
    static nnp::Execution execute_bank(Bot& b,nnp::OptionsState& state,std::uint32_t id) {
        d::champion_info me{};std::uint32_t gems=0;std::uint8_t restrictions=0;
        if(d::sdk_champion(b.my_id,&me)!=0||!channel_free(me)||d::sdk_champion_gems(b.my_id,&gems)!=0)return {};
        if(id==0)return {true,true,false};
        const std::uint32_t index=(id-1)/2;const bool deposit=(id%2)==0;
        if(index>=b.w.altars.size()||gems==0||d::sdk_champion_restrictions(b.my_id,&restrictions)!=0||(restrictions&1u))return {};
        const vec2 self{me.x,me.y},altar=b.w.altars[index];
        if(deposit) {
            float lock=-1;const int team=d::sdk_my_team();
            if(team<0||team>1||cheb(self,altar)>bc::constants::submit_gems_range||!lock_state(altar,team,lock)||lock==1)return {};
            if(d::sdk_submit_gems(altar.x,altar.y)!=0)return {};
            state.altar=static_cast<int>(index);state.goal=self;return {true,true,true};
        }
        // Travel execution must use the field admitted for this decision. Never start an unbudgeted cold
        // search from the much smaller execution reserve if the self position changed after admission.
        if(!cached_field(b.w,self,b.my_id,b.round))return {};
        Altar a{};if(!altar_distance(b.w,self,altar,a,b)||a.distance==kUnreach)return {};
        const bool changed=state.altar!=static_cast<int>(index)||!equal(state.goal,a.goal);
        state.altar=static_cast<int>(index);state.goal=a.goal;return {true,true,changed};
    }
    static nnp::Execution execute_shop(Bot& b,nnp::OptionsState&,std::uint32_t id) {
        if(id==0)return {true,true,false};
        std::uint32_t gold=0;if(d::sdk_champion_gold(b.my_id,&gold)!=0)return {};
        int allowed=0;
        if(id>=1&&id<=kItems) {
            d::item_info info{};const std::uint32_t item=id-1;
            if(d::sdk_champion_can_shop(b.my_id,0,&allowed)!=0||!allowed||d::sdk_item_info(item,&info)!=0||!info.purchasable||info.cost>gold)return {};
            if(d::sdk_buy_item(item,1)!=0)return {};
        } else if(id==1000||id==1002) {
            const std::uint32_t raw=id-1000;d::consumable_info info{};std::uint32_t counts[4]{};
            if(d::sdk_champion_can_shop(b.my_id,1,&allowed)!=0||!allowed||d::sdk_consumable_info(raw,&info)!=0||
               d::sdk_champion_consumables(b.my_id,counts)!=0||info.cost>gold||counts[raw]>=info.carry_limit)return {};
            if(d::sdk_buy_consumable(raw)!=0)return {};
        } else return {};
        // Purchases can change max health and combined stats. Refresh our legal self snapshot immediately.
        // A failed follow-up read cannot turn an already completed purchase into a failed action ack.
        try { b.refresh_self(); } catch(...) {}
        return {true,true,true};
    }
};
namespace nnp {
std::uint64_t bank_candidate_fuel(const Bot& b) { return nn_policy_economy_access::bank_candidate_fuel(b); }
bool build_bank(const Bot& b,const OptionsState& s,nnpc::Decision& d) { return nn_policy_economy_access::bank(b,s,d); }
bool build_shop(const Bot& b,const OptionsState& s,nnpc::Decision& d) { return nn_policy_economy_access::shop(b,s,d); }
Execution execute_bank(Bot& b,OptionsState& s,std::uint32_t id) { return nn_policy_economy_access::execute_bank(b,s,id); }
Execution execute_shop(Bot& b,OptionsState& s,std::uint32_t id) { return nn_policy_economy_access::execute_shop(b,s,id); }
}
#endif // NN_POLICY_V2
