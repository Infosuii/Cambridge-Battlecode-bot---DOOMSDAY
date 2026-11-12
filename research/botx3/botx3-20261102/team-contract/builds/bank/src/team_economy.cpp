#include "bot.h"
#if X3_TEAM
#include "team_scheduler.h"

namespace {
constexpr int draft_offset=480, draft_size=512;
std::uint16_t static_signature(const World& w) {
    std::uint32_t h=w.width*131u+w.height;
    for (const auto& g:w.groups) h=(h*16777619u)^g.handle^(g.gems<<8)^g.gold;
    return static_cast<std::uint16_t>(h);
}
}

void team_economic_draft() {
    static bool ready=false;
    if (ready || bc::constants::draft_memory_bytes<1024 || bc::fuel_remaining()<1000000) return;
    const auto before=bc::fuel_remaining();
    World world;world.init();
    if (world.groups.size()>126 || !world.ensure_altar_field()) {ready=true;return;}
    std::array<std::uint8_t,1024> memory{};
    bc::detail::check(bc::detail::sdk_read_draft_memory(0,memory.data(),memory.size()));
    auto* p=memory.data()+draft_offset;
    p[0]=0xD3;p[1]=1;p[2]=static_cast<std::uint8_t>(world.groups.size());p[3]=0;
    const auto sig=static_signature(world);p[4]=sig&255;p[5]=sig>>8;p[6]=world.width;p[7]=world.height;
    for (int gi=0;gi<static_cast<int>(world.groups.size());++gi) {
        int bank=kUnreach,home=kUnreach;
        for (int ci:world.groups[gi].camps) {
            const auto pos=world.camps[ci].pos;
            bank=std::min(bank,static_cast<int>(fdist(world.altar_field,pos)));
            home=std::min(home,static_cast<int>(fdist(world.spawn_field,pos)));
        }
        p[8+4*gi]=bank&255;p[9+4*gi]=(bank>>8)&255;
        p[10+4*gi]=home&255;p[11+4*gi]=(home>>8)&255;
    }
    bc::draft_memory=memory;ready=true;
#if X3_TRACE
    std::printf("X3_DRAFT groups%zu bytes%d fuel%llu\n",world.groups.size(),draft_size,
        static_cast<unsigned long long>(before-bc::fuel_remaining()));
#else
    (void)before;
#endif
}

void Bot::team_economic_init() {
    if (bc::draft_memory.size()<draft_offset+draft_size) return;
    const auto* p=reinterpret_cast<const std::uint8_t*>(bc::draft_memory.data())+draft_offset;
    const auto sig=static_signature(w);
    if (p[0]!=0xD3 || p[1]!=1 || p[2]!=w.groups.size() || (p[4]|(p[5]<<8))!=sig || p[6]!=w.width || p[7]!=w.height) return;
    x3_bank_distance.resize(w.groups.size());
    for (int gi=0;gi<static_cast<int>(w.groups.size());++gi) x3_bank_distance[gi]=p[8+4*gi]|(p[9+4*gi]<<8);
#if X3_TRACE
    std::printf("X3_DRAFT_READ slot%d groups%zu\n",slot,x3_bank_distance.size());
#endif
}

