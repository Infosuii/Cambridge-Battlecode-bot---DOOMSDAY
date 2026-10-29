#include "actions.h"
#include <cmath>

namespace dz {
float crew_strength(const Observation& obs, vec2 around, int radius) {
    float total=0;
    for (const auto& a:obs.allies) if (a.hp>0 && a.p.chebyshev_distance(around)<=radius) total+=a.strength;
    return total;
}
ClearRisk group_clear_risk(const StaticWorld& world, const Memory& mem, const Observation& obs, int index, float extra) {
    const auto& g=world.groups[index]; const auto& hp=mem.member_hp[index];
    if (hp.size()>clear_risk_members||g.initial_strength.size()!=hp.size()) return {};
    // Quantize damage down to a 5% grid. Heart of Ruin and Ryth strength moves
    // with health almost every turn; an exact key missed the cache constantly
    // and repricing every group cost ~50k fuel per turn. Rounding down never
    // overstates our damage, so feasibility stays conservative.
    const float raw=obs.strength*obs.camp_damage+extra;
    if (raw!=mem.quantize_raw) {
        mem.quantize_raw=raw;
        mem.quantize_out=raw>1 ? std::pow(1.05f,std::floor(std::log(raw)/std::log(1.05f))) : raw;
    }
    const float damage=mem.quantize_out;
    if (mem.risk_cache.size()!=world.groups.size()) mem.risk_cache.assign(world.groups.size(),{});
    // Slot 0 holds the solo price, slot 1 the latest crew price.
    auto& entry=mem.risk_cache[index][extra>0];
    const unsigned version=mem.hp_version[index];
    if (entry.version==version&&entry.damage==damage&&entry.factor==obs.camp_factor) {
#if DZ_TRACE
        ++::dz::turn_profile.acc[3];
#endif
        return entry.risk;
    }
#if DZ_TRACE
    ++::dz::turn_profile.acc[2];
#endif
    std::array<ClearMember,clear_risk_members> members;
    for (unsigned k=0;k<hp.size();++k) members[k]={std::max(0.f,hp[k]),g.initial_strength[k]*obs.camp_factor};
    entry={version,damage,obs.camp_factor,solo_clear_risk(std::span<const ClearMember>(members.data(),hp.size()),damage)};
    return entry.risk;
}
float enemy_danger(vec2 p, const Observation& obs) {
    float damage = 0;
    for (const auto& e : obs.enemies) {
        int distance = static_cast<int>(e.p.chebyshev_distance(p));
        if (distance <= e.range + 1) damage += e.strength;
        if (distance <= 6) damage += .25f * e.strength;
    }
    return damage;
}
float danger(vec2 p, const Observation& obs) {
    return enemy_danger(p,obs)+(config::camp_safety ? camp_damage({p.x,p.y},obs.camps) : 0);
}
bool channel_safe(const StaticWorld& world,const Observation& obs,const TurnContext& tc) {
    if (enemy_danger(cambc::self().position(),obs)>0) return false;
    const auto p=cambc::self().position();
    const auto awake=cambc::vision::awake_camp_tiles();
    for (const auto& g:world.groups) {
        if (g.strength<=0) continue;
        for (unsigned i=0;i<g.tiles.size();++i) {
            if ((i&15)==0&&!tc.allow(3500)) return false;
            if (g.initial_strength[i]>0 && p.chebyshev_distance(g.tiles[i])<=g.attack_ranges[i] &&
                (awake.is_set(g.tiles[i]) || !cambc::vision::in_vision(g.tiles[i]))) return false;
        }
    }
    return true;
}
namespace {
bool movable(vec2 p, const StaticWorld& w, const Observation& o) { return w.walkable(p) && !o.is_occupied(p); }
bool actionable(cambc::champion_state state) {
    return !state.is_dead() && !state.contains(cambc::champion_state::recalling) &&
        !state.contains(cambc::champion_state::submitting_gems) && !state.contains(cambc::champion_state::teleporting);
}
void ward_here(const Observation& obs,const TurnContext& tc,Actuator& act) {
    auto& me=cambc::self();
    if (me.ward_cooldown()!=0 || !tc.allow(2500) || obs.restrictions.contains(cambc::buff_restrictions::ward) || !actionable(me.state())) return;
    auto p=me.position();
    if (!cambc::map::altars().is_set(p) && !cambc::vision::ward_tiles(cambc::team::ally).is_set(p)) act.ward(p);
}
bool bank_here(Goal goal,const StaticWorld& world,Actuator& act) {
    if (goal.kind!=GoalKind::Bank || goal.index<0) return false;
    auto& me=cambc::self(); auto altar=world.altars[goal.index].tile;
    if (me.position().chebyshev_distance(altar)>cambc::constants::submit_gems_range) return false;
    // Query the enemy set explicitly: the convenience lookup prefers an allied
    // lock when both teams have a lock on the same altar.
    for (const auto& lock:cambc::vision::altar_locks(cambc::team::enemy)) if (lock.position()==altar) {
        if (me.can_attack()) act.attack(lock);
        return true;
    }
    act.bank(altar); return true;
}
// A bounded payload policy for SafeMode, independent of the later engagement model.
bool collateral_safe(vec2 center,float radius,int intended_group,const StaticWorld& world,const TurnContext& tc) {
    const int extent=static_cast<int>(std::ceil(radius));
    for (int dx=-extent;dx<=extent;++dx) {
        if (!tc.allow(3500)) return false;
        for (int dy=-extent;dy<=extent;++dy) {
            if (std::max(std::abs(dx),std::abs(dy))>radius) continue;
            int group=world.group_at(center+vec2{dx,dy});
            // Until multi-group pulls have a validated model, an area spell
            // must not wake an additional damaging group.
            if (group>=0 && group!=intended_group && world.groups[group].strength>0) return false;
        }
    }
    return true;
}
void spells(const cambc::unit* target, bool enemy, bool attacked, const Observation& obs,
            const StaticWorld& world,int intended_group,const TurnContext& tc, Actuator& act, bool preserve_move) {
    auto& me = cambc::self();
    for (auto ability : me.abilities()) {
        if (!tc.allow(3500) || !ability.is_ready() || !actionable(me.state())) continue;
        if (preserve_move && ability.info() && std::visit([](const auto& p) { return p.exclusive_with_movement; }, *ability.info())) continue;
        if (ability.is_attack_reset()) {
            if (attacked && target && target->is_visible() && target->health() > 0 &&
                me.position().chebyshev_distance(target->position()) <= me.attack_range()) {
                if (act.cast(ability) && me.can_attack()) act.attack(*target);
            }
            continue;
        }
        if (ability.is_shield()) {
            const bool damaging_target=target && (enemy || (intended_group>=0 && world.groups[intended_group].strength>0));
            if ((damaging_target || danger(obs.p,obs)>0) && obs.hp < .85f * obs.max_hp && !me.buffs().has<cambc::buff_shield>()) act.cast(ability);
            continue;
        }
        if (!target || !target->is_visible() || target->health() <= 0 || (!enemy && !obs.enemies.empty())) continue;
        if (!(ability.is_damage() || ability.is_cc() || ability.is_aoe_damage())) continue;
        if (enemy ? !ability.can_target_enemies() : !ability.can_target_camps()) continue;
        const auto p = target->position();
        if (!ability.valid_tiles().is_set(p)) continue;
        if (ability.is_aoe_damage() && !collateral_safe(p,std::get<cambc::ability_aoe_damage>(*ability.info()).radius,
            intended_group,world,tc)) continue;
        // CC against stun-immune Marcella has no control value; damaging CC still works.
        if (ability.is_cc() && ability.damage_amount() == 0 && enemy) {
            auto* c = dynamic_cast<const cambc::champion*>(target);
            if (c && c->champion_name() == cambc::champion_type::marcella) continue;
        }
        if (ability.can_target_ground() && ability.is_aoe_damage()) act.cast(ability, p);
        else act.cast(ability, *target);
    }
}
bool step(const cambc::distance_field& field, const StaticWorld& world, const Observation& obs,
          bool retreat, Actuator& act) {
    if (!cambc::self().can_move()) return false;
    const auto origin = cambc::self().position();
    vec2 best = origin;
    float score_best = 1e30f;
    // Prefer a strictly improving distance. Static fields are not used for collision avoidance.
    for (int dx = -1; dx <= 1; ++dx) for (int dy = -1; dy <= 1; ++dy) {
        auto p = origin + vec2{dx,dy};
        if (!world.walkable(p) || (p != origin && obs.is_occupied(p))) continue;
        int d = field.get(p);
        if (d == cambc::distance_field::unreachable) continue;
        float score = static_cast<float>(d) + danger(p, obs) * (retreat ? .08f : .015f);
        if (p == origin && d != 0) score += .2f;
        if (world.is_bush(p)) score -= .02f;
        if (score < score_best) { score_best = score; best = p; }
    }
    if (best != origin && act.move(best)) return field.get(best)<field.get(origin);
    return false;
}
}
void execute(Goal goal, StaticWorld& world, Memory& mem, const Observation& obs, const TurnContext& tc, Actuator& act) {
    auto& me = cambc::self();
#if DZ_TRACE
    if (world.slot==DZ_TRACE_SLOT && tc.round>=DZ_TRACE_FROM && tc.round<DZ_TRACE_TO)
        std::printf("DZ_EXEC round=%u enter kind=%d actionable=%d can_move=%d can_attack=%d fuel=%llu\n",tc.round,static_cast<int>(goal.kind),
            actionable(me.state()),me.can_move(),me.can_attack(),static_cast<unsigned long long>(cambc::fuel_remaining()));
#endif
    if (!actionable(me.state())) return;
    if (goal.kind==GoalKind::YieldSpawn) {
        if (me.can_move()&&tc.allow(world.field_budget()+4000)) {
            auto blocked=world.blocked|obs.occupied;
            auto roots=~(blocked|world.camp_spawns);
            cambc::distance_field field; field.compute(blocked,roots,world.visited);
            tc.guard(); step(field,world,obs,false,act);
        }
        return;
    }
    DZ_PROF(static_cast<char>('0'+static_cast<int>(goal.kind)));
    const bool retreat = goal.kind == GoalKind::Retreat || goal.kind == GoalKind::Home;
    const cambc::unit* target = nullptr;
    bool enemy = false;
    struct SpellReach { bool ready=false,exclusive=false,zero_stun=false; float range=0; };
    std::array<SpellReach,2> reach;
    unsigned spell=0;
    for (auto ability:me.abilities()) {
        auto& r=reach[spell++];
        if (!(ability.is_damage()||ability.is_cc()||ability.is_aoe_damage()) || !ability.can_target_enemies() || !ability.is_ready()) continue;
        std::visit([&](const auto& info) {
            r.ready=true; r.exclusive=info.exclusive_with_movement;
            if constexpr (requires{info.range;}) r.range=info.range;
            if constexpr (std::is_same_v<std::decay_t<decltype(info)>,cambc::ability_cc>) r.zero_stun=info.modifier==0;
        },*ability.info());
    }
    // Free melee hit while leaving; ranged attacks must not consume the escape move.
    float target_score = -1;
    for (auto& e : obs.enemies) {
        const auto distance=obs.p.chebyshev_distance(e.p);
        bool can_spell=false;
        for (auto r:reach) if (r.ready && distance<=r.range && !(retreat&&r.exclusive) &&
            !(r.zero_stun&&e.sdk.champion_name()==cambc::champion_type::marcella)) can_spell=true;
        const bool can_basic=distance<=obs.range && (!retreat||obs.range==1);
        if (!can_basic&&!can_spell) continue;
        float score = 1 / std::max(1.f, e.hp) + (e.hp <= obs.strength ? 10.f : 0.f);
        if (score > target_score) { target_score = score; target = &e.sdk; enemy = true; }
    }
    const cambc::camp* camp_target = nullptr;
    if (!target && goal.kind == GoalKind::Farm) {
        const auto& group = world.groups[goal.index];
        // Choose from static tiles, remembered HP and one visible-camp mask,
        // then query only the chosen camp. Five SDK calls per member made big
        // wolf packs cost tens of thousands of fuel per turn (02the-pack).
        // Damaging groups: strongest member first (cuts incoming damage soonest;
        // every crew member picks the same camp), then nearest, then weakest.
        LocalMask visible_camps; visible_camps.load(cambc::vision::camp_tiles());
        const auto& hp = mem.member_hp[goal.index];
        float best = 1e30f; int chosen = -1;
        for (unsigned k = 0; k < group.tiles.size() && k < hp.size(); ++k) {
            if (hp[k] <= 0 || !visible_camps.test(group.tiles[k])) continue;
            float score = static_cast<float>(obs.p.chebyshev_distance(group.tiles[k])) * 1000 + hp[k];
            if (group.strength > 0) score -= 1e6f * group.initial_strength[k];
            if (score < best) { best = score; chosen = static_cast<int>(k); }
        }
        if (chosen >= 0 && tc.allow(3500)) {
            const auto& c = group.sdk.camps()[chosen];
            if (c.is_visible() && !c.is_dead()) camp_target = &c;
        }
        target = camp_target;
        // Never wake a sleeping damaging group that the visible crew cannot
        // clear: asleep camps do not attack, so waiting beside them is safe.
        if (camp_target && group.strength>0 && camp_target->is_asleep() && !mem.legacy(tc.round)) {
            unsigned crew=1;
            for (const auto& a:obs.allies) if (a.hp>0 && a.p.chebyshev_distance(obs.p)<=4) ++crew;
            auto risk=group_clear_risk(world,mem,obs,goal.index,crew_strength(obs,obs.p,4));
            if (!clear_survivable(risk,obs.hp,obs.max_hp,crew_share(crew))) target=nullptr;
        }
    }
    if constexpr (config::camp_safety) {
        if (camp_target && camp_target->is_visible() && camp_target->is_asleep()) {
            const auto& g=world.groups[goal.index];
            float wake_damage=0;
            for (unsigned i=0;i<g.tiles.size();++i) {
                if (!tc.allow(5000)) return;
                if (mem.member_hp[goal.index][i]>0 && obs.p.chebyshev_distance(g.tiles[i])<=g.attack_ranges[i])
                    wake_damage+=g.initial_strength[i]*obs.camp_factor;
            }
            if (wake_damage>=obs.hp) {
                mem.release(tc.round);
                execute({GoalKind::Retreat},world,mem,obs,tc,act);
                return;
            }
        }
    }
    DZ_PROF('t');
    bool attacked = false;
    if (target && (!retreat||obs.range==1) && me.can_attack() && !obs.restrictions.contains(cambc::buff_restrictions::attack) &&
        obs.p.chebyshev_distance(target->position()) <= obs.range) attacked = act.attack(*target);
    spells(target, enemy, attacked, obs, world,enemy ? -1 : goal.index,tc, act, retreat);
    if (bank_here(goal,world,act)) return;
    if (goal.kind==GoalKind::Farm && mem.groups[goal.index].state==GroupState::Reward && world.group_at(me.position())==goal.index) {
        ward_here(obs,tc,act); return;
    }
    if (goal.kind==GoalKind::Home) {
        auto p=me.position();
        if (cambc::map::spawn_region(cambc::team::ally).is_set(p)) { ward_here(obs,tc,act); return; }
        if (world.home.get(p)>cambc::constants::recall_time+1 && channel_safe(world,obs,tc)) { act.recall(); return; }
    }
    if (goal.kind==GoalKind::Retreat && goal.destination && me.can_move()) {
        auto p=me.position(), end=*goal.destination;
        auto sign=[](int x){return (x>0)-(x<0);};
        auto next=p+vec2{sign(end.x-p.x),sign(end.y-p.y)};
        if (world.walkable(next) && !obs.is_occupied(next) && act.move(next)) return;
    }
    if (!tc.allow(world.field_budget())) {
#if DZ_TRACE
        if (world.slot==DZ_TRACE_SLOT && tc.round>=DZ_TRACE_FROM && tc.round<DZ_TRACE_TO)
            std::printf("DZ_EXEC round=%u low_budget fuel=%llu need=%llu\n",tc.round,
                static_cast<unsigned long long>(cambc::fuel_remaining()),static_cast<unsigned long long>(world.field_budget()));
#endif
        const cambc::distance_field* field=nullptr;
        if (goal.kind==GoalKind::Home||goal.kind==GoalKind::Retreat) field=&world.home;
        else if (goal.kind==GoalKind::Bank) field=world.altars[goal.index].field.get();
        else if (goal.kind==GoalKind::Farm) field=world.groups[goal.index].field.get();
        if (field&&me.can_move()&&tc.allow(5000+300*obs.camps.size())) {
            step(*field,world,obs,retreat,act);
        }
        bank_here(goal,world,act);
        return;
    }

    // Movement roots encode the role. Dynamic occupancy is included so a crowd
    // cannot cause permanent oscillation around a blocked shortest-path step.
    DZ_PROF('a');
    RootSet roots;
    auto blocked = world.blocked | obs.occupied;
    if (retreat) {
        if (goal.destination && world.walkable(*goal.destination) && !obs.is_occupied(*goal.destination)) roots.set(*goal.destination);
        else roots = cambc::map::spawn_region(cambc::team::ally) & ~blocked;
    } else if (goal.kind == GoalKind::Fight && goal.destination) {
        // Close to basic-attack range of the focus target.
        const auto pos = *goal.destination;
        for (int dx = -obs.range; dx <= obs.range; ++dx) for (int dy = -obs.range; dy <= obs.range; ++dy) {
            auto p = pos + vec2{dx,dy};
            if ((movable(p, world, obs) || p == obs.p) && p != pos) roots.set(p);
        }
    } else if (goal.kind == GoalKind::Bank && goal.index >= 0) {
        auto altar = world.altars[goal.index].tile;
        for (int dx = -1; dx <= 1; ++dx) for (int dy = -1; dy <= 1; ++dy) {
            auto p = altar + vec2{dx,dy};
            if (world.walkable(p) && (!obs.is_occupied(p) || p == obs.p)) roots.set(p);
        }
    } else if (goal.kind == GoalKind::Farm) {
        auto& g = world.groups[goal.index];
        if (mem.groups[goal.index].state == GroupState::Reward) {
            vec2 nearest = obs.p; int distance = 65535;
            for (unsigned k=0;k<g.tiles.size();++k) {
                if ((k&15)==0 && !tc.allow(5000)) break;
                const auto p=g.tiles[k];
                const auto d = static_cast<int>(p.chebyshev_distance(obs.p));
                if (d < distance && (movable(p, world, obs) || p == obs.p)) { nearest = p; distance = d; }
            }
            if (distance < 65535) roots.set(nearest);
        } else if (camp_target && camp_target->is_visible() && !camp_target->is_dead()) {
            auto pos = camp_target->position();
            for (int dx = -obs.range; dx <= obs.range; ++dx) for (int dy = -obs.range; dy <= obs.range; ++dy) {
                auto p = pos + vec2{dx,dy};
                if ((movable(p, world, obs) || p == obs.p) && p != pos) roots.set(p);
            }
        } else {
            // Unseen group: route toward the free neighbours of every live
            // member. Only the straight-line nearest member was used before;
            // behind a wall it had no walkable neighbour, roots were empty and
            // the champion never moved (DZ_STUCK, 02fields). Never wait on a
            // spawn tile of a respawning group: it delays the whole respawn.
            // The static boundary already excludes every spawn tile.
            if (const auto* approach = world.approach_tiles(goal.index, tc)) {
                for (auto p : *approach) if (!obs.is_occupied(p)) roots.set(p);
            } else {
                // Not built yet: the bounded nearest-member frontier (<= 9 roots).
                vec2 nearest = obs.p; int distance = 65535;
                for (unsigned member=0;member<g.tiles.size();++member) {
                    if (mem.member_hp[goal.index][member]<=0) continue;
                    const auto d = static_cast<int>(g.tiles[member].chebyshev_distance(obs.p));
                    if (d < distance) { nearest = g.tiles[member]; distance = d; }
                }
                if (distance < 65535)
                    for (int dx = -1; dx <= 1; ++dx) for (int dy = -1; dy <= 1; ++dy) {
                        auto p = nearest + vec2{dx,dy};
                        if (movable(p, world, obs) && !world.is_spawn(p)) roots.set(p);
                    }
            }
        }
    }
    // Last resort for a farm job: follow the group's static field.
    if (roots.is_empty() && goal.kind == GoalKind::Farm && world.groups[goal.index].field && me.can_move())
        step(*world.groups[goal.index].field, world, obs, false, act);
    DZ_PROF('r');
    bool bank_blocked = goal.kind == GoalKind::Bank && roots.is_empty();
    if (!roots.is_empty() && me.can_move()) {
        cambc::distance_field field;
        field.compute(blocked, roots.board(), world.visited);
        tc.guard();
        bank_blocked = goal.kind == GoalKind::Bank && field.get(obs.p) == cambc::distance_field::unreachable;
        if (!bank_blocked) step(field,world,obs,retreat,act);
#if DZ_TRACE
        if (world.slot==DZ_TRACE_SLOT && tc.round>=DZ_TRACE_FROM && tc.round<DZ_TRACE_TO)
            std::printf("DZ_EXEC round=%u kind=%d target=%d,%d visible_target=%d enemy=%d roots=%u dist_here=%d moved_to=%d,%d\n",tc.round,static_cast<int>(goal.kind),
                target?target->position().x:-1,target?target->position().y:-1,camp_target!=nullptr,enemy,static_cast<unsigned>(roots.count()),
                field.get(obs.p),me.position().x,me.position().y);
#endif
    }
#if DZ_TRACE
    else if (world.slot==DZ_TRACE_SLOT && tc.round>=DZ_TRACE_FROM && tc.round<DZ_TRACE_TO)
        std::printf("DZ_EXEC round=%u kind=%d no_move roots=%u can_move=%d target=%d,%d\n",tc.round,static_cast<int>(goal.kind),
            static_cast<unsigned>(roots.count()),me.can_move(),target?target->position().x:-1,target?target->position().y:-1);
#endif
    DZ_PROF('d');
    if (bank_blocked && me.can_move()) {
            int prerequisite = -1, nearest = 65535;
            const auto& altar_field = *world.altars[goal.index].field;
            // Only groups beside the altar can block it. Scanning every camp of
            // every group through the SDK cost up to 70k fuel (02the-pack).
            for (int index : world.altars[goal.index].near_groups) {
                if (!tc.allow(3000)) break;
                for (auto& c : world.groups[index].sdk.camps()) {
                    if (!tc.allow(3500)) break;
                    if (!c.is_visible() || c.is_dead()) continue;
                    auto p = c.position();
                    int distance = static_cast<int>(obs.p.chebyshev_distance(p));
                    if (distance < nearest && altar_field.get(p) < altar_field.get(obs.p)) {
                        prerequisite = index; nearest = distance;
                    }
                }
            }
            if (prerequisite >= 0 && tc.allow(world.field_budget() + 8000)) {
                mem.observe_group(world, prerequisite, tc);
                auto& b = mem.groups[prerequisite];
                mem.contract.start(prerequisite, tc.round, world.distance(prerequisite, obs.p), b.hp, b.capture);
                execute({GoalKind::Farm, prerequisite}, world, mem, obs, tc, act);
                return;
            }
            // Until the blocking camp is visible, advance along the static route.
            step(altar_field, world, obs, false, act);
    }
    // Refresh the attack allowance after movement: melee can close and hit in one
    // turn; ranged cannot. An exclusive spell also affects these live allowances.
    // Re-pick an enemy that is now in reach: the pre-move choice only saw
    // enemies that were already in range, so an approach never hit.
    if (!attacked && me.can_attack() && (!retreat||obs.range==1)) {
        const auto here=me.position();
        float best_score=-1;
        for (const auto& e:obs.enemies) {
            if (!e.sdk.is_visible() || e.sdk.health()<=0 || here.chebyshev_distance(e.sdk.position())>me.attack_range()) continue;
            const float hp=e.sdk.health();
            const float score=1/std::max(1.f,hp)+(hp<=obs.strength?10.f:0.f);
            if (score>best_score) { best_score=score; target=&e.sdk; enemy=true; }
        }
    }
    if (!attacked && target && (!retreat||obs.range==1) && target->is_visible() && target->health() > 0 && me.can_attack() &&
        me.position().chebyshev_distance(target->position()) <= me.attack_range()) {
        attacked = act.attack(*target);
        spells(target, enemy, attacked, obs, world,enemy ? -1 : goal.index,tc, act, retreat);
    }
    if (bank_here(goal,world,act)) return;
    if (goal.kind == GoalKind::Home && !cambc::map::spawn_region(cambc::team::ally).is_set(me.position()) &&
        world.home.get(me.position()) > cambc::constants::recall_time + 1 && channel_safe(world,obs,tc)) act.recall();
    ward_here(obs,tc,act);
}
}
