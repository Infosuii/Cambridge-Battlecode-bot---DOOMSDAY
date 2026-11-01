#pragma once
#include "formation_search.h"
#include "crew_route.h"

namespace dz::crew {
struct Move { unsigned actor=0;std::vector<Tile> path; };
struct Phase {
    Monster target;
    Formation formation;
    std::vector<Move> moves;
    std::vector<Move> approach;
    std::array<Tile,max_units> staging{};
    std::array<double,max_units> raw{},escape{},transfer_loss{},approach_loss{};
    int transfer=0,approach_rounds=0,return_rounds=0;
};
// One formation per surviving member, including reachable, collision-free
// transitions in a concrete serial order. Geometry work and BFS both resume.
// A missing path never turns into a zero-cost leg or an executable partial plan.
struct SequenceSearch {
    enum class Stage { Empty, Geometry, Escape, Select, Route, Price, Done, Failed };
    Stage stage=Stage::Empty;
    FormationSearch geometry;
    RouteSearch route;
    std::vector<Phase> phases;
    unsigned phase=0,count=0,done=0,tried=0,moving=0;
    int width=0,height=0;
    std::array<Tile,max_units> positions{};
    std::array<Unit,max_units> roster{};
    unsigned actors=0;
    Tile destination{};
    bool parking=false;
    bool approaching=false;
    unsigned escape_actor=0,escape_ray=0,escape_step=1,price_move=0,price_step=0;
    unsigned price_camp=0;
    bool pricing_point=false;
    double escape_loss=0;
    bool escape_found=false;
    double best_escape=0;
    Tile best_exit{};
    int best_return=0;
    static constexpr std::array<Tile,8> rays{{{-1,-1},{-1,0},{-1,1},{0,-1},{0,1},{1,-1},{1,0},{1,1}}};
    bool pending() const {return stage!=Stage::Empty&&stage!=Stage::Done&&stage!=Stage::Failed;}
    void begin(std::span<const Unit> units,std::span<const Monster> camps,int w,int h) {
        phase=count=done=tried=0;width=w;height=h;stage=Stage::Failed;
        if(units.size()<2||units.size()>max_units||camps.empty()||camps.size()>max_camps)return;
        actors=units.size();std::copy(units.begin(),units.end(),roster.begin());
        if(phases.capacity()<max_camps)phases.reserve(max_camps);
        geometry.begin(units,camps);stage=Stage::Geometry;
    }
    template<class Open,class Home,class Budget>
    bool resume(std::span<const Unit> units,std::span<const Monster> camps,Open open,Home home,Budget budget) {
        if(stage==Stage::Done)return true;
        while(pending()) {
            if(!budget())return false;
            if(stage==Stage::Geometry) {
                const auto f=geometry.resume(units,camps.subspan(phase),[&](Tile p){return open(p,phase);},home,budget);
                if(geometry.pending())return false;
                if(!f.valid||f.active!=((1u<<units.size())-1u)){stage=Stage::Failed;return false;}
                if(phases.size()<=phase)phases.emplace_back();
                auto& next=phases[phase];next.target=camps[phase];next.formation=f;next.moves.clear();next.approach.clear();
                next.raw={};next.escape={};next.transfer_loss={};next.approach_loss={};
                next.transfer=next.approach_rounds=next.return_rounds=0;
                if(next.moves.capacity()<2*max_units)next.moves.reserve(2*max_units);
                if(next.approach.capacity()<2*max_units)next.approach.reserve(2*max_units);
                escape_actor=escape_ray=0;escape_step=1;escape_loss=0;escape_found=false;stage=Stage::Escape;
            } else if(stage==Stage::Escape) {
                auto& next=phases[phase];
                if(escape_actor==units.size()) {
                    approaching=true;positions=next.staging;done=tried=0;stage=Stage::Select;continue;
                }
                if(escape_ray==rays.size()) {
                    if(!escape_found){stage=Stage::Failed;return false;}
                    next.staging[escape_actor]=best_exit;next.escape[escape_actor]=best_escape;
                    next.return_rounds=std::max(next.return_rounds,best_return);
                    ++escape_actor;escape_ray=0;escape_step=1;escape_loss=0;escape_found=false;continue;
                }
                const auto origin=next.formation.positions[escape_actor],d=rays[escape_ray];
                const Tile p{origin.x+d.x*static_cast<int>(escape_step),origin.y+d.y*static_cast<int>(escape_step)};
                bool occupied=false;for(unsigned u=0;u<units.size();++u)if(u!=escape_actor&&next.formation.positions[u]==p)occupied=true;
                for(unsigned c=phase;c<camps.size();++c)occupied|=camps[c].p==p;
                if(escape_step>140||occupied||!open(p,phase)){++escape_ray;escape_step=1;escape_loss=0;continue;}
                double raw=0,here=0;
                for(unsigned c=phase;c<camps.size();++c) {
                    if(cheb(p,camps[c].p)<=camps[c].range)raw+=camps[c].damage*units[escape_actor].factor;
                    if(cheb(origin,camps[c].p)<=camps[c].range)here+=camps[c].damage*units[escape_actor].factor;
                }
                escape_loss+=raw;
                next.raw[escape_actor]=here;
                bool reserved=false;for(unsigned u=0;u<escape_actor;++u)reserved|=next.staging[u]==p;
                if(raw==0&&!reserved) {
                    const int h=home(p);if(h<0||h>=65535){++escape_ray;escape_step=1;escape_loss=0;continue;}
                    const int cost=static_cast<int>(escape_step)+h+1;
                    if(!escape_found||escape_loss<best_escape||(escape_loss==best_escape&&cost<best_return)) {
                        escape_found=true;best_escape=escape_loss;best_exit=p;best_return=cost;
                    }
                    ++escape_ray;escape_step=1;escape_loss=0;
                } else if(escape_found&&escape_loss>best_escape){++escape_ray;escape_step=1;escape_loss=0;}
                else ++escape_step;
            } else if(stage==Stage::Select) {
                auto& next=phases[phase];const auto& goals=next.formation.positions;
                for(unsigned u=0;u<units.size();++u)if(positions[u]==goals[u])done|=1u<<u;
                if(done==((1u<<units.size())-1u)) {
                    price_move=price_step=0;pricing_point=false;positions=approaching?next.staging:phases[phase-1].formation.positions;
                    stage=Stage::Price;continue;
                }
                auto& moves=approaching?next.approach:next.moves;
                if(moves.size()>=2*max_units){stage=Stage::Failed;return false;}
                auto occupied=[&](Tile p,unsigned except){
                    for(unsigned u=0;u<units.size();++u)if(u!=except&&positions[u]==p)return true;
                    return false;
                };
                moving=units.size();parking=false;
                // The intended front tank enters last. Otherwise it absorbs
                // every camp phase while all helpers walk into their places.
                // Price the temporary helper exposure explicitly below.
                for(unsigned pass=0;pass<2&&moving==units.size();++pass)
                    for(unsigned u=0;u<units.size();++u)if((u==next.formation.tank)==static_cast<bool>(pass)&&
                        !(done&(1u<<u))&&!(tried&(1u<<u))&&!occupied(goals[u],u)) {
                        moving=u;destination=goals[u];break;
                    }
                if(moving==units.size()) {
                    // A swap cycle needs a real parking step. Do not claim that
                    // two champions can exchange occupied tiles simultaneously.
                    if(tried){stage=Stage::Failed;return false;}
                    for(unsigned u=0;u<units.size()&&moving==units.size();++u)if(!(done&(1u<<u)))
                        for(int dx=-1;dx<=1&&moving==units.size();++dx)for(int dy=-1;dy<=1;++dy) {
                            if(!dx&&!dy)continue;const Tile p{positions[u].x+dx,positions[u].y+dy};
                            if(occupied(p,u)||!open(p,phase)||std::find(goals.begin(),goals.begin()+units.size(),p)!=goals.begin()+units.size())continue;
                            bool spawn=false;for(unsigned c=phase;c<camps.size();++c)spawn|=camps[c].p==p;if(spawn)continue;
                            moving=u;destination=p;parking=true;break;
                        }
                    if(moving==units.size()){stage=Stage::Failed;return false;}
                }
                route.begin(positions[moving],destination,width,height);stage=Stage::Route;
            } else if(stage==Stage::Route) {
                const auto status=route.resume([&](Tile p){
                    if(!open(p,phase))return false;
                    for(unsigned u=0;u<units.size();++u)if(u!=moving&&positions[u]==p)return false;
                    for(unsigned c=phase;c<camps.size();++c)if(camps[c].p==p)return false;
                    return true;
                },budget);
                if(status==RouteSearch::Status::Pending)return false;
                if(status!=RouteSearch::Status::Complete) {
                    tried|=1u<<moving;stage=Stage::Select;continue;
                }
                (approaching?phases[phase].approach:phases[phase].moves).push_back({moving,std::move(route.path)});
                positions[moving]=destination;tried=0;stage=Stage::Select;
            } else if(stage==Stage::Price) {
                auto& next=phases[phase];const auto& moves=approaching?next.approach:next.moves;
                if(price_move==moves.size()) {
                    if(approaching&&phase>0) {
                        approaching=false;positions=phases[phase-1].formation.positions;done=tried=0;stage=Stage::Select;
                    } else {count=phase+1;advance(units,camps);}
                    continue;
                }
                const auto& move=moves[price_move];
                auto& loss=approaching?next.approach_loss:next.transfer_loss;
                if(!pricing_point) {
                    if(price_step==move.path.size()){++price_move;price_step=0;continue;}
                    positions[move.actor]=move.path[price_step++];price_camp=phase;pricing_point=true;
                    ++(approaching?next.approach_rounds:next.transfer);
                }
                if(price_camp==camps.size()){pricing_point=false;continue;}
                const auto& camp=camps[price_camp++];int target=-1,nearest=camp.range+1;
                for(unsigned u=0;u<units.size();++u) {
                    const int distance=cheb(positions[u],camp.p);
                    if(distance<nearest||(distance==nearest&&target>=0&&units[u].handle<units[target].handle)){nearest=distance;target=u;}
                }
                if(target>=0&&nearest<=camp.range)loss[target]+=camp.damage*units[target].factor;
            }
        }
        return stage==Stage::Done;
    }
private:
    void advance(std::span<const Unit> units,std::span<const Monster> camps) {
        if(++phase==camps.size()){stage=Stage::Done;return;}
        geometry.begin(units,camps.subspan(phase));stage=Stage::Geometry;
    }
};
// Return the sole next walker and waypoint. The observer must see all crew
// positions. A body off the checked path invalidates the march, rather than
// teleporting it into the quote or letting followers block one another.
struct March { bool valid=false,complete=false;unsigned actor=0;Tile next{}; };
inline March march(const Phase& previous,const Phase& next,std::span<const Tile> actual) {
    if(actual.empty()||actual.size()>max_units)return {};
    auto expected=previous.formation.positions;
    for(const auto& move:next.moves) {
        if(move.actor>=actual.size())return {};
        bool other_ok=true;
        for(unsigned u=0;u<actual.size();++u)if(u!=move.actor)other_ok&=actual[u]==expected[u];
        if(other_ok) {
            if(actual[move.actor]==expected[move.actor]&&!move.path.empty())return {true,false,move.actor,move.path.front()};
            for(unsigned k=0;k<move.path.size();++k)if(actual[move.actor]==move.path[k]) {
                if(k+1<move.path.size())return {true,false,move.actor,move.path[k+1]};
                break;
            }
        }
        if(!move.path.empty())expected[move.actor]=move.path.back();
    }
    for(unsigned u=0;u<actual.size();++u)if(actual[u]!=next.formation.positions[u])return {};
    return {true,true};
}
inline March approach(const Phase& phase,std::span<const Tile> actual) {
    if(actual.empty()||actual.size()>max_units)return {};
    // Share the cursor logic without copying any route vectors.
    auto expected=phase.staging;
    for(const auto& move:phase.approach) {
        if(move.actor>=actual.size())return {};
        bool other_ok=true;for(unsigned u=0;u<actual.size();++u)if(u!=move.actor)other_ok&=actual[u]==expected[u];
        if(other_ok) {
            if(actual[move.actor]==expected[move.actor]&&!move.path.empty())return {true,false,move.actor,move.path.front()};
            for(unsigned k=0;k<move.path.size();++k)if(actual[move.actor]==move.path[k]) {
                if(k+1<move.path.size())return {true,false,move.actor,move.path[k+1]};break;
            }
        }
        if(!move.path.empty())expected[move.actor]=move.path.back();
    }
    for(unsigned u=0;u<actual.size();++u)if(actual[u]!=phase.formation.positions[u])return {};
    return {true,true};
}
inline int capacity(const Unit& unit,double hp,const Phase& p,unsigned u,int horizon=2000) {
    const double reserve=.15*unit.max_hp+1.25*p.escape[u]+2*p.raw[u];
    if(hp<=reserve)return 0;
    if(p.raw[u]<=0)return horizon;
    return std::max(0,static_cast<int>(std::min<double>(horizon,std::ceil((hp-reserve)/p.raw[u])-1)));
}
enum class SequenceReason { None, Scene, Damage, Capacity, Horizon, Budget };
struct SequenceQuote { bool complete=false;int finish=0,visits=0;SequenceReason reason=SequenceReason::Scene; };
template<class Budget=Unlimited>
SequenceQuote quote(std::span<const Unit> units,std::span<const Monster> remaining,const SequenceSearch& search,
                    unsigned first,int capture,int recall,int horizon,Budget budget={},bool projection=false,int sleep=-1) {
    SequenceQuote q;
    if(search.stage!=SequenceSearch::Stage::Done||first>search.count||remaining.size()!=search.count-first||search.count>search.phases.size()||
        units.empty()||units.size()>max_units||units.size()!=search.actors||capture<0||capture>2000||recall<0||recall>2000||horizon<1||horizon>2000||
        sleep< -1||sleep>2000||(sleep>=0&&(search.count!=1||remaining.size()!=1))||
        !(projection?stronger_roles(units,std::span<const Unit>(search.roster.data(),search.actors)):
            same_roles(units,std::span<const Unit>(search.roster.data(),search.actors))))return q;
    for(auto unit:units)if(!std::isfinite(unit.hp)||unit.hp>unit.max_hp)return q;
    std::array<double,max_units> hp{};for(unsigned u=0;u<units.size();++u)hp[u]=units[u].hp;
    long long elapsed=0;
    for(unsigned c=0;c<remaining.size();++c) {
        if(!budget())return {false,0,0,SequenceReason::Budget};
        const auto& p=search.phases[first+c];float damage=0;
        if(!std::isfinite(remaining[c].hp)||remaining[c].hp<=0||remaining[c].member!=p.target.member||remaining[c].p!=p.target.p||
            remaining[c].damage!=p.target.damage||remaining[c].range!=p.target.range)return q;
        for(unsigned u=0;u<units.size();++u)if(cheb(p.formation.positions[u],remaining[c].p)<=units[u].range)damage+=units[u].damage;
        if(damage<=0||!std::isfinite(damage)||remaining[c].hp/damage>horizon)return {false,0,0,SequenceReason::Damage};
        const int work=static_cast<int>(std::ceil(remaining[c].hp/damage))+1;
        int current=horizon,fresh=horizon;
        for(unsigned u=0;u<units.size();++u) {
            const double loss=c?p.transfer_loss[u]:(sleep>=0?0:p.approach_loss[u]);
            current=std::min(current,capacity(units[u],hp[u]-loss,p,u,horizon));
            fresh=std::min(fresh,capacity(units[u],units[u].max_hp-(sleep>=0?0:p.approach_loss[u]),p,u,horizon));
        }
        if(fresh<=0)return {false,0,0,SequenceReason::Capacity};
        // Every member stages outside the entire encounter. An isolated single
        // monster can then sleep before entry; that wait is paid on EVERY
        // return, and the executor must observe sleep before walking in.
        const int recovery=std::max(p.return_rounds+recall,std::max(0,sleep))+p.approach_rounds+(sleep>=0);
        if(current<=0) {
            // Recover BEFORE attempting an unaffordable march. Never subtract
            // lethal travel and then silently restore a dead actor to full HP.
            elapsed+=sleep>=0?recovery:(c?search.phases[first+c-1].return_rounds:p.return_rounds)+recall+p.approach_rounds;current=fresh;
            for(unsigned u=0;u<units.size();++u)hp[u]=units[u].max_hp-(sleep>=0?0:p.approach_loss[u]);
            ++q.visits;
        } else {
            elapsed+=c?p.transfer:p.approach_rounds+std::max(0,sleep)+(sleep>=0);
            for(unsigned u=0;u<units.size();++u)hp[u]-=c?p.transfer_loss[u]:(sleep>=0?0:p.approach_loss[u]);
        }
        int last=work;const int extra=work>current?(work-current+fresh-1)/fresh:0;
        if(extra) {
            elapsed+=static_cast<long long>(extra)*recovery;last=work-current-(extra-1)*fresh;
            for(unsigned u=0;u<units.size();++u)hp[u]=units[u].max_hp-(sleep>=0?0:p.approach_loss[u]);
        }
        for(unsigned u=0;u<units.size();++u)hp[u]-=last*p.raw[u];
        elapsed+=work;q.visits+=extra+1;
        if(elapsed+capture>horizon)return {false,0,0,SequenceReason::Horizon};
    }
    q.finish=elapsed+capture;q.complete=true;q.reason=SequenceReason::None;return q;
}
}
