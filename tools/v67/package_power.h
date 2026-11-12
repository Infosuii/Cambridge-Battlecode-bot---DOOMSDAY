// Count the same two-turn arrival horizon on both teams. Distant visible enemies
// should not count as immediate full-health/full-damage fighters while equally
// distant allies count as zero. Gap ranges come from public immutable metadata;
// readiness is queried only for currently visible champions (or ourselves).
namespace {
int ready_gap67(std::uint32_t id, bc::champion_type type) {
    struct Entry { bool loaded=false; int reach[2]={0,0}; };
    static std::array<Entry,16> table{};
    const int t=static_cast<int>(type);
    if(t<0||t>=16)return 0;
    auto& entry=table[t];
    if(!entry.loaded) {
        entry.loaded=true;
        try {
            const auto abilities=bc::champion{type}.abilities();
            for(int s=0;s<2;++s) if(const auto& info=abilities[s].info();info) {
                if(const auto* dash=std::get_if<bc::ability_dash>(&*info))entry.reach[s]=static_cast<int>(dash->range);
            }
        } catch(...) {}
    }
    int gap=0;
    for(unsigned s=0;s<2;++s) if(entry.reach[s]>0) {
        std::int32_t cooldown=99;
        if(!cambc::detail::sdk_champion_cooldown(id,s,&cooldown)&&cooldown==0)
            gap=std::max(gap,entry.reach[s]);
    }
    return gap;
}
float contact_weight67(int distance,int range,int gap) {
    const int eta=std::max(0,distance-range-gap);
    return eta==0?1.0f:eta==1?0.75f:eta==2?0.5f:0.0f;
}
}
