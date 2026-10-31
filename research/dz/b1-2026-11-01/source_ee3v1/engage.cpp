#include "engage.h"
#if DZ_ECONOMY_V2
#include "engagement.h"
namespace dz {
namespace {
combat::Unit snapshot(const SeenChampion& seen,int side) {
    auto& c=seen.sdk;combat::Unit u;
    u.x=seen.p.x;u.y=seen.p.y;u.hp=seen.hp;u.max_hp=seen.max_hp;u.damage=seen.strength;
    u.range=seen.range;u.side=side;u.ranged=u.range>1;u.bag=c.gem_count();
    const auto state=c.state();const auto restrictions=c.restrictions();
    u.can_move=state.contains(cambc::champion_state::can_move)&&!restrictions.contains(cambc::buff_restrictions::move);
    u.can_attack=state.contains(cambc::champion_state::can_attack)&&!restrictions.contains(cambc::buff_restrictions::attack);
    u.can_cast=state.contains(cambc::champion_state::can_cast)&&!restrictions.contains(cambc::buff_restrictions::cast);
    u.immune=c.champion_name()==cambc::champion_type::marcella;
    u.heart=c.champion_name()==cambc::champion_type::heart_of_ruin;
    u.splash=c.champion_name()==cambc::champion_type::varg;
    if(c.champion_name()==cambc::champion_type::ren)u.retaliation=.2f*c.focus(); // Pinned engine-2.0.0 passive.
    const auto buffs=c.buffs();
    if(buffs.has_shield()){auto shield=buffs.get<cambc::buff_shield>();u.shield=shield.value;u.shield_ticks=shield.duration;}
    if(buffs.has_stun())u.stun=buffs.get<cambc::buff_stun>().duration;
    const auto owned=c.item_count();float durability=0;
    for(auto stat:{cambc::item_stat::strength,cambc::item_stat::focus,cambc::item_stat::health}) {
        auto item=cambc::get_item_enum(cambc::item_family::durability,stat,false);
        if(owned[item])durability=std::max(durability,item.passive_magnitude());
    }
    u.mitigation=1-durability;
    unsigned slot=0;
    for(auto ability:c.abilities()) {
        auto& s=u.spells[slot++];if(!ability.info())continue;
        s.cooldown=ability.cooldown();
        std::visit([&](auto p) {
            s.period=p.max_cooldown;s.exclusive=p.exclusive_with_movement;
            if constexpr(requires{p.range;})s.range=p.range;
            if constexpr(requires{p.duration;})s.duration=p.duration;
        },*ability.info());
        if(ability.is_attack_reset()) {
            s.kind=combat::Kind::Reset;
            if(std::get<cambc::ability_attack_reset>(*ability.info()).enhanced_attack)s.duration=1;
        }
        else if(ability.is_shield()){s.kind=combat::Kind::Shield;s.amount=ability.shield_amount();}
        else if(ability.is_heal()&&ability.can_target_self()){s.kind=combat::Kind::Heal;s.amount=ability.heal_amount();}
        else if(ability.is_dash()){s.kind=combat::Kind::Dash;s.amount=ability.damage_amount();}
        else if(ability.can_target_enemies()&&(ability.is_damage()||ability.is_aoe_damage()||ability.is_cc())) {
            s.kind=ability.is_cc()?combat::Kind::Control:combat::Kind::Damage;s.amount=ability.damage_amount();
        }
        // SDK spell damage already includes CURRENT Heart amplification. The
        // projection recomputes it from evolving HP, so store the raw amount.
        if(u.heart&&(s.kind==combat::Kind::Damage||s.kind==combat::Kind::Control||s.kind==combat::Kind::Dash))
            s.amount/=1+.5f*(1-u.hp/u.max_hp);
    }
    return u;
}
}
std::optional<Goal> engagement_goal(const StaticWorld& w,Memory& m,const Observation& o,const TurnContext& tc) {
    if(o.enemies.empty()||!tc.allow(45000))return std::nullopt;
    const auto start=fuel_left();
    std::array<combat::Unit,combat::max_units> scene{};unsigned n=0;
    const SeenChampion own{cambc::self(),o.p,o.hp,o.max_hp,o.strength,o.range};
    scene[n++]=snapshot(own,0);
    std::array<const SeenChampion*,combat::max_units> sources{};
    sources[0]=&own;
    for(auto side:{1,0})for(const auto& seen:side?o.enemies:o.allies) {
        if(n>=8||!tc.allow(30000)||start-fuel_left()>14000)break;
        if(seen.p.chebyshev_distance(o.p)>10||w.in_enemy_spawn(seen.p))continue;
        sources[n]=&seen;scene[n++]=snapshot(seen,side);
    }
    unsigned focus=n;float best=1e30f;
    for(unsigned i=1;i<n;++i)if(scene[i].side==1) {
        const float score=(scene[i].hp+scene[i].shield)/std::max(1.f,o.strength)+
            2*std::max(0,combat::distance(scene[0],scene[i])-o.range)-scene[i].bag*.02f;
        if(score<best){best=score;focus=i;}
    }
    if(focus==n)return std::nullopt;
    unsigned modeled_enemies=0;for(unsigned i=0;i<n;++i)modeled_enemies+=scene[i].side==1;
    const unsigned nearby_enemies=std::count_if(o.enemies.begin(),o.enemies.end(),[&](const auto& e){return e.p.chebyshev_distance(o.p)<=10&&!w.in_enemy_spawn(e.p);});
    if(!tc.allow(24000))return std::nullopt;
    // The two linked bodies are one fate, even if only one takes damage.
    for(unsigned i=0;i<n;++i)if(sources[i])for(unsigned j=i+1;j<n;++j)if(sources[j]&&scene[i].side==scene[j].side) {
        auto a=sources[i]->sdk.champion_name(),b=sources[j]->sdk.champion_name();
        if((a==cambc::champion_type::cassi&&b==cambc::champion_type::issac)||
            (a==cambc::champion_type::issac&&b==cambc::champion_type::cassi)) {scene[i].linked=j;scene[j].linked=i;}
    }
    // Cache legal terrain locally: no SDK calls inside the rollout. Camps remain
    // impassable; unseen enemy champions remain uncertainty, never assumed dead.
    auto walkable=[&](int x,int y){vec2 p{x,y};return o.p.chebyshev_distance(p)<=12&&w.walkable(p)&&
        (!o.is_occupied(p)||p==o.p||std::any_of(scene.begin(),scene.begin()+n,[&](const auto& u){return u.x==x&&u.y==y;}));};
    auto actors=std::span<const combat::Unit>(scene.data(),n);
    auto budget=[&]{return tc.allow(12000)&&start-fuel_left()<26000;};
    const auto pessimistic=combat::project(actors,focus,true,walkable,4,false,0,0,budget);
    if(!pessimistic.valid)return std::nullopt;
    auto optimistic=pessimistic;
    if(start-fuel_left()<14000&&tc.allow(25000)) {
        auto alternative=combat::project(actors,focus,false,walkable,4,false,0,0,budget);
        if(alternative.valid)optimistic=alternative;
    }
    const bool endangered=pessimistic.self_hp<.25f*o.max_hp||pessimistic.self_death>=0;
    vec2 escape=o.p;float route=1e30f;
    for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy) {
        auto p=o.p+vec2{dx,dy};if(!w.walkable(p)||(p!=o.p&&o.is_occupied(p)))continue;
        float value=enemy_danger(p,o)+.25f*w.home.get(p);
        for(const auto& ally:o.allies)if(ally.hp>.5f*ally.max_hp)value+=.5f*p.chebyshev_distance(ally.p);
        if(value<route){route=value;escape=p;}
    }
    const float opportunity=4*std::max(.15f,m.economic_rate);
    const float fight_value=.5f*(optimistic.kill_value+pessimistic.kill_value)-
        .5f*(optimistic.death_value+pessimistic.death_value)-opportunity;
    if(endangered)return Goal{GoalKind::Retreat,-1,escape};
    const bool carrier=bank_now(o.bag,65535,o.submitted,cambc::constants::winning_gems);
    // A short forecast may defend a good exchange; it cannot justify a long
    // chase. Helpers participate only after actually moving into attack range.
    if(!carrier&&modeled_enemies==nearby_enemies&&pessimistic.self_hp>.4f*o.max_hp&&fight_value>0&&
        combat::distance(scene[0],scene[focus])<=5&&pessimistic.their_dead>0)
        return Goal{GoalKind::Fight,-1,vec2{scene[focus].x,scene[focus].y}};
    return Goal{GoalKind::Idle}; // Continue economy; do not invoke the old instant-DPS fight heuristic.
}
}
#endif
