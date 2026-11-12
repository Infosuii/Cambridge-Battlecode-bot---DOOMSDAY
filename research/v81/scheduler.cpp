// Event-based coalition auction. Existing combat, shopping, banking, camp combat, vision and field building remain intact.
#include "bot.h"
#include <cmath>
#if V82_SCHEDULE
int Bot::scheduled_farm() {
    // Compact on-site protocol is exact in this domain. Larger maps use the unchanged control.
    if(round>300 || team_size>6 || w.groups.size()>kOnsiteGroups || w.groups.empty()) return -1;
    constexpr int READY=124;
    shared=read_shared(); decode_claims();
    const int ns=std::min(team_size,6),ng=static_cast<int>(w.groups.size());
    int task[6];float power[6],health[6];bool known[6]={};
    vec2 spawn=w.spawn_tiles.empty()?pos:w.spawn_tiles[w.spawn_tiles.size()/2];
    for(int s=0;s<ns;++s) {
        task[s]=claim_of(s);
        if(schedule_last[s]>=0 && schedule_last[s]<ng) schedule_pos[s]=w.camps[w.groups[schedule_last[s]].camps[0]].pos;
        else schedule_pos[s]=spawn;
        power[s]=std::max(30.0f,strength+focus*0.125f);health[s]=max_hp*0.8f;
        if(task[s]>=0 && task[s]<ng) schedule_last[s]=task[s],known[s]=true;
        else if(schedule_last[s]>=0) known[s]=true;
    }
    for(const auto& a:w.allies) for(int s=0;s<ns;++s) if(ally_handle[s]==a.id) {
        schedule_pos[s]=a.pos;power[s]=a.strength*1.125f+a.focus*0.25f;health[s]=a.hp;known[s]=true;
    }
    schedule_pos[slot]=pos;power[slot]=my_dps(nullptr);health[slot]=hp;known[slot]=true;
    // An explicit ready message is sent only after this champion has actually reached the farming stage.
    if(task[slot]<0 || task[slot]>=ng) task[slot]=READY;
    if(task[slot]>=0 && task[slot]<ng) {
        const int gi=task[slot];const auto& g=w.groups[gi];
        const int dist=w.has_field(gi)?w.group_distance(gi,pos):cheb(pos,w.camps[g.camps[0]].pos);
        const float left=g.hp_left(w.camps);
        if(gi!=schedule_watch_job) {
            schedule_watch_job=gi;schedule_watch_dist=dist;schedule_watch_hp=left;schedule_watch_round=round;
        } else if(dist<schedule_watch_dist || left<schedule_watch_hp) {
            schedule_watch_round=round;schedule_watch_dist=std::min(schedule_watch_dist,dist);schedule_watch_hp=std::min(schedule_watch_hp,left);
        }
        // A durable job must have an execution progress contract. The diagnostic exposed Cassi circling an unseen
        // corner gold cluster for 200 rounds after the planner had priced a short clear. Release infeasible work.
        if(dist==kUnreach || round-schedule_watch_round>std::max(12,capture_time+6)) {
            avoid_until[gi]=round+std::max(g.respawn,40);task[slot]=READY;schedule_watch_job=-1;
        }
    } else schedule_watch_job=-1;
    unsigned ready=0;
    for(int s=0;s<ns;++s) {
        if(task[s]>=0 && task[s]<ng) {
            const auto& g=w.groups[task[s]];
            if(g.state==GroupState::respawning) task[s]=READY;
        }
    }
    // A finished clear needs one capturer. Release other workers immediately, without forcing a carry to travel.
    for(int gi=0;gi<ng;++gi) if(w.groups[gi].state==GroupState::reward) {
        int owner=-1;
        for(int s=0;s<ns;++s) if(task[s]==gi) {
            if(owner<0 || (bit(w.groups[gi].tiles,schedule_pos[s]) && !bit(w.groups[gi].tiles,schedule_pos[owner]))) owner=s;
        }
        for(int s=0;s<ns;++s) if(task[s]==gi && s!=owner) task[s]=READY;
    }
    for(int s=0;s<ns;++s) if(task[s]==READY && known[s]) ready|=1u<<s;
    // Initial readiness handshake prevents the first actor from greedily taking a solo job before peers publish.
    if(round<2) ready=0;
    bool occupied[48]={};
    for(int s=0;s<ns;++s) if(task[s]>=0 && task[s]<ng) occupied[task[s]]=true;
    int allocated=0;
    for(int auction=0;auction<ns && ready && bc::fuel_remaining()>45000;++auction) {
        int best_g=-1;unsigned best_mask=0;float best_rate=0;
        for(int gi=0;gi<ng;++gi) {
            if(bc::fuel_remaining()<44000) break;
            const auto& g=w.groups[gi];
            if(occupied[gi] || g.camps.empty() || avoid_until[gi]>round || g.state==GroupState::respawning) continue;
            const float hp_left=g.hp_left(w.camps);
            int distance[6];
            for(int s=0;s<ns;++s) distance[s]=(ready&(1u<<s))?
                (w.has_field(gi)?w.group_distance(gi,schedule_pos[s]):cheb(schedule_pos[s],w.camps[g.camps[0]].pos)):kUnreach;
            // Every available coalition is priced in total worker-turns. This permits parallel singles/pairs and
            // a larger crew only when the shared clear pays more than its extra travel and time.
            for(unsigned mask=ready;mask;mask=(mask-1)&ready) {
                if(bc::fuel_remaining()<42000) break;
                int count=0,travel=0,first=kUnreach;float dps=0,pool=0;
                for(int s=0;s<ns;++s) if(mask&(1u<<s)) {
                    ++count;travel=std::max(travel,distance[s]);first=std::min(first,distance[s]);dps+=power[s];pool+=health[s];
                }
                if(travel==kUnreach || travel-first>6) continue;
                if(g.state==GroupState::reward && count>1) continue;
                const float clear=hp_left/std::max(1.0f,dps*camp_dealt_mult);
                if(!g.harmless && group_soak(g,dps)*camp_taken_mult>pool*0.8f) continue;
                const float cost=count*(std::max(0,travel-range)+clear)+capture_time;
                const float value=static_cast<float>(g.gold+g.gems);
                const float rate=value/std::max(1.0f,cost);
                if(rate>best_rate) best_rate=rate,best_g=gi,best_mask=mask;
            }
        }
        if(best_g<0) break;
        for(int s=0;s<ns;++s) if(best_mask&(1u<<s)) task[s]=best_g;
        ready&=~best_mask;occupied[best_g]=true;++allocated;
    }
    // Publish the whole joint assignment atomically, preserving the independent sighting bits.
    std::uint64_t command=read_shared();
    for(int s=0;s<ns;++s) {
        int code=task[s];
        if(code<0) code=kClaimCodeIdle;
        if(task[s]>=0 && task[s]<ng && claim_onsite(s) && claim_of(s)==task[s]) code+=kOnsiteBase;
        command&=~(kClaimMask<<(s*kClaimBits));command|=static_cast<std::uint64_t>(code)<<(s*kClaimBits);
    }
    bc::shared_memory.write(0,std::span<std::uint64_t,1>{&command,1});shared=command;decode_claims();
    const int job=task[slot];
#if V82_DIAG
    if(allocated || round%50==0) std::printf("SC %d %d job %d alloc %d ready %u fuel %llu\n",round,slot,job,allocated,ready,
        static_cast<unsigned long long>(bc::fuel_remaining()));
#endif
    if(job<0 || job>=ng) {mode="schedule-ready";return 1;}
    auto& g=w.groups[job];
    if(target_group!=job) staging_since=-1,staging_walk_since=-1,my_claim_since=round;
    target_group=job;write_claim(job);
    int crew=0;for(int s=0;s<ns;++s) crew+=task[s]==job;
    if(g.state==GroupState::alive) return fight_camps(g,std::max(1,crew))?1:0;
    if(g.state==GroupState::reward) {
        mode="schedule-capture";
        if(!bit(g.tiles,pos)) walk_toward(g.tiles);
        return 1;
    }
    return 1;
}
#else
int Bot::scheduled_farm(){return -1;}
#endif
