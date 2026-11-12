// Explicit rendezvous and repeated team clears at a concentrated gem objective.
#include "bot.h"
#if V85_OBJECTIVE
bool Bot::resource_team_objective() {
    if(bc::fuel_remaining()<30000 || hp<max_hp*0.55f) return false;
    if(objective_cluster.empty()) {
        if(objective_checked || bc::fuel_remaining()<55000)return false;
        objective_checked=true;
        // A geometry feature, not a map-name lookup: >=60% of all gems in one compact region.
        struct Point {vec2 p;float gems;};Point ps[128];int n=0;float total=0;
        for(const auto& g:w.groups){total+=g.gems;if(!g.gems || g.camps.empty() || n==128)continue;
            vec2 p{};for(int ci:g.camps)p=p+w.camps[ci].pos;
            p.x/=static_cast<int>(g.camps.size());p.y/=static_cast<int>(g.camps.size());ps[n++]={p,static_cast<float>(g.gems)};
        }
        if(total<=0)return false;
        float best=0;vec2 center{};
        for(int i=0;i<n;++i){float value=0;for(int j=0;j<n;++j)if(cheb(ps[i].p,ps[j].p)<=6)value+=ps[j].gems;
            if(value>best){best=value;center=ps[i].p;}}
        if(best<0.6f*total)return false;
        objective_center=center;
        for(std::size_t gi=0;gi<w.groups.size();++gi){const auto& g=w.groups[gi];if(!g.gems || g.camps.empty())continue;
            vec2 p{};for(int ci:g.camps)p=p+w.camps[ci].pos;
            p.x/=static_cast<int>(g.camps.size());p.y/=static_cast<int>(g.camps.size());
            if(cheb(p,center)<=6)objective_cluster.push_back(static_cast<int>(gi));
        }
        int best_home=kUnreach;
        // Bounded rays choose a reachable home-side staging tile outside monster attack areas.
        for(int rad=8;rad<=12;++rad)for(vec2 dir:kDirs){const vec2 q{center.x+rad*dir.x,center.y+rad*dir.y};
            if(q.x<0 || q.y<0 || q.x>=w.width || q.y>=w.height || bit(w.static_blocked,q))continue;
            bool unsafe=false;for(int gi:objective_cluster)for(int ci:w.groups[gi].camps){const auto& c=w.camps[ci];unsafe|=c.strength>0 && cheb(c.pos,q)<=c.range+1;}
            const int home=fdist(w.spawn_field,q);if(!unsafe && home<best_home){best_home=home;objective_stage=q;}
        }
        if(objective_stage.x<0)objective_cluster.clear();
    }
    if(objective_cluster.empty())return false;
    const int required=std::min(3,std::max(2,(team_size+1)/2));
    int local=1;for(const auto& a:w.allies)if(a.hp>=0.55f*a.max_hp && cheb(a.pos,pos)<=5)++local;
    if(local>=required)objective_until=round+30;
    const bool at_objective=cheb(pos,objective_center)<=8;
    if(round>objective_until || (!at_objective && local<required)) {
        // Wait only at the staging area. Distant workers keep walking there, rather than timing out en route.
        mode="objective-rally";
        bc::bitboard goals;goals.clear();goals.draw_chebyshev(objective_stage,2.0f);
        goals&=~w.static_blocked;goals&=~w.camp_tiles_all;
        if(!bit(goals,pos))walk_toward(goals);
        return true;
    }
    int best=-1;float key=-1;
    const float power=std::max(1.0f,my_dps(nullptr)*local);
    for(int gi:objective_cluster){auto& g=w.groups[gi];if(group_capture_covered(g))continue;
        const int wait=g.state==GroupState::respawning?std::max(0,g.respawn_round-round):0;
        const float score=g.gems/(capture_time+4.0f+wait+g.hp_left(w.camps)/power);
        if(score>key){key=score;best=gi;}}
    if(best<0){mode="objective-guard";return true;}
    auto& g=w.groups[best];target_group=best;write_claim(best);
    if(g.state==GroupState::alive){mode="objective-clear";return fight_camps(g,g.harmless?1:local);}
    if(g.state==GroupState::reward){
        mode="objective-capture";
        if(!bit(g.tiles,pos))walk_toward(g.tiles);
        return true;
    }
    // Vacate spawn tiles to allow the group to respawn, keeping the team in the same region.
    mode="objective-reset";
    bc::bitboard ring;ring.clear();for(int ci:g.camps)ring.draw_chebyshev(w.camps[ci].pos,3.0f);
    ring&=~w.camp_tiles_all;ring&=~w.static_blocked;
    if(!bit(ring,pos))walk_toward(ring);
    return true;
}
#else
bool Bot::resource_team_objective(){return false;}
#endif
