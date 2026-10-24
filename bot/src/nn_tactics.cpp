#include "nn_config.h"
#if NN_ANY_HEAD
#include "nn_tactics.h"
#include "bot.h"
#include "nn_obs.h"
#include "nn_budget.h"
#include "tsearch.h"

namespace {
// No constructors or heap state. Cached frame is immutable map information, not a cached live action snapshot.
constinit bool g_frame_ready = false;
constinit nnobs::Frame g_frame{};
constinit int g_leaf_round = -1, g_leaf_calls = 0;
constinit int g_belief_round = -1, g_belief_x = 0, g_belief_y = 0;
constinit float g_belief[9]{};
inline int bounded(int n, int max) { return n < 0 ? 0 : n > max ? max : n; }
inline std::uint32_t tile_id(int x, int y) { return static_cast<std::uint32_t>((y << 16) | x); }
}

struct nn_tactics_access {
    static void belief(const Bot& b) {
        if constexpr (nncfg::mode(nncfg::H::belief) != nncfg::Mode::off) {
            if (g_belief_round==b.round) return;
            g_belief_round=b.round;
            // Calling value before move admission avoids overwriting a pre-admission token. It caches all outputs.
            for (int s=0;s<9;++s) g_belief[s]=nne::bounded_belief(nnh::value(b,nncfg::H::belief,s));
            if (!nnh::context_position(g_belief_x,g_belief_y)) {
                g_belief_x=b.pos.x; g_belief_y=b.pos.y;
                for (float& v:g_belief) v=0.0f;
            }
        }
    }
    static nnobs::Frame frame(const Bot& b) {
        if (!g_frame_ready) {
            cambc::detail::aabb box{};
            const int team = cambc::detail::sdk_my_team();
            cambc::detail::sdk_spawn_region(team, &box);
            g_frame = nnobs::make_frame(b.w.width, b.w.height, static_cast<int>(bc::map::symmetry()),
                                      box.min_x + box.max_x - 1, box.min_y + box.max_y - 1, team);
            g_frame_ready = true;
        }
        return g_frame;
    }
    static float frac(const Bot& b) { return b.hp / std::max(1.0f, b.max_hp); }
    static float belief_risk(const Bot& b, vec2 q) {
        if constexpr (nncfg::mode(nncfg::H::belief) == nncfg::Mode::off) return 0.0f;
        const auto f=frame(b);
        const int dx=static_cast<int>(nnobs::canon_dx(f,q.x-g_belief_x));
        const int dy=static_cast<int>(nnobs::canon_dy(f,q.y-g_belief_y));
        return g_belief[nne::belief_sector(dx,dy)];
    }
    static int belief_rank(const Bot& b, const nne::Tile* tiles, int n) {
        if (n<=1) return 0;
        int best=0; float risk=belief_risk(b,{tiles[0].x,tiles[0].y})-0.5f;
        for (int i=1;i<n;++i) {
            const float r=belief_risk(b,{tiles[i].x,tiles[i].y});
            if (r<risk) best=i,risk=r;
        }
        return best;
    }
    static int home(const Bot& b, vec2 q) {
        const int d = fdist(b.w.spawn_field, q);
        return d == kUnreach ? 64 : d;
    }
    // Visible entities only, each bounded by the game roster. No hidden-state host queries.
    static void nearby(const Bot& b, vec2 q, int& foes, int& friends, float& threat, int& nearest) {
        foes = friends = 0; threat = 0; nearest = 64;
        for (const auto& e : b.w.enemies) {
            const int d = cheb(q,e.pos); nearest = std::min(nearest,d); foes += d <= 8;
            if (d <= e.range + 1) threat += e.strength + 0.25f * e.focus;
        }
        for (const auto& a : b.w.allies) friends += cheb(q,a.pos) <= 8;
    }
    static nne::Option move_option(const Bot& b, const nne::Tile& tile, std::uint8_t context, float teacher_score) {
        nne::Option o{}; const vec2 q{tile.x,tile.y}; o.id = tile_id(q.x,q.y);
        int en, al, nearest; float threat; nearby(b,q,en,al,threat,nearest);
        const auto f = frame(b);
        o.raw[0] = static_cast<float>(nnobs::canon_dx(f,q.x-b.pos.x));
        o.raw[1] = static_cast<float>(nnobs::canon_dy(f,q.y-b.pos.y));
        o.raw[2] = tile.score - teacher_score;
        o.raw[3] = static_cast<float>(home(b,q));
        o.raw[4] = static_cast<float>(home(b,b.pos)-home(b,q));
        o.raw[5] = static_cast<float>(nearest); o.raw[6] = static_cast<float>(en); o.raw[7] = static_cast<float>(al);
        o.raw[8] = threat; o.raw[9] = frac(b); o.raw[10] = static_cast<float>(b.gems);
        o.raw[11] = bit(b.w.bushes,q); o.raw[12] = bit(b.w.hot_zone,q); o.raw[13] = bit(b.w.ally_spawn,q);
        o.raw[14] = bit(b.w.enemy_spawn_zone,q); o.raw[15] = static_cast<float>(b.range);
        o.raw[16] = b.walked; o.raw[17] = b.cast_done; o.raw[18] = static_cast<float>(b.round);
        o.raw[19] = b.w.altar_ready ? static_cast<float>(std::min<int>(fdist(b.w.altar_field,q),64)) : 64.0f;
        if (b.target_group >= 0 && b.w.has_field(b.target_group))
            o.raw[20] = static_cast<float>(std::min(b.w.group_distance(b.target_group,q),64));
        o.raw[21] = context == 2; o.raw[22] = context == 3; o.raw[23]=belief_risk(b,q);
        return o;
    }
    static nne::Option combat_option(const Bot& b, const EnemyRec& e, int action, int slot, bool dash) {
        nne::Option o{};
        // Target handles are IDs in context0; slot+1 (0=keep) are IDs in context1. Context disambiguates them.
        o.id = action == 0 ? e.id : static_cast<std::uint32_t>(slot + 1);
        int en, al, nearest; float threat; nearby(b,b.pos,en,al,threat,nearest);
        o.raw[0] = static_cast<float>(action); o.raw[1] = static_cast<float>(slot + 1);
        o.raw[2] = static_cast<float>(cheb(b.pos,e.pos)); o.raw[3] = e.hp;
        o.raw[4] = e.hp / std::max(1.0f,e.max_hp); o.raw[5] = static_cast<float>(e.gems);
        o.raw[6] = e.strength; o.raw[7] = e.focus; o.raw[8] = static_cast<float>(e.range);
        o.raw[9] = static_cast<float>(en); o.raw[10] = static_cast<float>(al); o.raw[11] = static_cast<float>(b.range);
        o.raw[12] = frac(b); o.raw[13] = e.tributing(); o.raw[14] = e.recalling();
        o.raw[15] = b.walked; o.raw[16] = b.cast_done; o.raw[17] = dash;
        if (slot >= 0) {
            const auto& sp = b.spells[slot];
            o.raw[18] = sp.kind == bc::ability_kind::cc; o.raw[19] = sp.kind == bc::ability_kind::aoe_damage;
            o.raw[21] = sp.modifier * b.focus / std::max(1.0f,e.hp);
        }
        o.raw[20] = static_cast<float>(b.round); o.raw[22] = static_cast<float>(b.gems) / 50.0f;
        return o;
    }
    static int move(const Bot& b, const nne::Tile* tiles, int n, std::uint8_t c) {
        n = bounded(n,nnh::kMaxK);
        if (n <= 1) return 0;
        belief(b);
        if constexpr (nncfg::mode(nncfg::H::move) == nncfg::Mode::off) {
            if (!nnb::admit(nncfg::H::belief,1800+n*200)) return 0;
            nnb::Meter meter(nncfg::H::belief);
            return belief_rank(b,tiles,n);
        }
        if (!nnh::admit(b,nncfg::H::move,n,1200 + n*950)) return 0;
        nne::Option a[nnh::kMaxK];
        for (int i=0;i<n;++i) a[i] = move_option(b,tiles[i],c,tiles[0].score);
        nnh::Decision d; nne::build_move(a,n,c,d);
        const auto r = nnh::decide(b,d); return r.choice >= 0 && r.choice < n ? r.choice : 0;
    }
    static const EnemyRec* target(const Bot& b, const EnemyRec* teacher) {
        if (!teacher || b.w.enemies.size() <= 1 || !nnh::admit(b,nncfg::H::combat,8,8000)) return teacher;
        const EnemyRec* ptr[nnh::kMaxK] = {teacher}; int n = 1;
        for (const auto& e : b.w.enemies) {
            if (e.id == teacher->id || e.hp <= 0 || n >= 8) continue;
            // Selection is a visible-target intent. Exact action readiness/range stays in attack_unit/cast_on_enemy.
            cambc::detail::champion_info live{};
            if (cambc::detail::sdk_champion(e.id,&live)!=0 || live.health<=0) continue;
            ptr[n++] = &e;
        }
        nne::Option a[nnh::kMaxK];
        for (int i=0;i<n;++i) a[i] = combat_option(b,*ptr[i],0,-1,false);
        nnh::Decision d; nne::build_combat(a,n,0,d);
        return ptr[nnh::decide(b,d).choice];
    }
    static nne::Tile local(const Bot& b, nne::Tile teacher, std::uint8_t c) {
        belief(b);
        if constexpr (nncfg::mode(nncfg::H::move) == nncfg::Mode::off) {
            if (!nnb::admit(nncfg::H::belief,12000)) return teacher;
        } else if (!nnh::admit(b,nncfg::H::move,9,12000)) return teacher;
        const auto feature_start=nnb::fuel_left();
        nne::Tile tiles[9] = {teacher}; int n=1;
        // Only after admission: bounded local endpoint generator; traversability and occupancy stay deterministic.
        for (vec2 dir:kDirs) {
            const vec2 q=b.pos+dir;
            if ((q.x==teacher.x && q.y==teacher.y) || q.x<0 || q.y<0 || q.x>=b.w.width || q.y>=b.w.height ||
                bit(b.w.static_blocked,q) || bit(b.w.unit_tiles,q)) continue;
            tiles[n++] = nne::Tile{q.x,q.y,teacher.score};
        }
        // Holding the current tile is a legal movement intent. Existing caller returns false and continues its action chain.
        if (n<9 && (teacher.x!=b.pos.x || teacher.y!=b.pos.y)) tiles[n++] = nne::Tile{b.pos.x,b.pos.y,teacher.score};
        if constexpr (nncfg::mode(nncfg::H::move) == nncfg::Mode::off) {
            const auto chosen=tiles[belief_rank(b,tiles,n)];
            nnb::charge(nncfg::H::belief,feature_start-nnb::fuel_left());
            return chosen;
        }
        nne::Option a[9]; for (int i=0;i<n;++i) a[i]=move_option(b,tiles[i],c,teacher.score);
        nnh::Decision d; nne::build_move(a,n,c,d); return tiles[nnh::decide(b,d).choice];
    }
    static nne::CastPick cast(const Bot& b, const EnemyRec& e, int best, int ds, int ax, int ay) {
        const nne::CastPick teacher{ds >= 0 ? ds : best,ds >= 0};
        if (teacher.slot < 0 || !nnh::admit(b,nncfg::H::combat,4,5000)) return teacher;
        nne::CastPick picks[4] = {teacher}; int n=1;
        for (int s=0;s<2;++s) {
            if (s == teacher.slot || !b.spell_ready(s)) continue;
            const auto& sp = b.spells[s];
            if ((sp.excludes_walk && b.walked) || !sp.enemies) continue;
            const int reach = NOVA_AOE_AIM && sp.kind == bc::ability_kind::aoe_damage && sp.ground ?
                              static_cast<int>(sp.range+sp.radius) : static_cast<int>(sp.range);
            if (cheb(b.pos,e.pos) > reach) continue;
            if (sp.kind != bc::ability_kind::damage && sp.kind != bc::ability_kind::aoe_damage && sp.kind != bc::ability_kind::cc) continue;
            if (sp.kind == bc::ability_kind::cc && b.keep_channel && e.tributing()) continue;
            // Mask before deciding, so the NFS1 chosen index still describes the action actually dispatched.
            try { if (!bc::self().abilities()[s].is_ready()) continue; } catch (...) { continue; }
            picks[n++] = nne::CastPick{s,false};
        }
        picks[n++] = nne::CastPick{-1,false}; // keep the spell; ordinary attack/move chain remains available
        nne::Option a[4]; for (int i=0;i<n;++i) a[i] = combat_option(b,e,1,picks[i].slot,picks[i].dash);
        nnh::Decision d; nne::build_combat(a,n,1,d);
        const nne::CastPick chosen = picks[nnh::decide(b,d).choice];
        (void)ax; (void)ay; return chosen;
    }
    static int verdict(const Bot& b, int teacher, float fight, float run, float margin, float ttd, bool target) {
        if (!nnh::admit(b,nncfg::H::engage,3,4000)) return teacher;
        int ids[3] = {teacher,0,0}; int n=1;
        for (int id=-1;id<=1;++id) {
            if (id==teacher) continue;
            // Emergency flee remains deterministic; fight requires a visible target and a viable health reserve.
            if (id==1 && (!target || frac(b)<0.25f || ttd<=1.0f || a2ts::snap.omit_reach ||
                          a2ts::snap.link_partial || bit(b.w.hot_zone,b.pos))) continue;
            if (teacher==-1 && (frac(b)<0.15f || ttd<=1.0f)) continue;
            ids[n++] = id;
        }
        int en, al, nearest; float threat; nearby(b,b.pos,en,al,threat,nearest);
        nne::Option a[3];
        for (int i=0;i<n;++i) {
            auto& o=a[i]; o={}; o.id=static_cast<std::uint32_t>(ids[i]+1);
            o.raw[0]=ids[i]==1; o.raw[1]=ids[i]==-1; o.raw[2]=ids[i]==0;
            o.raw[3]=fight; o.raw[4]=run; o.raw[5]=margin; o.raw[6]=ttd;
            o.raw[7]=nearest; o.raw[8]=frac(b); o.raw[9]=static_cast<float>(b.gems);
            o.raw[10]=en; o.raw[11]=al; o.raw[12]=b.strength; o.raw[13]=b.focus;
            o.raw[14]=b.heading_home; o.raw[15]=b.melee; o.raw[16]=target;
            o.raw[17]=static_cast<float>(b.round); o.raw[18]=b.cast_done; o.raw[19]=b.walked;
        }
        nnh::Decision d; nne::build_engage(a,n,0,d); return ids[nnh::decide(b,d).choice];
    }
    static int ward(const Bot& b, const nne::Tile* tiles, int n, std::uint8_t context) {
        n=bounded(n,15);
        if (n==0 || !nnh::admit(b,nncfg::H::ward,n+1,1400+n*600)) return n ? 0 : -1;
        nne::Option a[nnh::kMaxK]; const auto f=frame(b);
        for (int i=0;i<=n;++i) {
            auto& o=a[i]; o={}; const bool skip=i==n; o.id=skip ? 0xffffffffu : tile_id(tiles[i].x,tiles[i].y);
            const vec2 q=skip ? b.pos : vec2{tiles[i].x,tiles[i].y};
            int en, al, nearest; float threat; nearby(b,q,en,al,threat,nearest);
            o.raw[0]=static_cast<float>(nnobs::canon_dx(f,q.x-b.pos.x)); o.raw[1]=static_cast<float>(nnobs::canon_dy(f,q.y-b.pos.y));
            o.raw[2]=skip ? 0 : tiles[i].score-tiles[0].score;
            o.raw[3]=static_cast<float>(nearest); o.raw[4]=en; o.raw[5]=skip;
            o.raw[6]=bit(b.w.bushes,q); o.raw[7]=bit(b.w.visible,q); o.raw[8]=bit(b.w.hot_zone,q);
            o.raw[9]=frac(b); o.raw[10]=static_cast<float>(b.gems); o.raw[11]=b.heading_home;
            o.raw[12]=static_cast<float>(b.round); o.raw[13]=context==1; o.raw[14]=context==2;
        }
        nnh::Decision d; nne::build_ward(a,n+1,context,d); const int k=nnh::decide(b,d).choice; return k==n ? -1 : k;
    }
    static float leaf_value(const Bot& b, const ts::State& s, const ts::State& e, int hx, int hy, int plan) {
        if (g_leaf_round != b.round) g_leaf_round=b.round,g_leaf_calls=0;
        if (g_leaf_calls>=4 || !nnh::admit(b,nncfg::H::ts_leaf,1,2200)) return 0.0f;
        ++g_leaf_calls;
        float raw[nne::kLeafF]={};
        for (int i=0;i<s.n && i<ts::kMaxUnits;++i) {
            const int side=s.u[i].team;
            raw[side==0 ? 0 : 1] += e.u[i].hp-s.u[i].hp;
            raw[side==0 ? 2 : 3] += s.u[i].alive() && !e.u[i].alive();
        }
        raw[4]=e.u[0].alive() ? e.u[0].hp/std::max(1.0f,e.u[0].max_hp) : 0;
        raw[5]=static_cast<float>(ts::cheb(e.u[0].x,e.u[0].y,hx,hy));
        raw[6]=static_cast<float>(e.u[0].gems-s.u[0].gems); raw[7]=static_cast<float>(plan);
        float feat[nne::kLeafF]; nne::build_leaf(raw,feat);
        return nnh::leaf(b,feat,nne::kLeafF,0);
    }
};

namespace nne {
int move_rank(const Bot& b,const Tile* t,int n,std::uint8_t c) { return nn_tactics_access::move(b,t,n,c); }
Tile local_move(const Bot& b,Tile t,std::uint8_t c) { return nn_tactics_access::local(b,t,c); }
const EnemyRec* combat_target(const Bot& b,const EnemyRec* t) { return nn_tactics_access::target(b,t); }
CastPick combat_cast(const Bot& b,const EnemyRec& e,int best,int ds,int x,int y) { return nn_tactics_access::cast(b,e,best,ds,x,y); }
int engage(const Bot& b,int t,float f,float r,float m,float d,bool target) { return nn_tactics_access::verdict(b,t,f,r,m,d,target); }
int ward_rank(const Bot& b,const Tile* t,int n,std::uint8_t c) { return nn_tactics_access::ward(b,t,n,c); }
float leaf(const Bot& b,const ts::State& s,const ts::State& e,int x,int y,int p) { return nn_tactics_access::leaf_value(b,s,e,x,y,p); }
}
#endif
