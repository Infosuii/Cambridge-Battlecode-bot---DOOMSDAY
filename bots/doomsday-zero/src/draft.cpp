#include "draft.h"
#include "map_signature.h"
#include "v81_draft.h"

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
        using D=cambc::champion_draft;
        const unsigned supported=draft_value::physical(static_cast<unsigned>(D::vendetta))|
            draft_value::physical(static_cast<unsigned>(D::marcella))|draft_value::physical(static_cast<unsigned>(D::vesper_vale))|
            draft_value::physical(static_cast<unsigned>(D::heart_of_ruin))|draft_value::physical(static_cast<unsigned>(D::ryth));
        std::array<objective::Actor,13> actors{};
        for(unsigned b=0;b<actors.size();++b) {
            if(DZ_LIFECYCLE&&!(supported&(1u<<b)))continue;
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
            const auto members=groups[g].camps();if(members.empty())continue;
            int arrival=65535;float hp=0;
            for(const auto& camp:members){arrival=std::min(arrival,static_cast<int>(home.get(camp.spawn_position())));hp+=design(camp).base_health;}
            if(arrival>=65535)continue;
            const float value=groups[g].gem_value()+objective::gold_price(cambc::constants::max_rounds)*groups[g].gold_value();
            if(value>0)shortlist.push_back({g,arrival,value/(arrival+std::ceil(hp/std::max(1.f,actors[2].damage))+cambc::constants::capture_time+1)});
        }
        std::sort(shortlist.begin(),shortlist.end(),[](auto a,auto b){return a.bound>b.bound||(a.bound==b.bound&&a.group<b.group);});
        portfolio.count=std::min<unsigned>(draft_value::jobs,shortlist.size());
        for(unsigned j=0;j<portfolio.count;++j) {
            const auto job=shortlist[j];const auto& group=groups[job.group];std::array<ClearMember,clear_risk_members> targets{};
            std::array<unsigned,clear_risk_members> multiplicities{};unsigned n=0;
            bool cluster=true;
            for(const auto& camp:group.camps()) {
                const auto s=design(camp);unsigned k=0;
                while(k<n&&(targets[k].hp!=s.base_health||targets[k].incoming!=s.base_strength))++k;
                if(k==n){if(n==targets.size())return false;targets[n++]={s.base_health,s.base_strength};}
                ++multiplicities[k];cluster&=s.base_strength==0;
            }
            objective::Encounter encounter{std::span<const ClearMember>(targets.data(),n),static_cast<float>(group.gem_value()),static_cast<float>(group.gold_value())};
            encounter.multiplicities={multiplicities.data(),n};
            encounter.cluster=cluster;encounter.horizon=std::min(2000,static_cast<int>(cambc::constants::max_rounds));
            for(unsigned a=0;a<actors.size();++a)for(unsigned b=a;b<actors.size();++b) {
                if(DZ_LIFECYCLE&&(!(supported&(1u<<a))||!(supported&(1u<<b))))continue;
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
            if(DZ_LIFECYCLE&&pick!=static_cast<unsigned>(cambc::champion_draft::vendetta)&&
                pick!=static_cast<unsigned>(cambc::champion_draft::marcella)&&pick!=static_cast<unsigned>(cambc::champion_draft::vesper_vale)&&
                pick!=static_cast<unsigned>(cambc::champion_draft::heart_of_ruin)&&pick!=static_cast<unsigned>(cambc::champion_draft::ryth))continue;
            const auto score=evaluate(pick);if(!score.complete)break;
            if(score.value>value&&score.value>baseline.value*(DZ_LIFECYCLE?1.1f:1.f)){value=score.value;best=pick;}
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
#if DZ_LIFECYCLE
        // Exact current collision reference ca170a4d and documented packs
        // reference 1bf7d5f5: three complementary jobs, no Varg or linked pair.
        if(DZ_DRAFT_VARIANT==0&&(signature==3779302321u||signature==3765343063u))variant=1;
#endif
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
#if DZ_TRACE && DZ_TRACE_DRAFTMEM
        {
            cambc::draft_memory_buffer memory;
            const std::array<std::uint32_t, 2> probe{0x445a4d31u, signature}; // "DZM1", signature
            memory = probe;
            ::dz::TraceScope dz_trace_scope;
            ::dz::trace("DZ_DRAFTMEM_WRITE size=%zu signature=%u fuel=%llu\n", memory.size(), signature,
                static_cast<unsigned long long>(cambc::fuel_remaining()));
        }
#endif
#if DZ_TRACE
        {
        // C3 priority 7 (geometric selector): static map features, trace builds only. Computed outside the
        // TraceScope (metered work there counts against the trace cap and the line is dropped).
        auto centroid=[](cambc::team t){ long long x=0,y=0,n=0; for(auto p:cambc::map::spawn_region(t).positions()){x+=p.x;y+=p.y;++n;} return std::array<long long,2>{n?x/n:0,n?y/n:0}; };
        const auto a=centroid(cambc::team::ally), e=centroid(cambc::team::enemy);
        long long gems=0,gold=0,camps=0,groups=0,big=0,near_ally=0,near_mid=0; double hp=0;
        for (const auto& g:cambc::map::camp_groups()) {
            ++groups; gems+=g.gem_value(); gold+=g.gold_value(); const auto n=static_cast<long long>(g.camps().size()); camps+=n; if (n>=4) ++big;
            for (const auto& c:g.camps()) hp+=c.base_stats().base_health;
            const auto p=g.camps().empty()?cambc::vec2{0,0}:g.camps()[0].spawn_position();
            const long long da=(p.x-a[0])*(p.x-a[0])+(p.y-a[1])*(p.y-a[1]), de=(p.x-e[0])*(p.x-e[0])+(p.y-e[1])*(p.y-e[1]);
            if (da<de) ++near_ally;
            if (da*10<de*13&&de*10<da*13) ++near_mid;
        }
        long long altar_min=1<<30, altars=0;
        for (auto p:cambc::map::altars().positions()) { ++altars; altar_min=std::min(altar_min,static_cast<long long>(std::max(std::abs(p.x-a[0]),std::abs(p.y-a[1])))); }
        ::dz::TraceScope dz_trace_scope;
        ::dz::trace("DZ_MAPFEAT w=%d h=%d walls=%u holes=%u bushes=%u altars=%lld altar_min=%lld spawn_d=%lld groups=%lld big=%lld camps=%lld gems=%lld gold=%lld hp=%.0f near_ally=%lld mid=%lld\n",
            static_cast<int>(cambc::map::width()),static_cast<int>(cambc::map::height()),static_cast<unsigned>(cambc::map::walls().count()),
            static_cast<unsigned>(cambc::map::holes().count()),static_cast<unsigned>(cambc::map::bushes().count()),altars,altar_min,
            static_cast<long long>(std::max(std::abs(a[0]-e[0]),std::abs(a[1]-e[1]))),groups,big,camps,gems,gold,hp,near_ally,near_mid);
        }
#endif
    } catch (...) {}
#if DZ_DRAFT_MASTERY
    // F8 champion mastery: DZ's league results per champion (gems/1k rounds: Ryth 115, Marcella/Vendetta 80, Varg 73,
    // Vesper 70, Heart 48; deaths/game: Vendetta 5.1, Varg 4.7, Marcella 3.8). Lowest-yield champions last.
    (void)variant;
#if DZ_DRAFT_MASTERY == 2
    // Variant 2: Vendetta (most deaths, 5.1 a game) last.
    const Order order3{D::ryth, D::marcella, D::vesper_vale, D::varg, D::heart_of_ruin, D::vendetta};
#else
    const Order order3{D::ryth, D::marcella, D::vesper_vale, D::varg, D::vendetta, D::heart_of_ruin};
#endif
#else
    const Order order3 = variants[variant];
#endif
    Order order5 = order3;
#if DZ_DRAFT_MASTERY == 3
    // Variant 3: the mastery order for every team size and map (variants 1-2 kept the incumbent 5-pick order
    // wherever the incumbent map table chose variant 0).
#else
    if (variant == 0) order5 = {D::vendetta, D::varg, D::vesper_vale, D::marcella, D::heart_of_ruin, D::ryth};
#endif
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
#if DZ_DRAFT_NET
            if (const int choice = v81::draft_choice(cambc::draft::team_size()); choice >= 0) next = static_cast<D>(choice);
#endif
            act.pick(next); // Pick before any optional work, including shared initialization.
#if DZ_ECONOMY_V2 && DZ_LIFECYCLE
            publish_opening_cache(tc,act);
#endif
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
