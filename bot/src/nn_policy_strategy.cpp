// Direct v2 strategic options. Only cached static geometry and permitted observations are read.
#include "nn_policy_options.h"
#if NN_POLICY_V2
#include "bot.h"

namespace {
constexpr int kUnknownDistance=10000;
bool inside(vec2 p,const World& w) { return p.x>=0&&p.y>=0&&p.x<w.width&&p.y<w.height; }
bool same(vec2 a,vec2 b) { return a.x==b.x&&a.y==b.y; }
struct Goal { bool legal=false; vec2 pos{-1,-1}; int distance=kUnknownDistance,group=-1; };
struct Preview {const Bot* owner=nullptr;int round=-1;vec2 pos{};nnp::OptionsState state{};Goal choice[7]{};bool ready=false;};
constinit Preview g_strategy_preview{},g_role_preview{};
// Camp spawn geometry is immutable. Cache canonical anchors, never scores or a selected objective.
constinit const Bot* g_anchor_owner=nullptr;
constinit std::size_t g_anchor_groups=0,g_anchor_camps=0;
constinit vec2 g_anchor_frame{};
constinit vec2 g_anchor[1024]{};
constinit bool g_anchor_ready[1024]{};
struct GroupOption { int group=-1,distance=kUnknownDistance; std::uint32_t id=0; vec2 anchor{}; };
struct ObjectiveGeometry {const Bot* owner=nullptr;vec2 pos{},frame{};std::size_t groups=0;int fields=-1,n=0;GroupOption selected[16]{};};
constinit ObjectiveGeometry g_objective_geometry{};
}

