// Direct v2 strategic options. Only cached static geometry and permitted observations are read.
#include "nn_policy_options.h"
#if NN_POLICY_V2
#include "bot.h"

namespace {
constexpr int kUnknownDistance=10000;
bool inside(vec2 p,const World& w) { return p.x>=0&&p.y>=0&&p.x<w.width&&p.y<w.height; }
bool same(vec2 a,vec2 b) { return a.x==b.x&&a.y==b.y; }
struct Goal { bool legal=false; vec2 pos{-1,-1}; int distance=kUnknownDistance,group=-1; };
struct GroupOption { int group=-1,distance=kUnknownDistance; std::uint32_t id=0; vec2 anchor{}; };
}

struct nn_policy_strategy_access {
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
        bool found=false;vec2 anchor{},key{};
        for(int ci:g.camps) {
            if(ci<0||ci>=static_cast<int>(b.w.camps.size()))return false;
            const vec2 p=b.w.camps[static_cast<std::size_t>(ci)].pos;if(!inside(p,b.w))return false;
            const vec2 c=nnp::canonical(b,p);
            if(!found||c.y<key.y||(c.y==key.y&&c.x<key.x))anchor=p,key=c,found=true;
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
        for(int i=0;i<7;++i) {
            const Goal g=goals[i];auto& r=rows[i];r.id=i;r.legal=g.legal;
            const float f[12]={static_cast<float>(i),b.hp/std::max(1.0f,b.max_hp),static_cast<float>(b.gems),static_cast<float>(b.gold),
                static_cast<float>(remaining(b)),static_cast<float>(g.distance),allies,enemies,strength,static_cast<float>(b.ally_score-b.enemy_score),
                g.group>=0?static_cast<float>(b.w.groups[static_cast<std::size_t>(g.group)].gems):0,damage[i]};
            std::copy(f,f+12,r.raw);
        }
        return nnpc::build(nncfg::H::strategy,rows,7,context(b,s),out)==nnpc::Error::ok;
    }
    static bool objective(const Bot& b,const nnp::OptionsState& s,nnpc::Decision& out) {
        if(!usable(b)){out.K=0;return false;}
        // Keep the best16 per quadrant, then take four each and fill unused quotas round-robin.
        // Fixed buffers bound memory; every comparison is static distance then public handle.
        GroupOption bucket[4][16]{};int count[4]{};const vec2 self=nnp::canonical(b,b.pos);
        for(int gi=0;gi<static_cast<int>(b.w.groups.size());++gi) {
            GroupOption q;if(!group(b,gi,q))continue;const vec2 c=nnp::canonical(b,q.anchor);
            const int quadrant=(c.x>=self.x?1:0)|(c.y>=self.y?2:0);int at=0;
            while(at<count[quadrant]&&!nearer(q,bucket[quadrant][at]))++at;
            if(at>=16)continue;const int last=std::min(count[quadrant],15);
            for(int j=last;j>at;--j)bucket[quadrant][j]=bucket[quadrant][j-1];
            bucket[quadrant][at]=q;if(count[quadrant]<16)++count[quadrant];
        }
        GroupOption selected[16]{};int used[4]{},n=0;
        for(int q=0;q<4;++q)for(int i=0;i<std::min(4,count[q]);++i)selected[n++]=bucket[q][used[q]++];
        for(bool added=true;n<16&&added;) {
            added=false;for(int q=0;q<4&&n<16;++q)if(used[q]<count[q])selected[n++]=bucket[q][used[q]++],added=true;
        }
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
        // Farmer/scout share the same reachability precondition. Building masks needs only existence,
        // not their exact nearest/oldest destination, so stop at the first cached reachable group.
        bool reachable=assigned;
        if(active&&!reachable)for(int gi=0;gi<static_cast<int>(b.w.groups.size())&&!reachable;++gi)reachable=group(b,gi,q);
        for(int i=0;i<5;++i) {
            const float f[12]={static_cast<float>(i),static_cast<float>(b.slot),b.hp/std::max(1.0f,b.max_hp),static_cast<float>(b.gems),
                static_cast<float>(b.gold),static_cast<float>(b.range),allies,enemies,static_cast<float>(distance),static_cast<float>(claims(b,s.objective)),
                static_cast<float>(b.ally_score-b.enemy_score),static_cast<float>(remaining(b))};
            rows[i].id=i;rows[i].legal=(i==0||i==4)?reachable:role_goal(b,s,i).legal;std::copy(f,f+12,rows[i].raw);
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
        if(id>6)return {};const Goal g=intent_goal(b,s,static_cast<int>(id));if(!g.legal)return {};
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
        if(id>4)return {};const Goal g=role_goal(b,s,static_cast<int>(id));if(!g.legal)return {};
        const int intent=id==1?1:id==2?5:id==3?4:0;
        const bool changed=s.role!=static_cast<int>(id)||s.intent!=intent||s.objective!=g.group||!same(s.goal,g.pos);
        s.role=static_cast<int>(id);s.intent=intent;s.objective=g.group;s.goal=g.pos;s.altar=-1;
        b.target_group=g.group;claim(b,g.group);b.mode="nn-v2-role";
        return {true,true,changed};
    }
};

namespace nnp {
bool build_strategy(const Bot& b,const OptionsState& s,nnpc::Decision& d) {return nn_policy_strategy_access::strategy(b,s,d);}
bool build_objective(const Bot& b,const OptionsState& s,nnpc::Decision& d) {return nn_policy_strategy_access::objective(b,s,d);}
bool build_role(const Bot& b,const OptionsState& s,nnpc::Decision& d) {return nn_policy_strategy_access::role(b,s,d);}
Execution execute_strategy(Bot& b,OptionsState& s,std::uint32_t id) {return nn_policy_strategy_access::execute_strategy(b,s,id);}
Execution execute_objective(Bot& b,OptionsState& s,std::uint32_t id) {return nn_policy_strategy_access::execute_objective(b,s,id);}
Execution execute_role(Bot& b,OptionsState& s,std::uint32_t id) {return nn_policy_strategy_access::execute_role(b,s,id);}
bool resume_assignments(Bot& b,const OptionsState& s) {return nn_policy_strategy_access::resume(b,s);}
}
#endif
