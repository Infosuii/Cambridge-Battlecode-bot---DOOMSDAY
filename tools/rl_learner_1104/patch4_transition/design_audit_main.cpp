// Entry point: dispatch draft and gameplay turns; errors are logged and the turn still ends.
#include <iostream>

#include "bot.h"
#include "draft.h"

#if A2_LAB
#include "learner.h"
// Engine lab: the host finds the learner weights through this export.
extern "C" __attribute__((export_name("lab_learner_w"))) float* lab_learner_w() { return learner::w_lab; }
#include "lab.h"
extern "C" __attribute__((export_name("lab_ctl"))) lab::Ctl* lab_ctl() { return &lab::ctl; }
extern "C" __attribute__((export_name("lab_knobs"))) float* lab_knobs() { return lab::knobs; }
extern "C" __attribute__((export_name("lab_pol_w"))) float* lab_pol_w() { return lab::pol_w; }
extern "C" __attribute__((export_name("lab_pol_cfg"))) std::int32_t* lab_pol_cfg() { return lab::pol_cfg; }
extern "C" __attribute__((export_name("lab_pol_log"))) float* lab_pol_log() { return lab::pol_log; }
extern "C" __attribute__((export_name("lab_macro_feat"))) float* lab_macro_feat() { return lab::macro_feat; }
extern "C" __attribute__((export_name("lab_cn_w"))) float* lab_cn_w() { return lab::cn_w; }
extern "C" __attribute__((export_name("lab_cn_cfg"))) std::int32_t* lab_cn_cfg() { return lab::cn_cfg; }
extern "C" __attribute__((export_name("lab_cn_force"))) std::int32_t* lab_cn_force() { return lab::cn_force; }
extern "C" __attribute__((export_name("lab_cn_log"))) float* lab_cn_log() { return lab::cn_log; }
extern "C" __attribute__((export_name("lab_builds"))) std::int32_t* lab_builds() { return lab::builds; }
#endif

int main() {
    Bot bot;
    for(int i=0;i<13;++i){
        bc::detail::champion_design design{};
        bc::detail::check(bc::detail::sdk_champion_design(i,&design));
        const auto& x=design.base_stats;
        std::printf("JDS1 %d %.9g %.9g %.9g %.9g %.9g %.9g\n",i,double(x.base_health),double(x.base_strength),double(x.base_focus),double(x.health_growth),double(x.strength_growth),double(x.focus_growth));
    }
    for(const auto it:{bc::item_type::skirmish_emblem_of_strength,bc::item_type::greed_emblem_of_strength}){
        const auto x=it.info();
        std::printf("JDI1 %u %d %d %d %.9g %u %u\n",static_cast<unsigned>(it),x.health_points,x.strength_points,x.focus_points,double(x.passive_magnitude),x.cost,x.combine_count);
    }
    std::fflush(stdout);

#if A2_FUELLOG
    // Diagnostics only: a turn that is still running when the round advances ran out of fuel and lost the next turn.
    std::uint32_t turns = 0, overruns = 0;
#endif
    while (true) {
        try {
            if (bc::is_draft()) {
                play_draft();
#if V58_DIRECTOR
                economy_record_roster();
#endif
            }
#if A2_FUELLOG
            else {
                const std::uint32_t r0 = bc::round_number();
                bot.play_turn();
#ifdef CLNA_EPS
                bot.clna_end();
#endif
#if defined(A2_NN_PIPE) && A2_NN_PIPE
                bot.nn_pipe_step();
#endif
#if defined(A2_NN_LIVE) && A2_NN_LIVE
                bot.nn_turn_end();
#endif
#ifdef CLNA_HEAD
                bot.clna_turn_end();
#endif
                ++turns;
                if (bc::round_number() != r0) {
                    ++overruns;
                    std::printf("fuellog overrun round %u type %d\n", r0, static_cast<int>(bc::self().champion_name()));
                }
                if (r0 % 250 == 0) std::printf("fuellog round %u turns %u overruns %u\n", r0, turns, overruns);
            }
#else
            else {
                bot.play_turn();
#ifdef CLNA_EPS
                bot.clna_end();
#endif
#if A2_NN_MACRO && defined(A2_NN_RL)
                bot.nn_rl_end();
#endif
#if defined(A2_NN_PIPE) && A2_NN_PIPE
                bot.nn_pipe_step();
#endif
#if defined(A2_NN_LIVE) && A2_NN_LIVE
                bot.nn_turn_end();
#endif
#ifdef CLNA_HEAD
                bot.clna_turn_end();
#endif
            }
#endif
        } catch (const std::exception& error) {
            std::printf("bot error: %s\n", error.what());
        } catch (...) {
            std::printf("bot error: unknown exception\n");
        }
        bc::end_turn();
    }
}