struct nn_policy_strategy_access {
    static std::uint64_t bound(const Bot& b,nncfg::H head) {
        // Includes the cached static group traversal and selected-row descriptors. No SDK reads.
        const auto groups=std::uint64_t(b.w.groups.size()),camps=std::uint64_t(b.w.camps.size());
        const auto bodies=std::uint64_t(b.w.enemies.size()+b.w.allies.size());
        if(head==nncfg::H::objective&&geometry_cached(b))return 5000+
            std::uint64_t(g_objective_geometry.n)*1600+bodies*g_objective_geometry.n*150+camps*35;
        return (head==nncfg::H::objective?22000:9000)+groups*(head==nncfg::H::objective?500:180)+camps*180+bodies*2200+
               std::uint64_t(b.w.spawn_tiles.size()+b.w.sightings.size())*100;
    }
    static bool same_state(const nnp::OptionsState& a,const nnp::OptionsState& c) {
        return a.intent==c.intent&&a.role==c.role&&a.objective==c.objective&&a.altar==c.altar&&
               a.engagement==c.engagement&&same(a.goal,c.goal);
    }
    static void save(Preview& p,const Bot& b,const nnp::OptionsState& s,const Goal* goals,int n) {
        p.owner=&b;p.round=b.round;p.pos=b.pos;p.state=s;p.ready=true;
        std::copy_n(goals,n,p.choice);
    }
    static bool cached(Preview& p,const Bot& b,const nnp::OptionsState& s,int id,Goal& g) {
        if(!p.ready||p.owner!=&b||p.round!=b.round||!same(p.pos,b.pos)||!same_state(p.state,s))return false;
        g=p.choice[id];p.ready=false;
        if(!usable(b)||!g.legal){g.legal=false;return true;}
        if(g.group>=0){GroupOption q;if(!group(b,g.group,q)||!same(q.anchor,g.pos))g.legal=false;}
        return true;
    }
    static bool usable(const Bot& b) { return b.inited&&b.hp>0&&inside(b.pos,b.w); }
    static bool visible(const Bot& b,vec2 p) { return inside(p,b.w)&&bit(b.w.visible,p); }
    static std::uint8_t context(const Bot& b,const nnp::OptionsState& s) {
        return s.intent==6?2:!b.w.enemies.empty()?1:(s.intent==2||s.intent==4)?3:0;
    }
    static int remaining(const Bot& b) { return std::max(0,static_cast<int>(bc::constants::max_rounds)-b.round); }
    static int claims(const Bot& b,int gi) {
        if(gi<0||gi>=static_cast<int>(kClaimCodeDead))return 0;
        int n=0; for(int s=0;s<std::min(b.team_size,kClaimSlots);++s)
            n+=s!=b.slot&&static_cast<int>((b.shared>>(s*kClaimBits))&kClaimMask)==gi;
        return n;
    }
    // Missing fields are unknown, never substituted with geometric distance or teacher ranking.
    static bool group(const Bot& b,int gi,GroupOption& out) {
        if(gi<0||gi>=static_cast<int>(b.w.groups.size())||!b.w.has_field(gi))return false;
        const auto& g=b.w.groups[static_cast<std::size_t>(gi)];
        const int distance=b.w.group_distance(gi,b.pos);if(distance==kUnreach||g.camps.empty())return false;
        const auto frame=nnp::canonical(b,{0,0});
        if(g_anchor_owner!=&b||g_anchor_groups!=b.w.groups.size()||g_anchor_camps!=b.w.camps.size()||!same(g_anchor_frame,frame)) {
            g_anchor_owner=&b;g_anchor_groups=b.w.groups.size();g_anchor_camps=b.w.camps.size();g_anchor_frame=frame;
            std::fill_n(g_anchor_ready,1024,false);
        }
        bool found=gi<1024&&g_anchor_ready[gi];vec2 anchor=found?g_anchor[gi]:vec2{},key{};
        if(!found) {
            for(int ci:g.camps) {
                if(ci<0||ci>=static_cast<int>(b.w.camps.size()))return false;
                const vec2 p=b.w.camps[static_cast<std::size_t>(ci)].pos;if(!inside(p,b.w))return false;
                const vec2 c=nnp::canonical(b,p);
                if(!found||c.y<key.y||(c.y==key.y&&c.x<key.x))anchor=p,key=c,found=true;
            }
            if(found&&gi<1024)g_anchor[gi]=anchor,g_anchor_ready[gi]=true;
        }
        if(!found)return false;
        out={gi,distance,g.handle,anchor};return true;
    }
    static bool nearer(const GroupOption& a,const GroupOption& b) {
        return a.distance<b.distance||(a.distance==b.distance&&a.id<b.id);
    }
    static Goal scout(const Bot& b) {
        GroupOption best,q;bool found=false;int oldest=0;
        for(int gi=0;gi<static_cast<int>(b.w.groups.size());++gi)if(group(b,gi,q)) {
            const int seen=b.w.groups[static_cast<std::size_t>(gi)].seen_round;
            if(!found||seen<oldest||(seen==oldest&&nearer(q,best)))best=q,oldest=seen,found=true;
        }
        return found?Goal{true,best.anchor,best.distance,best.group}:Goal{};
    }
    static Goal home(const Bot& b) {
        Goal out;const int d=fdist(b.w.spawn_field,b.pos);if(d==kUnreach)return out;
        int best=kUnknownDistance;vec2 key{};
        for(vec2 p:b.w.spawn_tiles) {
            if(!inside(p,b.w))continue;const int distance=cheb(p,b.pos);const vec2 c=nnp::canonical(b,p);
            if(!out.legal||distance<best||(distance==best&&(c.y<key.y||(c.y==key.y&&c.x<key.x))))
                out={true,p,d,-1},best=distance,key=c;
        }
        return out;
    }
    static Goal intent_goal(const Bot& b,const nnp::OptionsState& s,int intent) {
        Goal out;if(!usable(b))return out;
        if(intent==0||intent==3) {
            GroupOption best,q;bool found=false;
            if(group(b,s.objective,q))return {true,q.anchor,q.distance,q.group};
            if(s.role==4)return scout(b);
            for(int gi=0;gi<static_cast<int>(b.w.groups.size());++gi)
                if(group(b,gi,q)&&(!found||nearer(q,best)))best=q,found=true;
            if(found)return {true,best.anchor,best.distance,best.group};
        } else if(intent==1) {
            // The bank head owns destination selection and the exact per-altar reachability recheck.
            // An uncomputed aggregate field does not assert that every altar is reachable.
            if(b.gems>0&&!b.w.no_bank&&!b.w.altars.empty()) {
                const int d=b.w.altar_ready?fdist(b.w.altar_field,b.pos):kUnknownDistance;
                if(d!=kUnreach)return {true,b.pos,d,-1};
            }
        } else if(intent==2||intent==6) return home(b);
        else if(intent==4) {
            const AllyRec* best=nullptr;int distance=kUnknownDistance;
            for(const auto& a:b.w.allies)if(a.hp>0&&a.id!=b.my_id&&visible(b,a.pos)) {
                const int d=cheb(a.pos,b.pos);
                if(!best||d<distance||(d==distance&&a.id<best->id))best=&a,distance=d;
            }
            if(best)return {true,best->pos,kUnknownDistance,-1};
        } else if(intent==5) {
            const EnemyRec* best=nullptr;int distance=kUnknownDistance;
            for(const auto& e:b.w.enemies)if(e.hp>0&&(e.state&1u)&&visible(b,e.pos)) {
                const int d=cheb(e.pos,b.pos);
                if(!best||d<distance||(d==distance&&e.id<best->id))best=&e,distance=d;
            }
            if(best)return {true,best->pos,kUnknownDistance,-1};
            // Sightings are our legally remembered, aged observations, never private enemy positions.
            const Sighting* latest=nullptr;vec2 key{};
            for(const auto& sight:b.w.sightings) {
                if(!inside(sight.pos,b.w)||sight.round>b.round||b.round-sight.round>100)continue;
                const vec2 c=nnp::canonical(b,sight.pos);
                if(!latest||sight.round>latest->round||(sight.round==latest->round&&(c.y<key.y||(c.y==key.y&&c.x<key.x))))
                    latest=&sight,key=c;
            }
            if(latest)return {true,latest->pos,kUnknownDistance,-1};
        }
        return out;
    }
    static void nearby(const Bot& b,float& allies,float& enemies,float& strength) {
        allies=0;enemies=0;strength=b.strength;
        for(const auto& a:b.w.allies)if(a.hp>0&&a.id!=b.my_id&&visible(b,a.pos)&&cheb(a.pos,b.pos)<=8)++allies,strength+=a.strength;
        for(const auto& e:b.w.enemies)if(e.hp>0&&(e.state&1u)&&visible(b,e.pos)&&cheb(e.pos,b.pos)<=8)++enemies,strength-=e.strength;
    }
    static float threat(const Bot& b,vec2 p) {
        float damage=0;if(!inside(p,b.w))return damage;
        for(const auto& e:b.w.enemies)if(e.hp>0&&(e.state&1u)&&visible(b,e.pos)&&cheb(e.pos,p)<=e.range)damage+=e.strength;
        for(std::size_t i=0;i<b.w.camps.size();++i) {
            const auto& c=b.w.camps[i];
            if(!c.dead&&c.hp>0&&i<b.w.camp_visible.size()&&b.w.camp_visible[i]&&cheb(c.pos,p)<=c.range)damage+=c.strength;
        }
        return damage;
    }
    static bool strategy(const Bot& b,const nnp::OptionsState& s,nnpc::Decision& out) {
        nnpc::Candidate rows[7]{};float allies,enemies,strength;nearby(b,allies,enemies,strength);
        Goal goals[7]{};float damage[7]{};
        // Farm/contest and defend/retreat share availability/geometry, not preference scores.
        // Cache these descriptors so a missing current objective never scans all groups twice.
        if(usable(b)) {
            goals[0]=intent_goal(b,s,0);goals[3]=goals[0];
            goals[1]=intent_goal(b,s,1);goals[2]=home(b);goals[6]=goals[2];
            goals[4]=intent_goal(b,s,4);goals[5]=intent_goal(b,s,5);
        }
        for(int i=0;i<7;++i) {
            bool reused=false;for(int j=0;j<i;++j)if(same(goals[i].pos,goals[j].pos)) {damage[i]=damage[j];reused=true;break;}
            if(!reused)damage[i]=threat(b,goals[i].pos);
        }
        save(g_strategy_preview,b,s,goals,7);
        for(int i=0;i<7;++i) {
            const Goal g=goals[i];auto& r=rows[i];r.id=i;r.legal=g.legal;
            const float f[12]={static_cast<float>(i),b.hp/std::max(1.0f,b.max_hp),static_cast<float>(b.gems),static_cast<float>(b.gold),
                static_cast<float>(remaining(b)),static_cast<float>(g.distance),allies,enemies,strength,static_cast<float>(b.ally_score-b.enemy_score),
                g.group>=0?static_cast<float>(b.w.groups[static_cast<std::size_t>(g.group)].gems):0,damage[i]};
            std::copy(f,f+12,r.raw);
        }
        return nnpc::build(nncfg::H::strategy,rows,7,context(b,s),out)==nnpc::Error::ok;
    }
    static int fields(const Bot& b) {
        int n=0;for(int gi=0;gi<static_cast<int>(b.w.groups.size());++gi)n+=b.w.has_field(gi);return n;
    }
    static bool geometry_cached(const Bot& b) {
        const auto& g=g_objective_geometry;
        return g.owner==&b&&same(g.pos,b.pos)&&g.groups==b.w.groups.size()&&g.fields==fields(b)&&same(g.frame,nnp::canonical(b,{0,0}));
    }
    static int geometry(const Bot& b,GroupOption* selected) {
        if(geometry_cached(b)){std::copy_n(g_objective_geometry.selected,g_objective_geometry.n,selected);return g_objective_geometry.n;}
        // Keep the best16 per quadrant, then take four each and fill unused quotas round-robin.
        // Fixed buffers bound memory; every comparison is static distance then public handle.
        GroupOption bucket[4][16]{};int count[4]{};const vec2 self=nnp::canonical(b,b.pos);
        for(int gi=0;gi<static_cast<int>(b.w.groups.size());++gi) {
            GroupOption q;if(!group(b,gi,q))continue;const vec2 c=nnp::canonical(b,q.anchor);
            const int quadrant=(c.x>=self.x?1:0)|(c.y>=self.y?2:0);
            auto* heap=bucket[quadrant];auto& size=count[quadrant];
            if(size<16){heap[size++]=q;std::push_heap(heap,heap+size,nearer);}
            else if(nearer(q,heap[0])){std::pop_heap(heap,heap+size,nearer);heap[size-1]=q;std::push_heap(heap,heap+size,nearer);}
        }
        for(int q=0;q<4;++q)std::sort_heap(bucket[q],bucket[q]+count[q],nearer);
        int used[4]{},n=0;
        for(int q=0;q<4;++q)for(int i=0;i<std::min(4,count[q]);++i)selected[n++]=bucket[q][used[q]++];
        for(bool added=true;n<16&&added;) {
            added=false;for(int q=0;q<4&&n<16;++q)if(used[q]<count[q])selected[n++]=bucket[q][used[q]++],added=true;
        }
        auto& cached=g_objective_geometry;cached.owner=&b;cached.pos=b.pos;cached.frame=nnp::canonical(b,{0,0});
        cached.groups=b.w.groups.size();cached.fields=fields(b);cached.n=n;std::copy_n(selected,n,cached.selected);
        return n;
    }
    static bool objective(const Bot& b,const nnp::OptionsState& s,nnpc::Decision& out) {
        if(!usable(b)){out.K=0;return false;}
        GroupOption selected[16]{};const int n=geometry(b,selected);const auto self=nnp::canonical(b,b.pos);
        nnpc::Candidate rows[16]{};
        for(int i=0;i<n;++i) {
            const auto& q=selected[i];const auto& g=b.w.groups[static_cast<std::size_t>(q.group)];const vec2 c=nnp::canonical(b,q.anchor);
            float hp=0;for(int ci:g.camps)if(!b.w.camps[static_cast<std::size_t>(ci)].dead)hp+=b.w.camps[static_cast<std::size_t>(ci)].hp;
            int enemies=0;for(const auto& e:b.w.enemies)if(e.hp>0&&(e.state&1u)&&visible(b,e.pos)&&cheb(e.pos,q.anchor)<=8)++enemies;
            const float f[12]={static_cast<float>(c.x-self.x),static_cast<float>(c.y-self.y),static_cast<float>(q.distance),static_cast<float>(g.gems),
                static_cast<float>(g.gold),hp,g.strength,static_cast<float>(bc::constants::capture_time),
                g.state==GroupState::respawning?static_cast<float>(std::max(0,g.respawn_round-b.round)):0,static_cast<float>(claims(b,q.group)),
                static_cast<float>(enemies),g.seen_round<0?static_cast<float>(std::max(0,b.round)+1):static_cast<float>(std::max(0,b.round-g.seen_round))};
            rows[i].id=q.id;rows[i].legal=1;std::copy(f,f+12,rows[i].raw);
        }
        return nnpc::build(nncfg::H::objective,rows,n,context(b,s),out)==nnpc::Error::ok;
    }
    static bool role(const Bot& b,const nnp::OptionsState& s,nnpc::Decision& out) {
        nnpc::Candidate rows[5]{};float allies,enemies,strength;nearby(b,allies,enemies,strength);GroupOption q;
        const bool active=usable(b),assigned=active&&group(b,s.objective,q);
        const int distance=assigned?q.distance:kUnknownDistance;
        Goal goals[5]{};GroupOption nearest{},oldest{},current{};bool any=false;int oldest_round=0;
        // One geometric pass supplies both farmer/scout descriptors and their exact guarded executors.
        // The objective network still has to select a group before physical farming is permitted.
        if(active)for(int gi=0;gi<static_cast<int>(b.w.groups.size());++gi)if(group(b,gi,current)) {
            const int seen=b.w.groups[gi].seen_round;
            if(!any||nearer(current,nearest))nearest=current;
            if(!any||seen<oldest_round||(seen==oldest_round&&nearer(current,oldest)))oldest=current,oldest_round=seen;
            any=true;
        }
        if(assigned)goals[0]={true,q.anchor,q.distance,q.group};
        else if(any)goals[0]={true,nearest.anchor,nearest.distance,nearest.group};
        if(any)goals[4]={true,oldest.anchor,oldest.distance,oldest.group};
        for(int i=1;i<=3;++i)goals[i]=role_goal(b,s,i);
        save(g_role_preview,b,s,goals,5);
        for(int i=0;i<5;++i) {
            const float f[12]={static_cast<float>(i),static_cast<float>(b.slot),b.hp/std::max(1.0f,b.max_hp),static_cast<float>(b.gems),
                static_cast<float>(b.gold),static_cast<float>(b.range),allies,enemies,static_cast<float>(distance),static_cast<float>(claims(b,s.objective)),
                static_cast<float>(b.ally_score-b.enemy_score),static_cast<float>(remaining(b))};
            rows[i].id=i;rows[i].legal=goals[i].legal;std::copy(f,f+12,rows[i].raw);
        }
        return nnpc::build(nncfg::H::role,rows,5,context(b,s),out)==nnpc::Error::ok;
    }
    static void claim(Bot& b,int gi) { b.write_claim(gi>=0&&gi<static_cast<int>(kClaimCodeDead)?gi:-1); }
    static Goal role_goal(const Bot& b,const nnp::OptionsState& s,int role) {
        if(!usable(b))return {};
        if(role==0) {auto farmer=s;farmer.role=0;return intent_goal(b,farmer,0);}
        if(role==1)return intent_goal(b,s,1);
        if(role==2) {
            // Fighter requires a current visible target; old sightings alone permit strategic attack.
            bool enemy=false;for(const auto& e:b.w.enemies)enemy|=e.hp>0&&(e.state&1u)&&visible(b,e.pos);
            return enemy?intent_goal(b,s,5):Goal{};
        }
        if(role==3)return intent_goal(b,s,4);
        if(role==4)return scout(b);
        return {};
    }
    static bool resume(Bot& b,const nnp::OptionsState& s) {
        if(!usable(b)||s.role<0||s.role>4||s.intent<0||s.intent>6||!inside(s.goal,b.w))return false;
        // Check role availability as a predicate. Reexecuting the role would overwrite a newer strategy.
        if(s.role==0||s.role==4) {
            GroupOption q;bool reachable=group(b,s.objective,q);
            if(!reachable)for(int gi=0;gi<static_cast<int>(b.w.groups.size())&&!reachable;++gi)reachable=group(b,gi,q);
            if(!reachable)return false;
        } else if(s.role==1) {
            if(!intent_goal(b,s,1).legal)return false;
        } else if(s.role==2) {
            bool target=false;for(const auto& e:b.w.enemies)target|=e.hp>0&&(e.state&1u)&&visible(b,e.pos);
            if(!target)return false;
        } else if(s.role==3) {
            bool ally=false;for(const auto& a:b.w.allies)ally|=a.hp>0&&a.id!=b.my_id&&visible(b,a.pos);
            if(!ally)return false;
        }
        const bool farming=s.intent==0||s.intent==3;int objective=-1;
        if(farming) {
            // An unavailable selected group invalidates this assignment; never substitute another group.
            GroupOption q;if(!group(b,s.objective,q))return false;objective=s.objective;
        } else if(!intent_goal(b,s,s.intent).legal)return false;
        b.target_group=objective;
        // The whole-bot teacher may have changed our target/claim during the suspended turn.
        // Republish only when necessary. Nonencodable local group indices remain idle on the wire.
        if(b.slot>=0&&b.slot<kClaimSlots) {
            const int published=objective>=0&&objective<static_cast<int>(kClaimCodeDead)?objective:static_cast<int>(kClaimMask);
            const int observed=static_cast<int>((b.shared>>(b.slot*kClaimBits))&kClaimMask);
            if(published!=observed)claim(b,objective);
        }
        return true;
    }
    static nnp::Execution execute_strategy(Bot& b,nnp::OptionsState& s,std::uint32_t id) {
        if(id>6)return {};Goal g;if(!cached(g_strategy_preview,b,s,static_cast<int>(id),g))g=intent_goal(b,s,static_cast<int>(id));if(!g.legal)return {};
        const bool farming=id==0||id==3;const int objective=farming?g.group:-1;
        const bool changed=s.intent!=static_cast<int>(id)||s.objective!=objective||!same(s.goal,g.pos);
        s.intent=static_cast<int>(id);s.objective=objective;s.goal=g.pos;if(id!=1)s.altar=-1;
        b.target_group=objective;claim(b,objective);b.mode="nn-v2-strategy";
        return {true,true,changed};
    }
    static nnp::Execution execute_objective(Bot& b,nnp::OptionsState& s,std::uint32_t id) {
        if(!usable(b)||(s.intent!=0&&s.intent!=3))return {};
        for(int gi=0;gi<static_cast<int>(b.w.groups.size());++gi)if(b.w.groups[static_cast<std::size_t>(gi)].handle==id) {
            GroupOption q;if(!group(b,gi,q))return {};
            const bool changed=s.objective!=gi||!same(s.goal,q.anchor);s.objective=gi;s.goal=q.anchor;s.altar=-1;
            b.target_group=gi;claim(b,gi);b.mode="nn-v2-objective";return {true,true,changed};
        }
        return {};
    }
    static nnp::Execution execute_role(Bot& b,nnp::OptionsState& s,std::uint32_t id) {
        if(id>4)return {};Goal g;if(!cached(g_role_preview,b,s,static_cast<int>(id),g))g=role_goal(b,s,static_cast<int>(id));if(!g.legal)return {};
        if(id==1&&b.gems<=0)return {};
        const int intent=id==1?1:id==2?5:id==3?4:0;
        const bool changed=s.role!=static_cast<int>(id)||s.intent!=intent||s.objective!=g.group||!same(s.goal,g.pos);
        s.role=static_cast<int>(id);s.intent=intent;s.objective=g.group;s.goal=g.pos;s.altar=-1;
        b.target_group=g.group;claim(b,g.group);b.mode="nn-v2-role";
        return {true,true,changed};
    }
};

