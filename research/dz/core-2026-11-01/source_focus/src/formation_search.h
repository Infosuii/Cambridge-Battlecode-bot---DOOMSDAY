#pragma once
#include "formation.h"

namespace dz::crew {
// Geometry construction is a persistent job, not a retry of an aborted whole
// search. The adapter owns roster/scene identity and invalidates this state.
struct FormationSearch {
    enum class Stage { Empty, Front, Directions, Ray, Helpers, Done, Failed };
    Stage stage=Stage::Empty;
    Formation result;
    struct Front { Tile p;float incoming=0;int home=0; };
    std::array<Front,8> front{};
    std::array<std::pair<int,Tile>,8> directions{};
    std::array<unsigned,max_units> order{};
    unsigned cursor=0,count=0,face=0,ray=0,helper=0,pose=0,robust=0,attempt=0;
    int step=1;
    float ray_loss=0,best_incoming=0;
    int best_reach=-1,best_home=65535;
    bool found=false;
    bool pending() const {return stage!=Stage::Empty&&stage!=Stage::Done&&stage!=Stage::Failed;}
    void begin(std::span<const Unit> units,std::span<const Monster> camps,unsigned focus=0) {
        *this={};stage=Stage::Failed;
        if(units.empty()||units.size()>max_units||camps.empty()||camps.size()>max_camps||focus>=camps.size())return;
        for(auto c:camps)if(!std::isfinite(c.hp)||!std::isfinite(c.damage)||c.hp<=0||c.damage<0||c.range<0||c.range>64)return;
        unsigned melee=max_units;
        for(unsigned u=0;u<units.size();++u) {
            const auto& a=units[u];
            if(!std::isfinite(a.hp)||!std::isfinite(a.max_hp)||!std::isfinite(a.damage)||!std::isfinite(a.factor)||
                a.hp<=0||a.max_hp<a.hp||a.damage<=0||a.factor<=0||a.range<1||a.range>3)return;
            order[u]=u;
            if(a.range==1&&(melee==max_units||a.handle<units[melee].handle))melee=u;
            if(a.max_hp/a.factor>units[robust].max_hp/units[robust].factor||
                (a.max_hp/a.factor==units[robust].max_hp/units[robust].factor&&a.handle<units[robust].handle))robust=u;
        }
        std::sort(order.begin(),order.begin()+units.size(),[&](auto a,auto b){return units[a].handle<units[b].handle;});
        result.focus=focus;result.tank=melee<max_units?melee:robust;stage=Stage::Front;
    }
    template<class Walkable,class Home,class Budget=Unlimited>
    Formation resume(std::span<const Unit> units,std::span<const Monster> camps,Walkable walkable,Home home,Budget budget={}) {
        if(stage==Stage::Done)return result;
        if(!pending()||units.empty()||units.size()>max_units||camps.empty()||camps.size()>max_camps)return {};
        std::array<CampThreat,max_camps> threats;
        int range=0;
        for(unsigned c=0;c<camps.size();++c){threats[c]={camps[c].p,camps[c].damage,camps[c].range};range=std::max(range,camps[c].range);}
        const auto scene=std::span<const CampThreat>(threats.data(),camps.size());
        auto open=[&](Tile p){return walkable(p)&&std::none_of(camps.begin(),camps.end(),[&](auto c){return c.p==p;});};
        const std::array<Tile,8> steps{{{-1,-1},{-1,0},{-1,1},{0,-1},{0,1},{1,-1},{1,0},{1,1}}};
        auto fail_or_retry=[&] {
            if(!attempt&&result.tank!=robust) {
                result={false,robust,0,result.focus};attempt=1;cursor=count=face=0;stage=Stage::Front;
            } else stage=Stage::Failed;
        };
        while(pending()) {
            if(!budget())return {};
            if(stage==Stage::Front) {
                if(cursor<9) {
                    const int dx=static_cast<int>(cursor/3)-1,dy=static_cast<int>(cursor%3)-1;++cursor;
                    if(!dx&&!dy)continue;
                    const Tile p{camps[result.focus].p.x+dx,camps[result.focus].p.y+dy};
                    if(open(p))front[count++]={p,camp_damage(p,scene),home(p)};
                    continue;
                }
                std::sort(front.begin(),front.begin()+count,[](auto a,auto b){
                    if(a.incoming!=b.incoming)return a.incoming<b.incoming;
                    if(a.home!=b.home)return a.home<b.home;
                    return a.p.x<b.p.x||(a.p.x==b.p.x&&a.p.y<b.p.y);
                });
                if(!count){fail_or_retry();continue;}
                cursor=0;stage=Stage::Directions;
            } else if(stage==Stage::Directions) {
                const auto p=front[face].p;
                if(cursor<steps.size()) {
                    const auto d=steps[cursor];directions[cursor++]={home({p.x+d.x,p.y+d.y}),d};continue;
                }
                std::sort(directions.begin(),directions.end(),[](auto a,auto b){return a.first<b.first;});
                ray=0;step=1;ray_loss=0;stage=Stage::Ray;
            } else if(stage==Stage::Ray) {
                if(ray==steps.size()) {
                    if(++face==count){fail_or_retry();continue;}
                    cursor=0;stage=Stage::Directions;continue;
                }
                const auto origin=front[face].p,d=directions[ray].second;
                const Tile p{origin.x+d.x*step,origin.y+d.y*step};
                if(step>2*range+2||!open(p)){++ray;step=1;ray_loss=0;continue;}
                const float incoming=camp_damage(p,scene);ray_loss+=incoming;
                if(incoming==0) {
                    result.positions[result.tank]=origin;result.exit=p;result.escape_steps=step;result.active=1u<<result.tank;
                    helper=pose=0;found=false;best_reach=-1;stage=Stage::Helpers;
                } else ++step;
            } else if(stage==Stage::Helpers) {
                if(helper==units.size()) {
                    if(std::popcount(result.active)<2&&units.size()>1){fail_or_retry();continue;}
                    result.valid=true;stage=Stage::Done;return result;
                }
                const unsigned u=order[helper];const int r=units[u].range,width=2*r+1;
                if(u==result.tank||pose==static_cast<unsigned>(width*width)) {
                    if(found&&u!=result.tank)result.active|=1u<<u;
                    ++helper;pose=0;found=false;best_reach=-1;continue;
                }
                const Tile p{camps[result.focus].p.x+static_cast<int>(pose/width)-r,
                    camps[result.focus].p.y+static_cast<int>(pose%width)-r};++pose;
                const int reach=cheb(p,camps[result.focus].p);
                if(!reach||!open(p)||(reach==1&&units[u].handle<units[result.tank].handle))continue;
                const auto origin=result.positions[result.tank];const int distance=cheb(p,origin);
                const Tile d{(result.exit.x>origin.x)-(result.exit.x<origin.x),(result.exit.y>origin.y)-(result.exit.y<origin.y)};
                if(distance<=result.escape_steps&&p==Tile{origin.x+d.x*distance,origin.y+d.y*distance})continue;
                bool occupied=false;for(unsigned a=0;a<units.size();++a)occupied|=(result.active&(1u<<a))&&result.positions[a]==p;
                if(occupied)continue;
                const float incoming=camp_damage(p,scene);const int h=home(p);
                if(!found||incoming<best_incoming||(incoming==best_incoming&&(reach>best_reach||(reach==best_reach&&h<best_home)))) {
                    found=true;best_incoming=incoming;best_reach=reach;best_home=h;result.positions[u]=p;
                }
            }
        }
        return {};
    }
};
}
