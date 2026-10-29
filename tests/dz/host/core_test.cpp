#include "core.h"
#include "protocol.h"
#include "camp_threat.h"
#include "ledger.h"
#include "basic_clear.h"
#include <cassert>
#include <iostream>
#include <limits>

int main() {
    using namespace dz;
    assert(!action_budget_available(5000,ActionBudget::Normal));
    assert(action_budget_available(5000,ActionBudget::Emergency));
    assert(!action_budget_available(1800,ActionBudget::Emergency));
    assert(action_budget_available(1801,ActionBudget::Emergency));
    std::array<BasicTarget,12> cluster;
    cluster.fill({120,80});
    assert(basic_attack_work(cluster).attacks==24); // Aggregated HP / damage wrongly gives 18.
    assert(basic_attack_work(cluster,23).status==WorkStatus::BeyondHorizon);
    assert(basic_attack_work(std::span<const BasicTarget>{},0).complete());
    const BasicTarget dead[]{ {0,0} };
    assert(basic_attack_work(dead,0).complete());
    for (float hp:{-1.f,std::numeric_limits<float>::infinity(),std::numeric_limits<float>::quiet_NaN()}) {
        const BasicTarget bad[]{ {hp,80} };
        assert(basic_attack_work(bad).status==WorkStatus::Invalid);
    }
    for (float damage:{0.f,-1.f,std::numeric_limits<float>::infinity()}) {
        const BasicTarget bad[]{ {120,damage} };
        assert(basic_attack_work(bad).status==WorkStatus::Invalid);
    }
    const BasicTarget huge[]{ {std::numeric_limits<float>::max(),std::numeric_limits<float>::denorm_min()} };
    assert(basic_attack_work(huge).status==WorkStatus::BeyondHorizon);
    const BasicTarget invalid_tail[]{ {1e30f,1.f},{-1,1} };
    assert(basic_attack_work(invalid_tail).status==WorkStatus::Invalid);
    for (int hp=1;hp<=400;++hp) for (int damage=1;damage<=90;++damage) {
        int remaining=hp,count=0;
        while (remaining>0) { remaining-=damage; ++count; }
        const BasicTarget target[]{ {static_cast<float>(hp),static_cast<float>(damage)} };
        auto got=basic_attack_work(target);
        assert(got.complete()&&got.attacks==static_cast<unsigned>(count));
    }
    const BasicTarget below[]{ {std::nextafter(160.f,0.f),80} },exact[]{ {160,80} },above[]{ {std::nextafter(160.f,200.f),80} };
    assert(basic_attack_work(below).attacks==2&&basic_attack_work(exact).attacks==2&&basic_attack_work(above).attacks==3);
    auto wolf=stationary_duel(1000,{1350,70},20);
    assert(wolf.work.attacks==20&&wolf.future_damage_for_clear==380&&wolf.survives);
    auto boundary=stationary_duel(60,{140,70},60);
    assert(!boundary.survives&&stationary_duel(61,{140,70},60).survives);
    assert(stationary_duel(1,{70,70},200).survives); // A kill this turn prevents retaliation next turn.
    assert(!stationary_duel(1000,{2400,70},60).survives);
    assert(stationary_duel(0,{70,70},0).work.status==WorkStatus::Invalid);
    static_assert(tier_for(60000) == Tier::Full);
    static_assert(tier_for(59999) == Tier::Lean);
    static_assert(tier_for(24999) == Tier::Fallback);
    unsigned checks = 0;
    const std::uint64_t sentinel = 0xa5379876543210ffULL;
    for (unsigned index = 0; index < protocol::slots; ++index) for (unsigned obj = 0; obj < 128; ++obj)
        for (bool onsite : {false, true}) {
            auto word = protocol::with_slot(sentinel, index, {static_cast<std::uint8_t>(obj), onsite});
            const auto got = protocol::slot(word, index);
            assert(got.objective == obj && got.onsite == onsite);
            assert((word >> 48) == (sentinel >> 48));
            for (unsigned other = 0; other < protocol::slots; ++other) if (other != index) {
                assert(protocol::slot(word, other).objective == protocol::slot(sentinel, other).objective);
                assert(protocol::slot(word, other).onsite == protocol::slot(sentinel, other).onsite);
            }
            ++checks;
        }
    for (unsigned i = 0; i < 6; ++i) assert(protocol::slot(protocol::empty_word(), i).objective == protocol::idle);
    assert(protocol::group_code(111) == 111 && protocol::group_code(112) == protocol::idle);
    assert(protocol::with_slot(sentinel, 6, {0,false}) == sentinel);
    bool stale = false, action_ran = false;
    try { require_current(4, [] { return 5u; }); action_ran = true; } catch (const StaleTurn&) { stale = true; }
    assert(stale && !action_ran);
    require_current(5, [] { return 5u; });
    ModuleHealth broken,healthy; unsigned attempts=0,reports=0,healthy_runs=0;
    for (unsigned i=0;i<8;++i) {
        assert(!guarded_module(broken,[&] { ++attempts; throw std::runtime_error("controlled failure"); },[&](const char*) { ++reports; }));
        assert(guarded_module(healthy,[&] { ++healthy_runs; },[](const char*) { assert(false); }));
    }
    assert(attempts==3 && reports==3 && !broken.enabled() && healthy_runs==8 && healthy.enabled());
    try { guarded_module(healthy,[]{throw StaleTurn{};},[](const char*){assert(false);}); assert(false); }
    catch (const StaleTurn&) {}
    assert(healthy.failures==0); // Budget suspension is not a broken module.
    ActionHistory actions;
    assert(actions.may_cast(true, false, false, true));
    actions.record_move(false); // Hidden obstruction keeps the allowance.
    assert(actions.may_cast(true, false, false, true));
    actions.record_move(true);
    assert(!actions.may_cast(true, false, false, true));
    assert(actions.may_cast(true, false, false, false)); // Shield/reset can follow movement.
    actions = {};
    actions.record_cast(false, true);
    assert(actions.may_move(true, false, false));
    actions.record_cast(true, true);
    assert(!actions.may_move(true, false, false));
    assert(!actions.may_cast(true, false, false, false));
    actions = {};
    actions.record_cast(true, false);
    assert(actions.may_move(true, false, false));
    assert(!actions.may_move(false, false, false)); // Ranged attack removed engine move allowance.
    assert(!actions.may_move(true, true, false));
    assert(!actions.may_move(true, false, true));
    actions = {};
    assert(!actions.may_cast(false, false, false, false));
    assert(!actions.may_cast(true, true, false, false));
    assert(!actions.may_cast(true, false, true, false));
    Contract contract;
    contract.start(2, 0, 20, 500, 5);
    assert(contract.progressing(5, 20, 500, 5));
    assert(!contract.progressing(6, 20, 500, 5));
    assert(contract.progressing(6, 19, 500, 5));
    assert(contract.progressing(11, 19, 400, 5));
    assert(contract.progressing(16, 19, 400, 4));
    assert(!contract.progressing(22, 19, 400, 4));
    GroupBelief b; b.state = GroupState::Partial; b.hp = 123;
    assert(b.available(100) && b.hp == 123); // Unattended partial HP is retained.
    b.state = GroupState::Respawning; b.ready = 150;
    assert(!b.available(149) && b.available(150));
    assert(!bank_now(0, 0, 999, 1000));
    assert(bank_now(1, 40, 999, 1000));
    assert(bank_now(30, 40, 0, 1000));
    assert(bank_now(1, 8, 0, 1000));
    assert(!bank_now(29, 9, 0, 1000));
    std::array threats{CampThreat{{0,0},60,4}};
    auto exit=camp_escape(Tile{1,0},threats,[](Tile,int){return true;});
    assert(exit.found && exit.steps==4 && exit.damage==180);
    assert(camp_damage(exit.exit,threats)==0);
    assert(must_escape_camps(240,60,180) && !must_escape_camps(241,60,180));
    auto no_exit=camp_escape(Tile{1,0},threats,[](Tile,int){return false;});
    assert(!no_exit.found);
    auto blocked_exit=camp_escape(Tile{1,0},threats,[](Tile p,int){return !(p.x==3 && p.y==0);});
    assert((blocked_exit.found && blocked_exit.exit!=Tile{5,0}));
    auto no_budget=camp_escape(Tile{1,0},threats,[](Tile,int){return true;},[]{return false;});
    assert(!no_budget.found && no_budget.truncated);
    std::array pair{CampThreat{{0,0},60,4},CampThreat{{0,0},120,4}};
    assert(camp_damage({1,1},pair)==180);
    assert(camp_damage({5,1},pair)==0);
    GroupBelief ledger; std::vector<float> initial{120,120},known=initial;
    apply_group_sample(ledger,known,initial,{GroupState::Alive,0,65535,{10.f,std::nullopt}},10);
    assert(ledger.state==GroupState::Partial && ledger.hp==130);
    apply_group_sample(ledger,known,initial,{GroupState::Alive,0,65535,{std::nullopt,20.f}},20);
    assert(ledger.hp==30 && known[0]==10);
    // Unseen capture+respawn: HP increasing proves a new generation; hidden
    // members must not retain old generation damage.
    apply_group_sample(ledger,known,initial,{GroupState::Alive,0,65535,{120.f,std::nullopt}},100);
    assert(ledger.state==GroupState::Alive && ledger.hp==240 && known[1]==120);
    apply_group_sample(ledger,known,initial,{GroupState::Reward,0,3,{std::nullopt,std::nullopt}},110);
    assert(ledger.hp==0 && known[0]==0 && known[1]==0 && ledger.capture==3);
    apply_group_sample(ledger,known,initial,{GroupState::Alive,0,65535,{100.f,std::nullopt}},170);
    assert(ledger.hp==220 && known[1]==120);
    apply_group_sample(ledger,known,initial,{GroupState::Respawning,30,65535,{std::nullopt,std::nullopt}},180);
    assert(ledger.ready==210 && ledger.hp==240);
    std::cout << checks << " protocol cases; guard, contract, ledger and bank checks passed\n";
}