namespace nnp {
void prepare_strategy(const Bot& b,std::uint64_t reserve) {
    if(!nn_policy_strategy_access::usable(b)||nn_policy_strategy_access::geometry_cached(b))return;
    const auto cost=nn_policy_strategy_access::bound(b,nncfg::H::objective);
    if(bc::fuel_remaining()>cost+reserve){GroupOption selected[16]{};nn_policy_strategy_access::geometry(b,selected);}
}
std::uint64_t strategy_candidate_fuel(const Bot& b,nncfg::H h) {return nn_policy_strategy_access::bound(b,h);}
bool build_strategy(const Bot& b,const OptionsState& s,nnpc::Decision& d) {return nn_policy_strategy_access::strategy(b,s,d);}
bool build_objective(const Bot& b,const OptionsState& s,nnpc::Decision& d) {return nn_policy_strategy_access::objective(b,s,d);}
bool build_role(const Bot& b,const OptionsState& s,nnpc::Decision& d) {return nn_policy_strategy_access::role(b,s,d);}
Execution execute_strategy(Bot& b,OptionsState& s,std::uint32_t id) {return nn_policy_strategy_access::execute_strategy(b,s,id);}
Execution execute_objective(Bot& b,OptionsState& s,std::uint32_t id) {return nn_policy_strategy_access::execute_objective(b,s,id);}
Execution execute_role(Bot& b,OptionsState& s,std::uint32_t id) {return nn_policy_strategy_access::execute_role(b,s,id);}
bool resume_assignments(Bot& b,const OptionsState& s) {return nn_policy_strategy_access::resume(b,s);}
}
#endif
