#include "draft.h"
#include "map_signature.h"
#if DZ_ECONOMY_V2
#include "draft_value.h"
#include "objective_model.h"
#endif

namespace dz {
#if DZ_ECONOMY_V2
namespace {
struct DraftProfile {
    draft_value::Portfolio portfolio;bool ready=false,attempted=false;
    bool build(const TurnContext& tc) {
        if(attempted)return ready;
        attempted=true;
        if(!tc.allow(150000))return false; // Only the boosted first draft turn.
        using C=cambc::champion_type;
        std::array<objective::Actor,13> actors{};
        for(unsigned b=0;b<actors.size();++b) {
            const auto& body=cambc::champion_designs[b];const auto stats=body.base_stats();
            auto& actor=actors[b];actor.hp=actor.max_hp=stats.base_health;actor.damage=stats.base_strength;
            actor.gold_multiplier=body.champion_name()==C::vesper_vale?1.33f:1.f;
            float extra=0;
            for(const auto& ability:body.abilities())if(ability.info())std::visit([&](const auto& p){
                if(p.max_cooldown<=0)return;
                if constexpr(std::is_same_v<std::decay_t<decltype(p)>,cambc::ability_attack_reset>)extra=std::max(extra,stats.base_strength/p.max_cooldown);
                else if constexpr(requires{p.modifier;}) {
                    if((ability.is_damage()||ability.is_cc())&&p.valid_targets.contains(cambc::ability_target_mask::camps)&&!p.exclusive_with_movement)
                        extra=std::max(extra,stats.base_focus*p.modifier/p.max_cooldown);
                }
            },*ability.info());
            actor.damage+=extra;actor.capture_rounds=cambc::constants::capture_time;
        }
        auto blocked=cambc::map::walls()|cambc::map::holes()|cambc::map::altars()|cambc::map::spawn_region(cambc::team::enemy);
        cambc::distance_field home;cambc::bitboard visited;home.compute(blocked,cambc::map::spawn_region(cambc::team::ally),visited);
        const auto groups=cambc::map::camp_groups();
        struct Job {unsigned group;int arrival;float bound;};std::vector<Job> shortlist;
        std::array<cambc::camp_stats,6> designs{};std::array<bool,6> known{};
        auto design=[&](const cambc::camp& camp) {
            const auto kind=static_cast<unsigned>(camp.kind());
            if(kind>=designs.size())throw std::logic_error("unsupported camp design in draft");
            if(!known[kind]){designs[kind]=camp.base_stats();known[kind]=true;}return designs[kind];
        };
        for(unsigned g=0;g<groups.size();++g) {
            if(!tc.allow(15000))return false;
            const auto members=groups[g].camps();if(members.empty()||members.size()>32)continue;
            int arrival=0;float hp=0;
            for(const auto& camp:members){arrival=std::max(arrival,static_cast<int>(home.get(camp.spawn_position())));hp+=design(camp).base_health;}
            if(arrival>=65535)continue;
            const float value=groups[g].gem_value()+objective::gold_price(cambc::constants::max_rounds)*groups[g].gold_value();
            if(value>0)shortlist.push_back({g,arrival,value/(arrival+std::ceil(hp/std::max(1.f,actors[2].damage))+cambc::constants::capture_time+1)});
        }
        std::sort(shortlist.begin(),shortlist.end(),[](auto a,auto b){return a.bound>b.bound||(a.bound==b.bound&&a.group<b.group);});
        portfolio.count=std::min<unsigned>(draft_value::jobs,shortlist.size());
        for(unsigned j=0;j<portfolio.count;++j) {
            const auto job=shortlist[j];const auto& group=groups[job.group];std::array<ClearMember,32> targets{};unsigned n=0;
            bool cluster=true;
            for(const auto& camp:group.camps()) {const auto s=design(camp);targets[n++]={s.base_health,s.base_strength};cluster&=camp.is_gold_cluster()||camp.is_gem_cluster();}
            objective::Encounter encounter{std::span<const ClearMember>(targets.data(),n),static_cast<float>(group.gem_value()),static_cast<float>(group.gold_value())};
            encounter.cluster=cluster;encounter.horizon=std::min(2000,static_cast<int>(cambc::constants::max_rounds));
            for(unsigned a=0;a<actors.size();++a)for(unsigned b=a;b<actors.size();++b) {
                if(!tc.allow(10000))return false;
                std::array<objective::Actor,2> crew{actors[a],actors[b]};crew[0].arrival=crew[1].arrival=job.arrival;
                const unsigned count=a==b?1:2,cap=crew[1].gold_multiplier>crew[0].gold_multiplier&&count==2?1:0;
                const auto quote=objective::forecast(encounter,std::span<const objective::Actor>(crew.data(),count),cap);
                if(quote.complete()&&quote.survivable)portfolio.rates[j][a][b]=quote.reward(objective::gold_price(cambc::constants::max_rounds))/std::max(1,quote.finish);
            }
        }
        tc.guard();ready=true;return true;
    }
    std::optional<cambc::champion_draft> next(std::span<const cambc::champion_draft> selected,cambc::champion_draft prior,const TurnContext& tc) const {
        if(!ready)return {};
        unsigned roster=0,used=0;for(auto p:selected){const unsigned pick=static_cast<unsigned>(p);roster|=draft_value::physical(pick);used|=1u<<pick;}
        const auto began=fuel_left();auto budget=[&]{return tc.allow(5000)&&began-fuel_left()<35000;};
        auto evaluate=[&](unsigned pick){return portfolio.score(roster|draft_value::physical(pick),budget);};
        const unsigned incumbent=static_cast<unsigned>(prior);auto baseline=evaluate(incumbent);if(!baseline.complete)return {};
        unsigned best=incumbent;float value=baseline.value;
        for(unsigned pick=0;pick<draft_value::picks;++pick)if(!(used&(1u<<pick))&&pick!=incumbent&&
            pick!=static_cast<unsigned>(cambc::champion_draft::varg)) {
            const auto score=evaluate(pick);if(!score.complete)break;
            if(score.value>value){value=score.value;best=pick;}
        }
        return static_cast<cambc::champion_draft>(best);
    }
};
}
#endif
void draft_loop(Counters& counts) {
    using D = cambc::champion_draft;
    // Research prior only; map-conditioned exhaustive utility is a later gate.
    // All three sizes have a legal frontline, damage/reset kit and banker.
    // Candidate lineups for the per-map draft study (DZ_DRAFT_VARIANT):
    // 4 Willow core; 5 Prism/Tavi; 6 linked duo core; 7 Ryth/Tavi.
    // Research sets define candidates only; defaults/table remain unchanged.
    // 0 current prior; 1 elite core Vesper/Heart/Vendetta/Marcella; 2 Ryth/
    // Vendetta/Marcella (beat the core on arena/fragment); 3 Vesper/Vendetta/Ryth.
    using Order = std::array<D,6>;
    constexpr std::array<Order,((DZ_DRAFT_VARIANT>=4||DZ_MAP_DRAFT_EXTRA||DZ_MAP_DRAFT_MATRIX||DZ_PLAN_TABLE) ? 8 : 4)> variants{{
        {D::vendetta, D::marcella, D::vesper_vale, D::heart_of_ruin, D::ryth, D::tavi},
        {D::vesper_vale, D::heart_of_ruin, D::vendetta, D::marcella, D::ryth, D::tavi},
        {D::ryth, D::vendetta, D::marcella, D::vesper_vale, D::heart_of_ruin, D::tavi},
        {D::vesper_vale, D::vendetta, D::ryth, D::marcella, D::heart_of_ruin, D::tavi}
#if DZ_DRAFT_VARIANT >= 4 || DZ_MAP_DRAFT_EXTRA || DZ_MAP_DRAFT_MATRIX || DZ_PLAN_TABLE
        ,{D::vesper_vale, D::vendetta, D::marcella, D::willow, D::heart_of_ruin, D::ryth},
        {D::vesper_vale, D::prism, D::marcella, D::tavi, D::heart_of_ruin, D::vendetta},
        {D::vesper_vale, D::vendetta, D::cassi_and_issac, D::marcella, D::heart_of_ruin, D::ryth},
        {D::ryth, D::vendetta, D::marcella, D::tavi, D::heart_of_ruin, D::vesper_vale}
#endif
    }};
    static_assert([&] {
        for (const auto& order:variants)for(unsigned i=0;i<order.size();++i) {
            if(order[i]==D::varg)return false;
            for(unsigned j=0;j<i;++j)if(order[i]==order[j])return false;
        }
        return true;
    }(),"DZ lineups must contain unique non-Varg picks");
    // Per-map variant table (signature -> variant), chosen by
    // tools/dz_draft_select.py using the old lineup definitions. The rows require
    // fresh validation after removing Varg from the variant lineups. Empty = default.
    struct MapDraft { std::uint32_t signature; std::uint8_t variant; };
    static constexpr MapDraft map_drafts[] = {
#include "map_drafts.inc"
    };
    // A future table must not index an experiment compiled out of this build.
    static_assert([] {
        for (const auto& row : map_drafts)
            if (row.variant >= ((DZ_DRAFT_VARIANT>=4||DZ_MAP_DRAFT_EXTRA||DZ_MAP_DRAFT_MATRIX||DZ_PLAN_TABLE) ? 8 : 4)) return false;
        return true;
    }());
    static_assert(!(DZ_MAP_DRAFT_EXTRA && DZ_MAP_DRAFT_MATRIX));
    static_assert(DZ_DRAFT_VARIANT >= 0 && DZ_DRAFT_VARIANT < 8);
    int variant = DZ_DRAFT_VARIANT;
    try {
        const auto signature = map_signature(); // First draft turn: 10x budget.
        for (const auto& row : map_drafts) if (row.signature == signature && DZ_DRAFT_VARIANT == 0 && DZ_MAP_DRAFT_TABLE) variant = row.variant;
#if DZ_MAP_DRAFT_MATRIX
        static constexpr MapDraft matrix[] = {
#include "map_drafts_matrix.inc"
        };
        static_assert([] { for(const auto& row:matrix)if(row.variant>=8)return false;return true; }());
        for(const auto& row:matrix)if(row.signature==signature && DZ_DRAFT_VARIANT==0)variant=row.variant;
#endif
#if DZ_MAP_DRAFT_EXTRA
        static constexpr MapDraft extra[] = {
#include "map_drafts_extra.inc"
        };
        static_assert([] { for(const auto& row:extra)if(row.variant>=8)return false;return true; }());
        for(const auto& row:extra)if(row.signature==signature && DZ_DRAFT_VARIANT==0)variant=row.variant;
#endif
#if DZ_PLAN_TABLE
        load_plan(signature);
        if (DZ_DRAFT_VARIANT == 0 && plan_draft >= 0 && plan_draft < 8) variant = plan_draft;
#endif
#if DZ_TRACE
        { ::dz::TraceScope dz_trace_scope;
        ::dz::trace("DZ_SIG signature=%u variant=%d\n", signature, variant);
        }
#endif
    } catch (...) {}
    const Order order3 = variants[variant];
    Order order5 = order3;
    // Variant 0 now uses the same meta-core order for all team sizes.
    bool initialized = false;
#if DZ_ECONOMY_V2
    DraftProfile profile;std::optional<D> prepared;
#endif
    for (;;) {
        const auto tc = TurnContext::begin(); Actuator act(tc, counts);
        try {
            auto picks = cambc::draft::current_draft(cambc::team::ally);
            const auto& order = cambc::draft::team_size() == 3 ? order3 : order5;
            auto next = order.front();
            for (auto option : order) if (std::find(picks.begin(), picks.end(), option) == picks.end()) { next = option; break; }
#if DZ_ECONOMY_V2
            if(prepared&&std::find(picks.begin(),picks.end(),*prepared)==picks.end())next=*prepared;
#endif
            act.pick(next); // Pick before any optional work, including shared initialization.
            if (!initialized) initialized = act.publish(protocol::empty_word());
#if DZ_ECONOMY_V2
            prepared.reset();
            if(variant==0&&picks.size()+1<cambc::draft::team_size()&&profile.build(tc)) {
                picks.push_back(next);auto prior=order.front();
                for(auto option:order)if(std::find(picks.begin(),picks.end(),option)==picks.end()){prior=option;break;}
                prepared=profile.next(picks,prior,tc);
#if DZ_TRACE
                if(prepared){TraceScope scope;trace("DZ_DRAFT_PORTFOLIO round=%u picked=%u next=%u jobs=%u\n",tc.round,
                    static_cast<unsigned>(next),static_cast<unsigned>(*prepared),profile.portfolio.count);}
#endif
            }
#endif
        } catch (const StaleTurn&) { ++counts.stale; continue; }
        catch (const std::exception& error) {
            ++counts.module_errors;
#if DZ_TRACE
            { ::dz::TraceScope dz_trace_scope;
            ::dz::trace("DZ_MODULE_ERROR round=%u module=draft %s\n",tc.round,error.what());
            }
#endif
        }
        catch (...) {
            ++counts.module_errors;
#if DZ_TRACE
            { ::dz::TraceScope dz_trace_scope;
            ::dz::trace("DZ_MODULE_ERROR round=%u module=draft unknown exception\n",tc.round);
            }
#endif
        }
        if (cambc::round_number() != tc.round) continue;
        dz::end_turn_traced();
    }
}
}
