// A crew has one stable clearing job. Followers read that job even when the
// leader is outside vision. Reward handoff only happens with a visible capturer
// actually on the region, so an absent designated carry cannot strand rewards.
#include "bot.h"

bool Bot::v67_team_farm() {
    if(avoid_until.size()!=w.groups.size())avoid_until.assign(w.groups.size(),0);
    if(field_calls==0)return false;
    using ct=bc::champion_type;
    auto crew=[&](int s) {
        if(team_size<=3)return 0;
        const auto t=slot_type[s];
        return t==ct::vesper_vale||t==ct::heart_of_ruin||t==ct::vendetta?0:1;
    };
    const int mine=crew(slot);
    int leader=-1,rank=-1;
    for(int s=0;s<std::min(team_size,6);++s) if(team67_[s].alive&&crew(s)==mine) {
        const auto t=slot_type[s];
        const int r=t==ct::heart_of_ruin?5:t==ct::varg?4:t==ct::vendetta?3:t==ct::ryth?2:1;
        if(r>rank)rank=r,leader=s;
    }
    auto valid=[&](int g) {return g>=0&&g<static_cast<int>(w.groups.size())&&!w.groups[g].camps.empty();};
    auto distance_to=[&](int g,vec2 origin) {
        if(w.has_field(g))return int(w.group_distance(g,origin));
        int d=999;for(int ci:w.groups[g].camps)d=std::min(d,cheb(origin,w.camps[ci].pos));
        return d;
    };
    auto capturer=[&](int gi) {
        const auto& g=w.groups[gi];
        if(g.state!=GroupState::reward)return -1;
        int owner=-1;
        for(int s=0;s<std::min(team_size,6);++s) {
            const auto& a=team67_[s];
            if(!a.alive||!a.exact||!bit(g.tiles,a.pos))continue;
            if(owner<0||slot_type[s]==ct::vesper_vale)owner=s;
        }
        return owner;
    };
    auto usable=[&](int gi) {
        if(!valid(gi)||avoid_until[gi]>round)return false;
        const auto& g=w.groups[gi];
        if(g.gold==0&&g.gems==0)return false;
        const int d=distance_to(gi,pos);
        if(d==kUnreach)return false;
        if(g.state==GroupState::respawning&&g.respawn_round-round-d>7)return false;
        const int owner=capturer(gi);
        return owner<0||owner==slot;
    };
    int job=-1;
    // Finish a capture already occupied by us before following a new clearing job.
    if(usable(target_group)&&w.groups[target_group].state==GroupState::reward&&
       bit(w.groups[target_group].tiles,pos)&&capturer(target_group)==slot)job=target_group;
    if(job<0&&leader>=0&&leader!=slot) {
        const auto& a=team67_[leader];
        if(round-a.job_seen<=4&&usable(a.job))job=a.job;
    }
    // The leader keeps an active clear; it does not rerank every turn as HP and
    // ally visibility fluctuate. Completed/reward-owned jobs release immediately.
    if(job<0&&usable(target_group)&&w.groups[target_group].state==GroupState::alive&&
       distance_to(target_group,pos)<=25)job=target_group;
    if(job<0) {
        float dps=0,pool=0;
        for(int s=0;s<std::min(team_size,6);++s) {
            const auto& a=team67_[s];
            if(!a.alive||crew(s)!=mine)continue;
            if(a.pos.x>=0&&cheb(a.pos,pos)>20)continue;
            const float weight=a.exact?1.0f:0.65f;
            const float splash=slot_type[s]==ct::varg?1.7f:slot_type[s]==ct::heart_of_ruin?1.4f:1.0f;
            dps+=(a.strength+a.focus*0.18f)*splash*weight;
            pool+=(a.exact?a.hp:a.max_hp*0.65f);
        }
        dps=std::max(dps,my_dps(nullptr));pool=std::max(pool,hp);
        float best=0;
        for(int gi=0;gi<static_cast<int>(w.groups.size());++gi) {
            if(!usable(gi))continue;
            const auto& g=w.groups[gi];const int d=distance_to(gi,pos);
            const float clear=g.state==GroupState::reward?0:g.hp_left(w.camps)/std::max(1.0f,dps);
            const float loss=g.strength*clear*0.6f*camp_taken_mult;
            if(loss>pool*0.75f&&!g.harmless)continue;
            const int wait=g.state==GroupState::respawning?std::max(0,g.respawn_round-round-d):0;
            float value=(g.gems+gold_weight()*g.gold)/(d+wait+clear+capture_time+4.0f);
            const auto at=w.camps[g.camps[0]].pos;
            const int home=fdist(w.spawn_field,at);
            if(w.enemy_ready&&home!=kUnreach) {
                const int enemy=fdist(w.enemy_field,at);
                if(enemy!=kUnreach&&home>enemy)value*=0.65f;
            }
            value/=1+loss/std::max(1.0f,pool)*0.5f;
            if(value>best)best=value,job=gi;
        }
    }
    if(!valid(job)) {target_group=-1;write_claim(-1);return false;}
    if(job!=target_group) {
        staging_since=staging_walk_since=-1;my_claim_since=round;
        target_group=job;
    }
    write_claim(job);
    auto& g=w.groups[job];
    if(g.state==GroupState::reward) {
        mode="crew-capture";
        if(bit(g.tiles,pos))return true;
        if(walk_toward(g.tiles))return true;
        if(walk_unreachable)avoid_until[job]=round+100;
        return false;
    }
    if(g.state==GroupState::respawning) {
        mode="crew-respawn";
        // Occupying any spawn tile blocks the entire group's respawn.
        bc::bitboard ring;ring.clear();
        for(int ci:g.camps)ring.draw_chebyshev(w.camps[ci].pos,2.0f);
        ring&=~g.tiles&~w.static_blocked;
        if(!bit(ring,pos))walk_toward(ring);
        return true;
    }
    int arrived=1;float local_dps=my_dps(&g);
    for(int s=0;s<std::min(team_size,6);++s) if(s!=slot&&team67_[s].alive&&crew(s)==mine&&
        team67_[s].job==job&&(team67_[s].onsite||(team67_[s].exact&&distance_to(job,team67_[s].pos)<=5))) {
        ++arrived;local_dps+=team67_[s].strength+team67_[s].focus*0.18f;
    }
    const int distance=distance_to(job,pos);
    if(distance<=5)mark_onsite(job);
    if(arrived<2&&!g.harmless&&distance<=5&&incoming_from_group(g,pos)<=0&&
       g.strength*g.hp_left(w.camps)/std::max(1.0f,local_dps)*0.6f*camp_taken_mult>hp*0.65f) {
        if(staging_since<0)staging_since=round;
        if(round-staging_since<6) {mode="crew-arrive";return true;}
        avoid_until[job]=round+12;target_group=-1;write_claim(-1);return false;
    }
    mode="crew-clear";
    return fight_camps(g,1);
}
