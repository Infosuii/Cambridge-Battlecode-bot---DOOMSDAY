#pragma once
#include "gx_mint.h"
#if GX_MINT
namespace gx_mint {
struct CampJob {
    bc::bitboard tiles;
    int id, gold, gems, home;
    float hp, soak;
};
inline int distance(const bc::distance_field& field,const bc::bitboard& tile) {
    int best=kUnreach;
    for (auto q : tile.positions()) best=std::min(best,static_cast<int>(fdist(field,q)));
    return best;
}
inline std::vector<std::uint8_t> make() {
    namespace d=bc::detail;
    std::uint32_t n=0;
    if (d::sdk_map_num_camp_groups(&n)!=0 || n<3 || n>64 || bc::constants::draft_memory_bytes<kBytes) return {};
    std::vector<std::uint32_t> handles(n);
    if (d::sdk_map_camp_groups(handles.data(),n,&n)!=0) return {};
    const auto home=bc::map::spawn_region(team::ally), enemy=bc::map::spawn_region(team::enemy);
    const auto terrain=bc::map::walls() | bc::map::holes() | bc::map::altars();
    bc::bitboard visited;
    bc::distance_field hf,ef;
    hf.compute(terrain|enemy,home,visited);
    ef.compute(terrain|home,enemy,visited);
    std::vector<CampJob> jobs;
    d::camp_design designs[16]{};
    bool known[16]{};
    for (std::uint32_t k=0;k<n && bc::fuel_remaining()>1500000;++k) {
        d::camp_group_info g{};
        std::uint32_t m=0, ids[12];
        if (d::sdk_map_camp_group(handles[k],&g)!=0 || g.gold<35 ||
            d::sdk_map_camp_group_num_camps(handles[k],&m)!=0 || m==0 || m>12 ||
            d::sdk_map_camp_group_camps(handles[k],ids,m,&m)!=0) continue;
        bc::bitboard tiles;
        tiles.clear();
        float hp=0,strength=0;
        std::uint32_t ok=0;
        for (std::uint32_t i=0;i<m;++i) {
            d::camp_info c{};
            if (d::sdk_map_camp_info(ids[i],&c)!=0 || c.type<0 || c.type>=16) break;
            if (!known[c.type]) {
                if (d::sdk_camp_design(c.type,&designs[c.type])!=0) break;
                known[c.type]=true;
            }
            const auto& s=designs[c.type].base_stats;
            hp+=s.base_health; strength+=s.base_strength;
            set_bit(tiles,{c.x,c.y});
            ++ok;
        }
        if (ok!=m || hp>1800.0f || hp*strength>18000.0f) continue;
        const int a=distance(hf,tiles),b=distance(ef,tiles);
        if (a>16 || b<a+5) continue;
        jobs.push_back({std::move(tiles),static_cast<int>(k),static_cast<int>(g.gold),static_cast<int>(g.gems),a,hp,hp*strength});
    }
    if (jobs.empty()) return {};
    int dists[64][64];
    for (std::size_t i=0;i<jobs.size();++i) {
        if (bc::fuel_remaining()<1000000) return {};
        bc::distance_field f;
        f.compute(terrain|enemy,jobs[i].tiles,visited,28);
        for (std::size_t j=0;j<jobs.size();++j) dists[i][j]=distance(f,jobs[j].tiles);
    }
    std::vector<std::uint8_t> out(kBytes,0);
    out[kAt]=0xc1;
    for (int role=0;role<3;++role) {
        d::champion_design u{};
        const auto at=kAt+1+5*role;
        out[at]=out[at+1]=255;
        if (d::sdk_champion_design(static_cast<int>(roles[role]),&u)!=0) continue;
        const float dps=std::max(28.0f,u.base_stats.base_strength+0.14f*u.base_stats.base_focus);
        const int req=role==0 ? 115 : 150; // Vesper receives one third more gold, with integer reward rounding.
        Plan best;
        int best_gems=-1;
        for (std::size_t i=0;i<jobs.size();++i) {
            const auto& a=jobs[i];
            const int time1=a.home+static_cast<int>(std::ceil(a.hp/dps))+bc::constants::capture_time+2;
            auto consider=[&](int id,int gold,int time,int gems,int last_home) {
                if (gold<req) return;
                const int trip=role==1 ? 0 : std::min(last_home,bc::constants::recall_time+2);
                const int total=time+trip;
                if (total>58 || (best.first>=0 && (total>best.turns || (total==best.turns && gems<=best_gems)))) return;
                best={a.id,id,std::min(95,total+20),std::min(250,a.gold),total};
                best_gems=gems;
            };
            consider(-1,a.gold,time1,a.gems,a.home);
            if (a.gold>=req) continue;
            for (std::size_t j=0;j<jobs.size();++j) {
                if (i==j || dists[i][j]>11) continue;
                const auto& b=jobs[j];
                const int time2=time1+dists[i][j]+static_cast<int>(std::ceil(b.hp/dps))+bc::constants::capture_time+2;
                consider(b.id,a.gold+b.gold,time2,a.gems+b.gems,b.home);
            }
        }
        if (best.first>=0) {
            out[at]=static_cast<std::uint8_t>(best.first);
            out[at+1]=best.second<0?255:static_cast<std::uint8_t>(best.second);
            out[at+2]=static_cast<std::uint8_t>(best.expires);
            out[at+3]=static_cast<std::uint8_t>(best.first_gold);
            out[at+4]=static_cast<std::uint8_t>(best.turns);
        }
    }
    return out;
}
} // namespace gx_mint
#endif
