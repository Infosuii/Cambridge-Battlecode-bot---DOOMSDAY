#include "bot.h"
#if X3_DRAFT_PATHS
#include <cstdio>

namespace {
constexpr int offset=480, capacity=528, max_groups=64;
std::uint16_t signature(const World& w) {
    std::uint32_t h=w.width*131u+w.height;
    for (const auto& g:w.groups) h=(h*16777619u)^g.handle^(g.gems<<8)^g.gold;
    return static_cast<std::uint16_t>(h);
}
int group_min(const World& w,int gi,const bc::distance_field& f) {
    int d=kUnreach;
    for (int ci:w.groups[gi].camps) d=std::min(d,static_cast<int>(fdist(f,w.camps[ci].pos)));
    return d;
}
// Width of a deterministic shortest banking route, terrain only. Camps/enemies
// are dynamic hazards, so this is geometry metadata, never a safety guarantee.
int bank_width(const World& w,int gi) {
    vec2 pos{-1,-1};int dist=kUnreach,width=8;
    for (int ci:w.groups[gi].camps) {
        const auto p=w.camps[ci].pos;const int d=fdist(w.altar_field,p);
        if (d<dist) {pos=p;dist=d;}
    }
    if (dist==kUnreach) return 0;
    while (dist>0) {
        int degree=0,best=dist;vec2 next=pos;
        for (int dy=-1;dy<=1;++dy) for (int dx=-1;dx<=1;++dx) if (dx || dy) {
            const vec2 q{pos.x+dx,pos.y+dy};
            if (q.x<0 || q.y<0 || q.x>=w.width || q.y>=w.height || bit(w.walk_terrain,q)) continue;
            ++degree;const int d=fdist(w.altar_field,q);
            if (d<best) {best=d;next=q;}
        }
        width=std::min(width,degree);
        if (best==dist) return 0;
        pos=next;dist=best;
    }
    return width;
}
}

void draft_paths_prepare() {
    static bool done=false;
    if (done || bc::fuel_remaining()<1000000) return;
    done=true;
    if (X3_TEAM || A2_DPLAN || V58_DIRECTOR || bc::constants::draft_memory_bytes<1024) return;
    const auto before=bc::fuel_remaining();
    World w;w.init();
    const int n=static_cast<int>(w.groups.size());
    if (n<1 || n>max_groups) return;
    w.ensure_altar_field();w.ensure_enemy_field();
    // Prefer a rich per-objective summary. Fit the full triangular travel table
    // alongside it on small maps; medium maps keep the complete travel table.
    bool matrix=n<=32,summary=8+7*n+(matrix ? n*(n-1)/2 : 0)<=capacity;
    if (!matrix && !summary) return;
    if (matrix) {
        while (!w.fields_ready() && bc::fuel_remaining()>600000)
            if (!w.build_next_group_field(std::min<std::uint64_t>(2000000,bc::fuel_remaining()-500000))) break;
        if (!w.fields_ready()) return;
    }
    std::array<std::uint8_t,1024> memory{};
    bc::detail::check(bc::detail::sdk_read_draft_memory(0,memory.data(),memory.size()));
    auto* p=memory.data()+offset;const auto sig=signature(w);
    p[0]=0xD4;p[1]=2;p[2]=n;p[3]=(matrix ? 1 : 0)|(summary ? 2 : 0);
    p[4]=sig&255;p[5]=sig>>8;p[6]=w.width;p[7]=w.height;
    int k=8;
    if (matrix) for (int i=0;i<n;++i) for (int j=i+1;j<n;++j) {
        const int d=w.group_to_group(i,j);
        if (d!=kUnreach && d>=255) return;
        if (d!=w.group_to_group(j,i)) return;
        p[k++]=d==kUnreach ? 255 : d;
    }
    if (summary) for (int i=0;i<n;++i) {
        if (bc::fuel_remaining()<150000) return;
        for (int d:{group_min(w,i,w.altar_field),group_min(w,i,w.spawn_field),group_min(w,i,w.enemy_field)}) {
            p[k++]=d&255;p[k++]=(d>>8)&255;
        }
        p[k++]=bank_width(w,i);
    }
    bc::draft_memory=memory;
#if X3_TRACE
    std::printf("X3_PATHS_DRAFT groups%d pairs%d rich%d bytes%d fuel%llu\n",n,matrix ? n*(n-1)/2 : 0,summary,k,
        static_cast<unsigned long long>(before-bc::fuel_remaining()));
#else
    (void)before;
#endif
}

void draft_paths_load(World& w) {
    if (bc::draft_memory.size()<1024 || w.bridges_on) return;
    const auto* p=reinterpret_cast<const std::uint8_t*>(bc::draft_memory.data())+offset;
    const int n=static_cast<int>(w.groups.size());const auto sig=signature(w);
    if (p[0]!=0xD4 || p[1]!=2 || p[2]!=n || n>max_groups || (p[4]|(p[5]<<8))!=sig || p[6]!=w.width || p[7]!=w.height) return;
    const bool matrix=p[3]&1,summary=p[3]&2;
    if (8+(matrix ? n*(n-1)/2 : 0)+(summary ? 7*n : 0)>capacity) return;
    static volatile int use=X3_DRAFT_USE+1;
    int k=8;
    if (matrix) {
        std::vector<std::vector<std::uint16_t>> rows(n,std::vector<std::uint16_t>(n,0));
        for (int i=0;i<n;++i) for (int j=i+1;j<n;++j) {
            const int d=p[k++];rows[i][j]=rows[j][i]=d==255 ? kUnreach : d;
        }
        if (use>1) w.pair_rows=std::move(rows);
    }
    if (summary) {
        std::vector<std::array<std::uint16_t,4>> meta(n);
        for (int i=0;i<n;++i) {
            for (int j=0;j<3;++j) {meta[i][j]=p[k]|(p[k+1]<<8);k+=2;}
            meta[i][3]=p[k++];
        }
        if (use>1) {
            w.draft_summary=std::move(meta);
            w.group_margin.resize(n);
            for (int i=0;i<n;++i) w.group_margin[i]=std::clamp(int(w.draft_summary[i][2])-int(w.draft_summary[i][1]),-999,999);
        }
    }
#if X3_TRACE
    std::printf("X3_PATHS_READ groups%d installed%d pairs%d rich%d\n",n,use>1,matrix,summary);
#endif
}
#endif
