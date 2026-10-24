// Entry point: dispatch draft and gameplay turns; errors are logged and the turn still ends.
#include <iostream>

#include "bot.h"
#include "draft.h"
#include "nn_config.h"
#if NN_ANY_HEAD
#include "nn_budget.h"
#include "nn_head.h"
#endif

#if A2_LAB && !NN_STRIP_LAB // lab host exports (NN_STRIP_LAB removes them)
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
#if A2_FUELLOG
    // Diagnostics only: a turn that is still running when the round advances ran out of fuel and lost the next turn.
    std::uint32_t turns = 0, overruns = 0;
#endif
    while (true) {
        try {
            if (bc::is_draft()) {
#if NN_ANY_HEAD
                nnb::begin_turn(); // per-turn credit/budget reset also on draft turns (draft decisions read teacher_left)
#endif
                play_draft();
#if NN_ANY_HEAD
                nnh::warmup(); // after the draft decision: verify installed model checksums with the 10x draft fuel
#endif
            }
#if A2_FUELLOG
            else {
                const std::uint32_t r0 = bc::round_number();
                bot.play_turn();
                ++turns;
                if (bc::round_number() != r0) {
                    ++overruns;
                    std::printf("fuellog overrun round %u type %d\n", r0, static_cast<int>(bc::self().champion_name()));
                }
                if (r0 % 250 == 0) std::printf("fuellog round %u turns %u overruns %u\n", r0, turns, overruns);
            }
#else
            else {
#if NN_ANY_HEAD
                // Neural runtime turn hooks (lead): reset per-turn budget/context, selftest/telemetry/markers; at the
                // end, flush queued training records from leftover fuel only. Compiled out when every head is off.
                nnb::begin_turn();
                {
                    nnb::CreditScope scope; // turn hooks are neural overhead: credited back in neutral_credit
                    nnh::turn_start();
                }
                bot.play_turn();
                nnh::idle();
#else
                bot.play_turn();
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
