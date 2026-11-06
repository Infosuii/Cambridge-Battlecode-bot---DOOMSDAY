// EXP291 ordinary-task selector. Private remembered state only; legacy execution follows.
int Bot::codex_task_pick(int& best_need,float& best_score) {
    best_need=1;best_score=0;
    const int count=static_cast<int>(w.groups.size());
    const int prior=target_group;
    int pin=-1;
#if CODEX_TASK_MODE >= 2
    if(prior>=0&&prior<count&&codex_task_group==prior&&codex_task_round+1==round&&avoid_until[prior]<=round){
        const auto& g=w.groups[prior];const float remaining=g.hp_left(w.camps);
        if(g.state==GroupState::alive&&remaining<codex_task_hp&&w.group_distance(prior,pos)<=range+1){
            const int required=champions_needed(g,remaining);
            if(required<=team_size&&(required==1||1+allies_near_group(g)>=required)){
                best_need=required;best_score=1e9f;
                codex_task_group=prior;codex_task_need=required;codex_task_round=round;codex_task_hp=remaining;
                return prior;
            }
        }
    }
#endif
    int best=-1;
    for(int gi=0;gi<count;++gi){
        if(pin>=0&&gi!=pin)continue;
        const std::uint64_t floor=tune::kDet?static_cast<std::uint64_t>(tune::kDetSafety)+10000:tune::kLowFuel;
        if(bc::fuel_remaining()<floor+8192)break;
        const auto& g=w.groups[gi];if(g.camps.empty()||avoid_until[gi]>round)continue;
        const int distance=w.group_distance(gi,pos);if(distance==kUnreach)continue;
        const float remaining=g.state==GroupState::alive?g.hp_left(w.camps):g.state==GroupState::respawning?g.max_hp:0.0f;
        const int required=g.state==GroupState::reward?1:champions_needed(g,remaining);
        if(required>team_size||required<1)continue;
#if CODEX_TASK_MODE >= 2
        if(g.state==GroupState::reward){
            const bool on=bit(g.tiles,pos);bool ally_on=false;
            for(const auto& a:w.allies)if(bit(g.tiles,a.pos)){ally_on=true;break;}
            if(on||ally_on){
                d::camp_group_capture_state capture{};
                if(d::sdk_camp_group_capture_state(g.handle,&capture)==0&&capture.state==1){
                    if(on){best=gi;best_need=1;best_score=1e9f;break;}
                    if(ally_on)continue; // actual same-team progress acknowledges a collector
                }
            }
        }
#endif
        const int seniors=gi==prior?senior_claims(gi):claim_count(gi);
        if(g.state!=GroupState::reward&&gi!=pin&&seniors>=required)continue;
        const float dps=std::max(1.0f,my_dps(&g));
        const float clear_work=remaining/dps;
        const int approach=std::max(0,distance-(g.state==GroupState::alive?range:0));
        const int wait=g.state==GroupState::respawning?std::max(0,g.respawn_round-round-approach):0;
        float value=static_cast<float>(g.gems)+CODEX_TASK_GOLD*gold_weight()*static_cast<float>(g.gold);
        if(round-g.enemy_round<15)value*=UB_ENEMY_CAMP;
        if(NOVA_SEED>0){
            std::uint32_t hs=static_cast<std::uint32_t>(NOVA_SEED)*2654435761u^static_cast<std::uint32_t>(gi)*40503u^
                static_cast<std::uint32_t>(round/20)*2246822519u^static_cast<std::uint32_t>(slot+1)*3266489917u;
            hs^=hs>>15;hs*=2246822519u;hs^=hs>>13;
            value*=1.0f+NOVA_SEED_EPS*(static_cast<float>(hs&0xffffu)/32767.5f-1.0f);
        }
        float health_fraction=0;
        if(!g.harmless&&g.state!=GroupState::reward){
            const float incoming=soak_coefficient(gi,remaining)*camp_taken_mult/(dps*static_cast<float>(required));
            const float pool=hp+static_cast<float>(required-1)*max_hp*.7f;
            health_fraction=incoming/std::max(1.0f,pool);
        }
        const float cost=(static_cast<float>(required)*CODEX_TASK_CREW*static_cast<float>(approach+wait+capture_time)+clear_work+1.0f)*
            (1.0f+CODEX_TASK_RISK*health_fraction);
        float score=value/std::max(1.0f,cost);
        if(gi==prior)score*=CODEX_TASK_STICKY;
        if(!std::isfinite(score))continue;
        if(score>best_score){best=gi;best_need=required;best_score=score;}
    }
    codex_task_group=best;codex_task_need=best_need;codex_task_round=round;
    codex_task_hp=best>=0?w.groups[best].hp_left(w.camps):0;
    return best;
}
