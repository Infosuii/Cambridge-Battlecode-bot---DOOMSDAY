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

#if JD_FUELPROBE
// JD_FUELPROBE (diagnostic only): per unit turn, the phase (D draft turn k of this VM; C first play turn of this VM;
// X dead turn; R first live turn after dead turns; O ordinary), fuel at entry and exit, whether the turn crossed into
// a later round, and on the first play turn whether a global written by a draft turn is visible in this VM, the
// draft-memory snapshot size/magic and host-call cost samples.
namespace jdfp {
inline std::uint32_t draft_turns = 0, play_turns = 0;
inline int was_dead = 0;
inline bool sampled = false;
inline volatile std::uint32_t draft_marker = 0;
inline std::int64_t round_or_neg() {
    try {
        return static_cast<std::int64_t>(bc::round_number());
    } catch (...) {
        return -1;
    }
}
inline void host_samples() {
    // Cost of one fuel_remaining() call, a bitboard AND and a full-map distance field from our spawn.
    const std::uint64_t a = bc::fuel_remaining(), b = bc::fuel_remaining();
    const bc::bitboard& walls = bc::map::walls();
    const std::uint64_t c = bc::fuel_remaining();
    bc::bitboard blocked = walls | bc::map::holes();
    const std::uint64_t d = bc::fuel_remaining();
    bc::distance_field f;
    bc::bitboard visited;
    f.compute(blocked, bc::map::spawn_region(team::ally), visited, 1000);
    const std::uint64_t e = bc::fuel_remaining();
    std::printf("JDFP H fr %llu walls %llu or %llu df %llu chunks %llu w %d h %d\n", static_cast<unsigned long long>(a - b),
        static_cast<unsigned long long>(b - c), static_cast<unsigned long long>(c - d), static_cast<unsigned long long>(d - e),
        static_cast<unsigned long long>(field_chunks()), static_cast<int>(bc::map::width()), static_cast<int>(bc::map::height()));
}
} // namespace jdfp
#endif

int main() {
    Bot bot;
#if JD_FUELPROBE
    while (true) {
        try {
            const std::uint64_t f0 = bc::fuel_remaining();
            if (bc::is_draft()) {
                const std::int64_t r0 = jdfp::round_or_neg();
                play_draft();
#if V58_DIRECTOR
                economy_record_roster();
#endif
                const std::uint64_t f1 = bc::fuel_remaining();
                std::printf("JDFP D %u r%lld in %llu out %llu dm %zu\n", jdfp::draft_turns, static_cast<long long>(r0),
                    static_cast<unsigned long long>(f0), static_cast<unsigned long long>(f1), bc::draft_memory.size());
                {
                    std::printf("JDFP P picks");
                    for (auto c : bc::draft::current_draft(team::ally)) std::printf(" %d", static_cast<int>(c));
                    std::printf("\n");
                }
                if (jdfp::draft_turns == 0) {
                    // Can the draft VM read the static map (public static analysis on the 10M turn)?
                    try {
                        jdfp::host_samples();
                    } catch (const std::exception& e) {
                        std::printf("JDFP H draft-map-error %s\n", e.what());
                    }
                }
                ++jdfp::draft_turns;
                jdfp::draft_marker = 0xD7AF7u;
            } else {
                const std::uint32_t r0 = bc::round_number();
                const bool dead = bc::self().state().is_dead();
                const char phase = jdfp::play_turns == 0 ? 'C' : (dead ? 'X' : (jdfp::was_dead ? 'R' : 'O'));
                bot.play_turn();
                const std::uint64_t f1 = bc::fuel_remaining();
                const std::uint32_t r1 = bc::round_number();
                std::printf("JDFP %c %u r%u in %llu out %llu sus %u t %d\n", phase, jdfp::play_turns, r0,
                    static_cast<unsigned long long>(f0), static_cast<unsigned long long>(f1), r1 - r0,
                    static_cast<int>(bc::self().champion_name()));
                if (jdfp::play_turns == 0) {
                    const std::size_t n = bc::draft_memory.size();
                    std::printf("JDFP G marker %x dm %zu b0 %d d %u\n", static_cast<unsigned>(jdfp::draft_marker), n,
                        n ? static_cast<int>(bc::draft_memory[0]) : -1, jdfp::draft_turns);
                    // Body-slot mapping: our index in champions(ally) and every ally's type (-1 = out of vision).
                    const auto allies = bc::champions(team::ally);
                    std::printf("JDFP S self %d slots", static_cast<int>(bc::self().champion_name()));
                    for (std::size_t i = 0; i < allies.size(); ++i) {
                        int t = -1;
                        try {
                            t = static_cast<int>(allies[i].champion_name());
                        } catch (...) {
                        }
                        std::printf(" %d%s", t, allies[i] == bc::self() ? "*" : "");
                    }
                    std::printf("\n");
                }
                if (!jdfp::sampled && r1 == r0 && f1 > 60000) {
                    jdfp::sampled = true;
                    jdfp::host_samples();
                }
                jdfp::was_dead = dead;
                ++jdfp::play_turns;
            }
        } catch (const std::exception& error) {
            std::printf("bot error: %s\n", error.what());
        } catch (...) {
            std::printf("bot error: unknown exception\n");
        }
        bc::end_turn();
    }
#endif
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
#if defined(A2_NN_PIPE) && A2_NN_PIPE
                bot.nn_pipe_step();
#endif
#if JD_NN_EVENT
                bot.jd_nn_pipe();
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
#if A2_NN_MACRO && defined(A2_NN_RL)
                bot.nn_rl_end();
#endif
#if defined(A2_NN_PIPE) && A2_NN_PIPE
                bot.nn_pipe_step();
#endif
#if JD_NN_EVENT
                bot.jd_nn_pipe();
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