int Bot::team_economic_assignment(int& need) {
    using namespace team_scheduler;
#if X3_TEAM >= 9
    // Keep both control values in initialized data, preserving identical code and
    // memory layout across the factorial arms (zero-in-BSS changed addresses).
    static volatile int enable_race=X3_TEAM_RACE+1,enable_farm=X3_TEAM_FARM+1;
    const bool race_due=enable_race>1 && ally_score+team_size*tune::kTributeCarry>=static_cast<int>(bc::constants::winning_gems);
#else
    const bool race_due=false;
#endif
    if (X3_TEAM==6) return -1; // transport/draft ablation, no team auction
    if (slot>=workers || team_size>workers || round-last_flee_round<10) return -1;
#if X3_TEAM >= 11
    if (team_size>=kClaimSlots) return -1; // no spare claim slot: keep the original protocol and policy
#endif
#if X3_TEAM >= 5
    if (x3_dominant_group==-2) {
        x3_dominant_group=-1;float total=0;
        for (const auto& g:w.groups) total+=g.gems;
        for (int gi=0;gi<static_cast<int>(w.groups.size());++gi)
            if (total>0 && w.groups[gi].gems>=0.9f*total) x3_dominant_group=gi;
    }
    if (x3_dominant_group>=0 && round>=A2_SOLE_FROM && !race_due) return -1;
#endif
#if X3_TEAM >= 4
    if (w.groups.size()>112) return -1; // keep the legacy fight/onsite encodings disjoint
    int leader=0;
    for (;leader<team_size;++leader) {
        std::int32_t alive=0;
        bc::detail::check(bc::detail::sdk_champion_is_alive(ally_handle[leader],&alive));
        if (alive) break;
    }
    shared=read_shared();decode_claims();
#if X3_TEAM >= 10
    const int age=round-x3_assignment_round;
    const bool leased=x3_assignment_round>=0 && age<8;
    if (slot!=leader || !x3_prepare || (leased && !race_due)) {
        if (slot==leader && !leased) return -1;
#else
    const int age=(round-static_cast<int>((shared>>42)&262143)+262144)&262143;
    const bool leased=(shared>>63) && static_cast<int>((shared>>60)&7)==leader && age<8;
    if ((leased && !(x3_prepare && race_due)) || slot!=leader) {
        if (!leased) return -1;
#endif
        const int command=claim_of(slot);
#if X3_TEAM >= 10
#if X3_TEAM >= 11
        const bool pending=((shared>>(35+slot))&1)!=0;
        if (pending) {x3_received_command=command;x3_received_round=round;}
        if (slot!=leader && !pending && (command!=x3_received_command || round-x3_received_round>=8)) return -1;
#else
        if (command!=x3_received_command) {x3_received_command=command;x3_received_round=round;}
        if (slot!=leader && command!=125 && round-x3_received_round>=8) return -1;
#endif
#endif
#if X3_TRACE
        if (round%10==0) std::printf("X3_APPLY R%d slot%d captain%d command%d age%d\n",round,slot,leader,command,age);
#endif
        if (command==125 && gems>0) return -3;
        if (command>=0 && command<static_cast<int>(w.groups.size()) && avoid_until[command]<=round) {
            const auto& g=w.groups[command];
            if (g.state!=GroupState::respawning || g.respawn_round<=round+5) {
                need=1;
                if (g.state==GroupState::alive) for (int s=0;s<team_size;++s) if (s!=slot && claim_of(s)==command) ++need;
                return command;
            }
        }
        return -1;
    }
#if X3_TEAM >= 7
    if (!x3_prepare) return -1; // compute only after this turn's essential actions
#endif
#endif
    // Preserve a real capture, including when a fresh auction sees richer jobs.
    if (target_group>=0 && target_group<static_cast<int>(w.groups.size())) {
        const auto& g=w.groups[target_group];
        if (g.state==GroupState::reward && bit(g.tiles,pos) && !group_capture_covered(g)) {
            need=1;return target_group;
        }
    }
#if X3_TEAM == 3
    if (x3_assignment_round>=0 && round-x3_assignment_round<8 && x3_assignment<0) return x3_assignment;
#endif
    if (X3_TEAM<4 && x3_assignment_round>=0 && round-x3_assignment_round<8 && x3_assignment>=0 &&
        x3_assignment<static_cast<int>(w.groups.size()) && avoid_until[x3_assignment]<=round &&
        w.groups[x3_assignment].state!=GroupState::respawning) {
        need=x3_crew;return x3_assignment;
    }
    if (bc::fuel_remaining()<(race_due ? 20000 : X3_TEAM>=3 ? 75000 : 60000) || !w.altar_ready) return -1;
    const auto fuel_before=bc::fuel_remaining();
    std::array<Actor,workers> actor{};
    std::array<vec2,workers> place{};
    actor[slot]={true,hp,my_dps(nullptr),gems,fdist(w.altar_field,pos),tune::kTributeCarry,target_group,-1};
    place[slot]=pos;
    unsigned visible=1u<<slot;
#if X3_TEAM >= 7
    const auto current_view=bc::vision::champion_tiles();
#endif
    for (int s=0;s<std::min(team_size,workers);++s) if (s!=slot) {
        for (const auto& a:w.allies) if (a.id==ally_handle[s] && a.hp>0) {
#if X3_TEAM >= 7
            if (!bit(current_view,a.pos)) break; // own movement may have changed personal vision
#endif
            // These queries are made only for an ally already in personal vision.
            const int bag=a.unit.gem_count();
            const auto state=a.unit.state();
            if (state.contains(bc::champion_state::recalling) || state.contains(bc::champion_state::submitting_gems) ||
                state.contains(bc::champion_state::teleporting)) break;
            actor[s]={true,a.hp,std::max(1.0f,a.strength*1.125f+a.focus*0.125f),bag,
                fdist(w.altar_field,a.pos),tune::kTributeCarry,claim_of(s),-1};
            place[s]=a.pos;visible|=1u<<s;
            const int c=claim_of(s);
            if (c>=0 && c<static_cast<int>(w.groups.size()) && w.groups[c].state==GroupState::reward && bit(w.groups[c].tiles,a.pos)) actor[s].fixed=c;
            break;
        }
    }
#if X3_TEAM >= 9
    if (race_due) {
        const unsigned banking=bank_cohort(actor,static_cast<int>(bc::constants::winning_gems)-ally_score);
        if (banking) {
            std::uint64_t word=read_shared();
#if X3_TEAM < 10
            word&=((std::uint64_t{1}<<42)-1);
#endif
            for (int s=0;s<workers;++s) if (banking&(1u<<s))
                word=(word&~(kClaimMask<<(s*kClaimBits))) | (std::uint64_t{125}<<(s*kClaimBits));
#if X3_TEAM >= 11
            for (int s=0;s<team_size;++s) if (banking&(1u<<s)) word|=std::uint64_t{1}<<(35+s);
#endif
#if X3_TEAM < 10
            word|=(static_cast<std::uint64_t>(round&262143)<<42) | (static_cast<std::uint64_t>(leader)<<60) | (std::uint64_t{1}<<63);
#endif
            bc::shared_memory.write(0,std::span<std::uint64_t,1>{&word,1});shared=word;decode_claims();
            x3_assignment_round=round;
#if X3_TRACE
            std::printf("X3_RACE R%d captain%d remaining%d mask%u\n",round,leader,static_cast<int>(bc::constants::winning_gems)-ally_score,banking);
#endif
            need=1;return (banking&(1u<<slot)) ? -3 : -1;
        }
    }
    if (enable_farm<2 || leased || (x3_dominant_group>=0 && round>=A2_SOLE_FROM) || bc::fuel_remaining()<75000) return -1;
#endif
#if X3_TEAM >= 3
    if ((visible&(visible-1))==0 && gems<tune::kTributeCarry) return -1;
#endif
    struct Candidate {int gi=-1;float rate=0;};
    std::array<Candidate,jobs> top{};int nt=0;
    constexpr int job_limit=X3_TEAM>=3 ? 6 : jobs;
    for (int gi=0;gi<static_cast<int>(w.groups.size());++gi) {
        if ((gi&7)==0 && bc::fuel_remaining()<52000) break;
        const auto& g=w.groups[gi];
        if (g.camps.empty() || !w.has_field(gi) || avoid_until[gi]>round) continue;
        // An unseen teammate's position/health is unknown. Keep its reservation.
        bool held=false;
        for (int s=0;s<std::min(team_size,workers);++s) if (!(visible&(1u<<s)) && claim_of(s)==gi) held=true;
        if (held || group_capture_covered(g)) continue;
        int dist=kUnreach;
        for (int s=0;s<workers;++s) if (actor[s].available) dist=std::min(dist,w.group_distance(gi,place[s]));
        if (dist==kUnreach) continue;
        const int wait=g.state==GroupState::respawning ? std::max(0,g.respawn_round-round-dist) : 0;
        const float value=g.gems+gold_weight()*g.gold;
        const float rate=value/(dist+wait+5+g.hp_left(w.camps)/std::max(1.0f,my_dps(nullptr)));
        Candidate c{gi,rate};
        for (int k=0;k<job_limit;++k) if (c.rate>top[k].rate) std::swap(c,top[k]);
    }
    std::array<Job,jobs> job{};
    for (const auto& c:top) {
        if (c.gi<0 || bc::fuel_remaining()<45000) break;
        const auto& g=w.groups[c.gi];
        Job j;j.id=c.gi;j.hp=g.hp_left(w.camps);j.gems=g.gems;j.gold_value=gold_weight()*g.gold;
        j.soak=g.harmless || g.state==GroupState::reward ? 0 : soak_coefficient(c.gi,j.hp)*camp_taken_mult;
        j.ready=g.state==GroupState::respawning ? std::max(0,g.respawn_round-round) : 0;
        j.capture=capture_time;
        if (x3_bank_distance.size()==w.groups.size()) j.bank_distance=x3_bank_distance[c.gi];
        else for (int ci:g.camps) j.bank_distance=std::min(j.bank_distance,static_cast<int>(fdist(w.altar_field,w.camps[ci].pos)));
        for (int s=0;s<workers;++s) {
            j.travel[s]=actor[s].available ? w.group_distance(c.gi,place[s]) : unreachable;
            if (j.travel[s]==kUnreach) j.travel[s]=unreachable;
        }
        for (const auto& e:w.enemies) for (int ci:g.camps) if (cheb(e.pos,w.camps[ci].pos)<=6) {
            j.risk*=0.65f;break;
        }
        job[nt++]=j;
    }
    const auto result=assign(actor,job.data(),nt);
#if X3_TEAM >= 4
    std::uint64_t word=read_shared();
#if X3_TEAM < 10
    word&=((std::uint64_t{1}<<42)-1);
#endif
    for (int s=0;s<workers;++s) if (visible&(1u<<s)) {
        const int target=result.target[s];
        std::uint64_t code=target>=0 ? target : target==bank ? 125 : kClaimCodeIdle;
        if (target>=0 && onsite_ok && target<kOnsiteGroups && claim_of(s)==target && claim_onsite(s)) code=kOnsiteBase+target;
        word=(word&~(kClaimMask<<(s*kClaimBits))) | (code<<(s*kClaimBits));
#if X3_TEAM >= 11
        word|=std::uint64_t{1}<<(35+s);
#endif
    }
#if X3_TEAM < 10
    word|=(static_cast<std::uint64_t>(round&262143)<<42) | (static_cast<std::uint64_t>(leader)<<60) | (std::uint64_t{1}<<63);
#endif
    bc::shared_memory.write(0,std::span<std::uint64_t,1>{&word,1});shared=word;decode_claims();
#if X3_TRACE
    std::printf("X3_ORDER R%d captain%d targets%d,%d,%d,%d,%d,%d\n",round,leader,
        result.target[0],result.target[1],result.target[2],result.target[3],result.target[4],result.target[5]);
#endif
#endif
    x3_assignment=result.target[slot];x3_crew=result.crew[slot];x3_assignment_round=round;
    need=x3_crew;
#if X3_TRACE
    std::printf("X3_TEAM R%d slot%d visible%u jobs%d bids%d assigned%d crew%d fuel%llu\n",round,slot,visible,nt,
        result.bids,x3_assignment,need,static_cast<unsigned long long>(fuel_before-bc::fuel_remaining()));
#else
    (void)fuel_before;
#endif
    return x3_assignment;
}
#endif
