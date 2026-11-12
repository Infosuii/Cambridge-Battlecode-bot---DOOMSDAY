// Unified bounded engagement action sequencing. The strategy/lifecycle remains the frozen v76 control.
#include "bot.h"
#include <cmath>
#if V81_SEQ
namespace d = cambc::detail;
bool Bot::sequence_combat() {
    auto& me = bc::self();
    const int now = static_cast<int>(bc::round_number());
    const std::uint64_t reserve = 32000;
    const auto entry_fuel=bc::fuel_remaining();
    if (entry_fuel < reserve + 18000 || !me.can_attack()) return false;
    const auto deadline=std::max<std::uint64_t>(reserve+9000,entry_fuel-16000);
    constexpr int N = 6;
    const EnemyRec* es[N]; int ne = 0;
    for (const auto& e : w.enemies)
        if (ne < N && e.hp > 0 && cheb(e.pos,pos) <= 7 && !bit(w.enemy_spawn,e.pos)) es[ne++] = &e;
    if (!ne) return false;
    float raw[2][N] = {}, incoming[N] = {};
    bool ready[2] = {spell_ready(0),spell_ready(1)};
    for (int j=0;j<ne;++j) {
        const auto& e=*es[j];
        incoming[j]=e.strength;
        for (int s=0;s<2;++s) if (ready[s]) {
            if (d::sdk_champion_ability_damage_against(my_id,s,e.id,&raw[s][j]) != 0)
                raw[s][j]=spells[s].modifier*focus;
        }
    }
    struct Route { vec2 dash, end; int slot; bool move; float prior; } routes[96];
    int nr=0;
    auto free = [&](vec2 p) {
        return p.x>=0 && p.y>=0 && p.x<w.width && p.y<w.height &&
            !bit(w.static_blocked,p) && (!bit(w.unit_tiles,p) || p==pos);
    };
    auto push = [&](vec2 land,vec2 end,int ds,bool mv) {
        if (bc::fuel_remaining()<deadline+3000) return;
        if (nr>=96 || !free(end)) return;
        float prior=-1e9f;
        for(int j=0;j<ne;++j) {
            const int gap=cheb(end,es[j]->pos);
            float damage=(gap<=range && (melee || !mv)) ? strength : 0.0f;
            if(ds>=0 && spells[ds].modifier>0 && cheb(land,es[j]->pos)<=spells[ds].radius) damage+=raw[ds][j];
            // Keep approach-only routes in the old executor, avoiding a new movement policy in this ablation.
            if(ds<0) for(int s=0;s<2;++s) if(ready[s] && spells[s].enemies && (!mv || !spells[s].excludes_walk)) {
                if(spells[s].kind==bc::ability_kind::dash) continue;
                const float reach=spells[s].range+(spells[s].kind==bc::ability_kind::aoe_damage?spells[s].radius:0.0f);
                if(gap<=reach) damage+=raw[s][j];
            }
            if (damage<=0) continue;
            prior=std::max(prior,damage+ (damage>=es[j]->hp ? 300.0f+4.0f*es[j]->gems : 0.0f));
        }
        if(prior<-1e8f) return;
        if(ds<0) prior+=1.0f;
        for(int i=0;i<nr;++i) if(routes[i].end==end && routes[i].slot==ds) {
            if(prior<=routes[i].prior) return;
            routes[i]={land,end,ds,mv,prior}; return;
        }
        routes[nr++]={land,end,ds,mv,prior};
    };
    push(pos,pos,-1,false);
    if(me.can_move()) for(vec2 delta:kDirs) if(free(pos+delta)) push(pos,pos+delta,-1,true);
    for(int s=0;s<2;++s) if(ready[s] && spells[s].kind==bc::ability_kind::dash && !spells[s].excludes_walk) {
        const int r=static_cast<int>(spells[s].range);
        for(int dy=-r;dy<=r;++dy) for(int dx=-r;dx<=r;++dx) {
            if(bc::fuel_remaining()<deadline+3000) break;
            const vec2 land{pos.x+dx,pos.y+dy};
            if(land==pos || !free(land)) continue;
            push(land,land,s,false);
            if(me.can_move()) for(vec2 delta:kDirs) push(land,land+delta,s,true);
        }
    }
    std::sort(routes,routes+nr,[](const Route&a,const Route&b){return a.prior>b.prior;});
    nr=std::min(nr,16);
    struct Plan {Route route; int attack=-1,spell=-1,spell_on=-1; vec2 aim; bool pre=false; float value=-1e9f;} best;
    int evaluated=0;
    auto danger = [&](vec2 q,int killed,int stunned) {
        float damage=0;
        for(int j=0;j<ne;++j) if(j!=killed && j!=stunned && cheb(q,es[j]->pos)<=es[j]->range+1) damage+=incoming[j];
        for(const auto& c:w.camps) if(!c.dead && c.hp<c.max_hp && cheb(c.pos,q)<=c.range) damage+=c.strength;
        return damage;
    };
    const float here_danger=danger(pos,-1,-1);
    for(int ri=0;ri<nr;++ri) {
        if(bc::fuel_remaining()<deadline) break;
        const Route& r=routes[ri];
        const float base_after=danger(r.end,-1,-1);
        // All basic targets, no spell and both spell slots. Target effects are evaluated jointly so a spell kill
        // can be paired with a basic hit on a different target rather than wasting the second action.
        for(int a=-1;a<ne;++a) {
            if(a>=0 && (cheb(r.end,es[a]->pos)>range || (!melee && r.move))) continue;
            for(int s=-1;s<2;++s) {
                if(s>=0 && (!ready[s] || r.slot>=0 || (spells[s].excludes_walk && r.move))) continue;
                if(s>=0 && spells[s].kind==bc::ability_kind::dash) continue;
                const bool reset=s>=0 && spells[s].kind==bc::ability_kind::attack_reset;
                if(reset && a<0) continue;
                if(s>=0 && !reset && (!spells[s].enemies ||
                    (spells[s].kind!=bc::ability_kind::damage && spells[s].kind!=bc::ability_kind::cc && spells[s].kind!=bc::ability_kind::aoe_damage))) continue;
                const int targets=(s<0 || reset)?1:ne;
                for(int t=0;t<targets;++t) {
                    if(bc::fuel_remaining()<deadline) break;
                    float damage[N]={}; int stunned=-1;
                    if(a>=0) damage[a]+=strength*champion_dealt_mult;
                    vec2 aim{}; bool pre=false;
                    if(reset) damage[a]+=strength*champion_dealt_mult;
                    else if(s>=0) {
                        const auto& sp=spells[s];
                        aim=es[t]->pos;
                        const int radius=sp.kind==bc::ability_kind::aoe_damage?static_cast<int>(sp.radius):0;
                        if(cheb(r.end,aim)>sp.range+radius) continue;
                        if(radius>0 && sp.ground && cheb(r.end,aim)>sp.range) {
                            aim.x=std::clamp(aim.x,r.end.x-static_cast<int>(sp.range),r.end.x+static_cast<int>(sp.range));
                            aim.y=std::clamp(aim.y,r.end.y-static_cast<int>(sp.range),r.end.y+static_cast<int>(sp.range));
                        }
                        for(int j=0;j<ne;++j) if(j==t || (radius>0 && cheb(es[j]->pos,aim)<=radius)) damage[j]+=raw[s][j];
                        if(sp.kind==bc::ability_kind::cc || (type==bc::champion_type::ryth && s==0)) stunned=t;
                    }
                    if(r.slot>=0 && spells[r.slot].modifier>0) for(int j=0;j<ne;++j)
                        if(cheb(r.dash,es[j]->pos)<=spells[r.slot].radius) damage[j]+=raw[r.slot][j];
                    float value=0; int killed=-1;
                    for(int j=0;j<ne;++j) {
                        value+=std::min(damage[j],es[j]->hp);
                        if(damage[j]>=es[j]->hp) value+=300.0f+4.0f*es[j]->gems,killed=j;
                    }
                    if(stunned>=0) value+=incoming[stunned];
                    float after=base_after;
                    if(killed>=0 && cheb(r.end,es[killed]->pos)<=es[killed]->range+1) after-=incoming[killed];
                    if(stunned>=0 && stunned!=killed && cheb(r.end,es[stunned]->pos)<=es[stunned]->range+1) after-=incoming[stunned];
                    value-=std::max(0.0f,after-here_danger);
                    value-=std::max(0.0f,after-hp)*2.0f;
                    if(r.slot>=0) value-=1.0f; // ties preserve a dash
                    ++evaluated;
                    if(value>best.value) best={r,a,s,t,aim,pre,value};
                }
            }
        }
    }
    if(best.value<=0 || !evaluated || (best.attack<0 && best.spell<0 && best.route.slot<0)) return false;
    bool acted=false; int errors=0;
    auto cast = [&](int s,int t,vec2 aim) {
        if(s<0 || cast_done) return;
        try {
            bool ok=false; const auto ab=me.abilities()[s];
            if(spells[s].kind==bc::ability_kind::attack_reset) ok=ab.use();
            else if(spells[s].ground || spells[s].kind==bc::ability_kind::aoe_damage || spells[s].kind==bc::ability_kind::dash) ok=ab.use(aim);
            else ok=ab.use(es[t]->unit);
            if(ok) cast_done=true,acted=true;
        } catch(...) {++errors;}
    };
    if(best.route.slot>=0) {
        cast(best.route.slot,0,best.route.dash);
        if(cast_done) pos=best.route.dash;
        else return false;
    }
    if(best.route.move && best.route.end!=pos) {
        try {if(me.move_absolute(best.route.end)) pos=best.route.end,walked=true,acted=true;} catch(...) {++errors;}
    }
    const bool reset=best.spell>=0 && spells[best.spell].kind==bc::ability_kind::attack_reset;
    if(best.spell>=0 && !reset) cast(best.spell,best.spell_on,best.aim);
    if(best.attack>=0) {
        const auto& e=*es[best.attack];
        if(attack_unit(e.unit,e.pos)) {
            acted=true;
            if(reset) {
                try {if(e.unit.is_visible() && e.unit.health()>0) {cast(best.spell,0,pos);attack_unit(e.unit,e.pos);}} catch(...) {++errors;}
            }
        }
    }
#if V81_SEQ_DIAG
    std::printf("SQ %d %d %d %d %d %d %.1f %d %llu %d\n",now,slot,nr,evaluated,best.route.slot,best.spell,best.value,errors,
        static_cast<unsigned long long>(entry_fuel-bc::fuel_remaining()),static_cast<int>(bc::round_number())-now);
#endif
    return acted;
}
#else
bool Bot::sequence_combat(){return false;}
#endif
