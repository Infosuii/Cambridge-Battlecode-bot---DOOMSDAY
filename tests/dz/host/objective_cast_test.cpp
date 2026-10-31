#include "objective_model.h"
#include "timed_damage.h"
#include <cassert>
#include <iostream>
#include <random>
using namespace dz;
using namespace dz::objective;
int main() {
    std::mt19937 rng(721);
    // The independently derived closed-form reset clock and exposure sums do
    // not share the new simulator's per-turn loop or health/shield state.
    for(unsigned trial=0;trial<1500;++trial) {
        std::array<ClearMember,4> targets{};std::array<TimedDamageJob,4> jobs{};
        const unsigned period=1+rng()%12,cd=rng()%(period+1);const bool refresh=rng()%2;
        for(unsigned k=0;k<targets.size();++k) {
            const unsigned attacks=1+rng()%15;
            targets[k]={float(100*attacks),float(1+rng()%30)};
            jobs[k]={{attacks,refresh},targets[k].incoming};
        }
        Kit kit;kit.casts[0]={CastKind::Reset,cd,period};kit.refresh_on_monster=refresh;
        const auto direct=cast_clear(targets,100000,100000,100,kit,2000);
        const auto clock=timed_clear_damage(jobs,cd,period);
        assert(direct.status==CastStatus::Complete&&clock.clock.complete());
        assert(direct.rounds==clock.clock.rounds&&direct.attacks==clock.clock.rounds+clock.clock.resets);
        assert(direct.casts[0]==clock.clock.resets&&std::abs(direct.loss-clock.damage)<.01);
    }
    ClearMember target{500,100};Kit kit;
    kit.casts={Cast{CastKind::Reset,0,4},Cast{CastKind::Shield,0,4,2,200}};
    auto p=cast_clear(std::span<const ClearMember>(&target,1),1000,1000,100,kit);
    assert(p.status==CastStatus::Complete&&p.rounds==4&&p.loss==100&&p.casts[0]==1&&p.casts[1]==1);
    target.hp=700;kit.casts[0]={};
    p=cast_clear(std::span<const ClearMember>(&target,1),1000,1000,100,kit);
    assert(p.status==CastStatus::Complete&&p.rounds==7&&p.loss==200&&p.casts[1]==2);
    kit={};kit.casts[0]={CastKind::Damage,0,3,0,250};target.hp=350;
    p=cast_clear(std::span<const ClearMember>(&target,1),1000,1000,100,kit);
    assert(p.status==CastStatus::Complete&&p.rounds==1&&p.loss==0&&p.casts[0]==1);
    kit.can_cast=false;
    p=cast_clear(std::span<const ClearMember>(&target,1),1000,1000,100,kit);
    assert(p.status==CastStatus::Complete&&p.rounds==2&&p.loss==100);
    auto stopped=cast_clear(std::span<const ClearMember>(&target,1),1000,1000,100,kit,96,[]{return false;});
    assert(stopped.status==CastStatus::Budget&&stopped.rounds==0);
    kit.casts[0].amount=std::numeric_limits<float>::quiet_NaN();
    assert(cast_clear(std::span<const ClearMember>(&target,1),1000,1000,100,kit).status==CastStatus::Invalid);
    target={1000,100};kit={};kit.casts={Cast{CastKind::Reset,0,4},Cast{CastKind::Shield,0,4,2,200}};
    Actor actor{1000,1000,100,1};Encounter e{std::span<const ClearMember>(&target,1),14,240};
    const auto basic=forecast(e,std::span<const Actor>(&actor,1),0),active=forecast_casts(e,actor,kit);
    assert(!basic.survivable&&active.complete()&&active.survivable&&active.cast_policy&&active.opening_shield==200);
    assert(active.clear<basic.clear&&active.loss_upper[0]<basic.loss_upper[0]&&active.gems==basic.gems);
    const auto fallback=forecast_casts(e,actor,kit,[]{return false;});
    assert(!fallback.cast_policy&&fallback.loss_upper==basic.loss_upper&&fallback.clear==basic.clear);
    unsigned two=2;e.multiplicities=std::span<const unsigned>(&two,1);
    assert(!forecast_casts(e,actor,kit).cast_policy); // No unproven focus/geometry credit.
    e.multiplicities={};actor.arrival=4;kit.casts[1].cooldown=4;
    assert(forecast_casts(e,actor,kit).opening_shield==200);
    std::cout<<"1500 independent reset/exposure references; shield phases, cast collisions, arrival and fallback passed\n";
}
