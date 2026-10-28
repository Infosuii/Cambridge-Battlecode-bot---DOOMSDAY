// Economic control of valuable capture regions that span both spawn areas.
#include "bot.h"
#if V84_DENIAL
bool Bot::deny_income_region() {
    if(bc::fuel_remaining()<26000 || gems>0 || hp<max_hp*0.5f) return false;
    if(denial_group==-2) {
        denial_group=-1;
        // Cassi and Issac are two bodies for one draft pick. Otherwise the earliest slots guard.
        int jobs[6],n=0; vec2 anchors[6];
        const auto enemy=w.enemy_spawn.positions();
        if(enemy.empty())return false;
        for(std::size_t gi=0;gi<w.groups.size() && n<6;++gi) {
            const auto& g=w.groups[gi];
            if(!g.harmless || g.gems || g.gold<100u || g.camps.size()<8)continue;
            int home=999,foe=999;vec2 anchor{-1,-1};
            for(int ci:g.camps){const vec2 p=w.camps[ci].pos;
                const int dh=fdist(w.spawn_field,p);
                if(dh<home){home=dh;anchor=p;}
                for(vec2 e:enemy)foe=std::min(foe,cheb(e,p));
            }
            // Only shared regions with a safe home endpoint; compact enemy camps do not qualify.
            if(home>5 || foe>5 || anchor.x<0)continue;
            jobs[n]=static_cast<int>(gi);anchors[n++]=anchor;
        }
        if(slot<n && n<=team_size/2){denial_group=jobs[slot];denial_anchor=anchors[slot];}
    }
    if(denial_group<0)return false;
    auto& g=w.groups[denial_group];
    // A living camp cannot be occupied. Clear the home endpoint first with the mature executor.
    const int ci=w.group_of_camp_tile(denial_anchor);
    if(ci<0)return false;
    const auto& camp=w.camps[ci];
    target_group=denial_group;write_claim(denial_group);
    if(g.state==GroupState::alive && !camp.dead){
        if(bit(w.visible,camp.pos) && cheb(camp.pos,pos)<=range){
            mode="deny-clear";cast_on_camp(ci);
            if(attack_unit(camp.camp,camp.pos))use_reset_and_attack(camp.camp,camp.pos);
            return true;
        }
        bc::bitboard goal;goal.clear();goal.draw_chebyshev(denial_anchor,static_cast<float>(range));
        goal.set(denial_anchor,false);mode="deny-approach";walk_toward(goal);return true;
    }
    if(pos!=denial_anchor){bc::bitboard goal;goal.clear();goal.set(denial_anchor,true);mode="deny-position";walk_toward(goal);return true;}
    // On a reward this contests/picks it up; during cooldown it prevents the whole region respawning.
    // We intentionally value denying the opponent's repeated 600-gold amplification over our own payout.
    mode="deny-income";
    opportunistic_attack();
    return true;
}
#else
bool Bot::deny_income_region(){return false;}
#endif
