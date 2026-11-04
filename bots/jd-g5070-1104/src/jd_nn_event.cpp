// JD_NN_EVENT (FEAT-003): event-driven, fuel-admitted runtime for Agent 2's student network (nnrec.cpp features,
// nn_infer.h forward, jd_nn_weights.h). research/jd-g5070-1104/MODEL_ABI.md is the contract.
//
// Per turn (jd_nn_turn, after the world update, cheap): detect events, validate the held decision, and hand farm()
// either the held target group (nn_group) and bank gate (nn_beh) or nothing (v92 chooses: the fallback). Events:
// first turn, respawn, leaving contact, the held target finished (went to respawning) or became unreachable, another
// ally newly claims it, the bag crosses a bank threshold, the decision is JD_NN_PERIOD rounds old; the held decision is
// dropped after JD_NN_MAXDUR rounds. An event arms the pipeline.
// End of turn (jd_nn_pipe, main.cpp after play_turn): the armed pipeline runs features (step 0) and the six
// nn::pipe_stage steps, each admitted by rb::admit_optional(rb::kNN, measured worst case + reserve); a refused step
// waits for the next turn. A finished decision is published unless its features are older than JD_NN_STALE rounds or
// the champion entered contact meanwhile. The network never runs in contact, and farm() skips v92's own group scoring
// while a network target is held (bot.cpp), so the full network and v92's scoring do not both run for one choice.
#include "bot.h"
#if A2_NN && (JD_NN_EVENT || JD_NN_LOG)
#include <algorithm>
#include <cstdio>
#include <string>

#include "nn_infer.h"
#include "runtime_budget.h"

namespace {
// layout 2 (500 features): offsets as in nnrec.cpp
constexpr int kG = 16, kS = 44, kA = 5, kAF = 12, kE = 8, kEF = 16, kC = 10, kCF = 22;
constexpr int kNF = 500, kCOff = kG + kS + kA * kAF + kE * kEF; // 248
// model version check: the exported header must describe the same layout, else the network is disabled
constexpr bool kModelOk = nnw::kc_off == kCOff && nnw::kc_n == kC && nnw::kc_w == kCF && nnw::ka_w == kAF &&
                          nnw::ke_n == kE && nnw::kl_off + nnw::kl_n * nnw::kl_w == kNF && A2_NN_LAYOUT == 2;

enum Reason : int { fbNoDec, fbFar, fbFinished, fbUnreach, fbStale, fbOOD, fbMaxDur, fbRespawn, fbModel, kNReason };
[[maybe_unused]] constexpr const char* kReasonName[kNReason] = {"nodec", "far", "finished", "unreach", "stale", "ood",
                                                                "maxdur", "respawn", "model"};
enum Event : int { evFirst, evRespawn, evContactExit, evFinished, evUnreach, evClaim, evBag, evPeriod, evMaxDur, kNEvent };
[[maybe_unused]] constexpr const char* kEventName[kNEvent] = {"first", "respawn", "contact", "finished", "unreach",
                                                              "claim", "bag", "period", "maxdur"};

struct Held {
    int tgt = -1, st = 0, beh = -1, at = -1000000, since = -1000000, claims = 0;
    int bag = -1;          // bag bucket when published
    int reason = fbNoDec;   // why tgt < 0
};
#if JD_NN_EVENT
struct Pipe {
    nn::Pipe p;
    std::int16_t f[kNF] = {};
    bool armed = false;
    int next = 0, feat_round = -1, event = evFirst, start_round = -1;
    std::uint64_t used = 0, maxstep = 0;
    int steps = 0;
    // measured worst case per step (+1/8), starting from Agent 2's E120 profile: features, g+s+a, e+l, camp halves,
    // pool + trunk 0, trunk 1 + heads
    std::uint64_t est[1 + nn::kPipeStages] = {34000, 13000, 14000, 17000, 17000, 24000, 19000};
    bool ran[1 + nn::kPipeStages] = {};
};
Pipe pipe;
#endif
struct Stat {
    int turns = 0, contact = 0, applied = 0, switches = 0, last_tg = -1, decisions = 0, published = 0;
    int fb[kNReason] = {}, ev[kNEvent] = {};
    int refused = 0, aborted = 0, stale = 0, ood = 0, overrun = 0, dur_n = 0, dur_max = 0;
    long long dur_sum = 0, rec_fuel = 0;
    int rec_n = 0, rec_drop = 0, rec_over = 0;
    int dumps = 0, logged = -1;
};
[[maybe_unused]] Held held;
Stat stat;
[[maybe_unused]] int prev_round = -1;
[[maybe_unused]] bool was_contact = false;
[[maybe_unused]] constexpr std::uint64_t kStepReserve = 5000; // the user's 2-5k margin against overrunning into the next turn
[[maybe_unused]] constexpr std::uint64_t kStepCap = 80000;    // no step estimate above this (an ordinary turn has 100k)

[[maybe_unused]] int bag_bucket(int g) { return g <= 0 ? 0 : g < 20 ? 1 : g < 40 ? 2 : g < 80 ? 3 : 4; }

[[maybe_unused]] std::string b64(const std::int16_t* p, int n) {
    static const char* T = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    const auto* b = reinterpret_cast<const unsigned char*>(p);
    const int len = 2 * n;
    std::string s;
    s.reserve((len + 2) / 3 * 4);
    for (int i = 0; i < len; i += 3) {
        const unsigned v = (b[i] << 16) | ((i + 1 < len ? b[i + 1] : 0) << 8) | (i + 2 < len ? b[i + 2] : 0);
        s += T[(v >> 18) & 63];
        s += T[(v >> 12) & 63];
        s += i + 1 < len ? T[(v >> 6) & 63] : '=';
        s += i + 2 < len ? T[v & 63] : '=';
    }
    return s;
}

[[maybe_unused]] void end_hold(int round) {
    if (held.tgt >= 0) {
        const int d = round - held.since;
        stat.dur_sum += d, ++stat.dur_n, stat.dur_max = std::max(stat.dur_max, d);
    }
}
} // namespace

// Per-turn counters for every network arm (JD_NN_LOG): turns, contact turns, target switches; one JDN C line every
// 100 rounds (the last line of a game is the champion's total).
void Bot::jd_nn_stat() {
#if JD_NN_LOG
    const bool contact = nn_near() <= 6;
    ++stat.turns;
    stat.contact += contact;
    if (target_group >= 0 && stat.last_tg >= 0 && target_group != stat.last_tg) ++stat.switches;
    if (target_group >= 0) stat.last_tg = target_group;
    if (round % 100 == 0 && round != stat.logged) {
        stat.logged = round;
        // one printf per line: the engine's stdout capture can split separate writes (NUL padding)
        char buf[512];
        int n = std::snprintf(buf, sizeof buf,
                              "JDN C %d %d turns %d contact %d applied %d switches %d dec %d pub %d refused %d aborted %d stale %d "
                              "ood %d overrun %d dur %lld %d %d fb",
                              round, slot, stat.turns, stat.contact, stat.applied, stat.switches, stat.decisions, stat.published,
                              stat.refused, stat.aborted, stat.stale, stat.ood, stat.overrun, stat.dur_sum, stat.dur_n, stat.dur_max);
        for (int r = 0; r < kNReason && n > 0 && n < 480; ++r) n += std::snprintf(buf + n, sizeof buf - static_cast<std::size_t>(n), " %d", stat.fb[r]);
        if (n > 0 && n < 480) n += std::snprintf(buf + n, sizeof buf - static_cast<std::size_t>(n), " ev");
        for (int e = 0; e < kNEvent && n > 0 && n < 480; ++e) n += std::snprintf(buf + n, sizeof buf - static_cast<std::size_t>(n), " %d", stat.ev[e]);
        if (n > 0 && n < 480) n += std::snprintf(buf + n, sizeof buf - static_cast<std::size_t>(n), " rec %lld %d %d %d", stat.rec_fuel, stat.rec_n, stat.rec_drop, stat.rec_over);
        std::printf("%s\n", buf);
    }
#endif
}

#if JD_NN_EVENT && JD_NN_REC
namespace {
// JD_NN_REC: the NR rows (training data at the deployed cadence) queue here and are written with the fuel left after
// the pipeline, each admitted on its own measured cost, so recording does not slow the decisions it records. A row costs
// ~28k fuel to write (stdout bytes are expensive; std::string + printf cost ~95k in nn-golden-03). Queue full: the
// oldest row is dropped (counted).
constexpr int kRecQ = 4;
std::int16_t recq[kRecQ][kNF];
int recq_round[kRecQ], recq_tg[kRecQ], recq_head = 0, recq_n = 0;
std::uint64_t rec_est = 32000;
bool rec_ran = false;
void rec_push(const std::int16_t* f, int round, int tg) {
    if (recq_n == kRecQ) recq_head = (recq_head + 1) % kRecQ, --recq_n, ++stat.rec_drop;
    const int i = (recq_head + recq_n) % kRecQ;
    std::copy(f, f + kNF, recq[i]);
    recq_round[i] = round, recq_tg[i] = tg, ++recq_n;
}
void rec_flush(int slot) {
    static char line[64 + 4 * ((2 * kNF + 2) / 3)];
    static const char* T = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    while (recq_n > 0 && rb::admit_optional(rb::kNN, rec_est + kStepReserve)) {
        const std::uint64_t c0 = bc::fuel_remaining();
        const auto r0 = bc::round_number();
        const int q = recq_head;
        // NR row in nn_record.py's format (table encoder into a static buffer, one fwrite)
        int n = std::snprintf(line, 32, "NR %d %d 0 ", recq_round[q], slot);
        const auto* b = reinterpret_cast<const unsigned char*>(recq[q]);
        constexpr int len = 2 * kNF; // 1000 bytes: 333 full groups + 1 byte
        int i = 0;
        for (; i + 3 <= len; i += 3) {
            const unsigned v = (static_cast<unsigned>(b[i]) << 16) | (static_cast<unsigned>(b[i + 1]) << 8) | b[i + 2];
            line[n] = T[(v >> 18) & 63], line[n + 1] = T[(v >> 12) & 63], line[n + 2] = T[(v >> 6) & 63], line[n + 3] = T[v & 63];
            n += 4;
        }
        if (i < len) {
            const unsigned v = (static_cast<unsigned>(b[i]) << 16) | (i + 1 < len ? static_cast<unsigned>(b[i + 1]) << 8 : 0u);
            line[n] = T[(v >> 18) & 63], line[n + 1] = T[(v >> 12) & 63];
            line[n + 2] = i + 1 < len ? T[(v >> 6) & 63] : '=', line[n + 3] = '=';
            n += 4;
        }
        n += std::snprintf(line + n, sizeof line - static_cast<std::size_t>(n), " nn %d 0 | \n", recq_tg[q]);
        std::fwrite(line, 1, static_cast<std::size_t>(n), stdout);
        recq_head = (recq_head + 1) % kRecQ, --recq_n;
        if (bc::round_number() != r0) {
            ++stat.rec_over;
            rec_est = std::min(kStepCap, std::max(rec_est, rec_est + rec_est / 4));
            return;
        }
        const std::uint64_t used = c0 - bc::fuel_remaining();
        stat.rec_fuel += static_cast<long long>(used), ++stat.rec_n;
        if (rec_ran) rec_est = std::min(kStepCap, std::max(rec_est, used + used / 8));
        rec_ran = true;
    }
}
} // namespace
#endif

#if JD_NN_EVENT
void Bot::jd_nn_turn() {
    const bool contact = nn_near() <= 6;
    const bool respawn = prev_round >= 0 && round - prev_round > 3;
    const bool first = prev_round < 0;
    prev_round = round;
    int ev = -1;
    auto fire = [&](int e) {
        if (ev < 0) ev = e;
    };
    if (!kModelOk) {
        held.tgt = -1, held.reason = fbModel;
    } else if (contact) {
        // contact: v92's fight code decides; a pipeline in flight is stale once the fight starts
        if (pipe.armed && pipe.next > 0) ++stat.aborted;
        pipe.armed = false, pipe.next = 0;
    } else {
        if (first) fire(evFirst);
        if (respawn) {
            end_hold(round);
            held = Held{}, held.reason = fbRespawn;
            fire(evRespawn);
        }
        if (was_contact) fire(evContactExit);
        if (held.tgt >= 0) {
            const auto ng = static_cast<int>(w.groups.size());
            if (held.tgt >= ng) {
                end_hold(round), held.tgt = -1, held.reason = fbUnreach;
                fire(evUnreach);
            } else {
                const auto& g = w.groups[static_cast<std::size_t>(held.tgt)];
                if (g.state == GroupState::respawning && held.st != static_cast<int>(GroupState::respawning)) {
                    end_hold(round), held.tgt = -1, held.reason = fbFinished; // finished: dropped at once
                    fire(evFinished);
                } else if (w.has_field(held.tgt) && w.group_distance(held.tgt, pos) >= kUnreach) {
                    end_hold(round), held.tgt = -1, held.reason = fbUnreach;
                    fire(evUnreach);
                } else if (round - held.since >= JD_NN_MAXDUR) {
                    end_hold(round), held.tgt = -1, held.reason = fbMaxDur;
                    fire(evMaxDur);
                } else if (claim_count(held.tgt) > held.claims) {
                    held.claims = claim_count(held.tgt);
                    fire(evClaim);
                }
            }
        }
        if (held.bag >= 0 && bag_bucket(gems) != held.bag) {
            held.bag = bag_bucket(gems);
            fire(evBag);
        }
        if (round - held.at >= JD_NN_PERIOD) fire(evPeriod);
        if (ev >= 0) {
            // forced events restart a pipeline in flight; periodic / bag / claim ones wait for it
            const bool forced = ev == evFirst || ev == evRespawn || ev == evContactExit || ev == evFinished || ev == evUnreach ||
                                ev == evMaxDur;
            if (!pipe.armed || forced) {
                ++stat.ev[ev];
                if (pipe.armed && pipe.next > 0) ++stat.aborted;
                pipe.armed = true, pipe.next = 0, pipe.event = ev;
                held.at = round; // the periodic clock restarts with the request
            }
        }
    }
    was_contact = contact;
    if (contact) return; // nn_group / nn_beh stay -1: v92 decides in contact (Agent 2's deployment rule)
#if !JD_NN_ZERO
    if (held.tgt >= 0) {
        nn_group = held.tgt;
        nn_beh = held.beh;
        ++stat.applied;
    } else {
        ++stat.fb[held.reason];
    }
#else
    ++stat.fb[held.tgt >= 0 ? fbNoDec : held.reason];
#endif
}

void Bot::jd_nn_pipe() {
    jd_nn_pipe_core();
#if JD_NN_REC
    if (inited) rec_flush(slot);
#endif
}

void Bot::jd_nn_pipe_core() {
    if (!inited || !kModelOk || !pipe.armed) return;
    for (;;) {
        const std::uint64_t left = bc::fuel_remaining();
        const std::uint64_t need = pipe.est[pipe.next] + kStepReserve;
        if (!rb::admit_optional(rb::kNN, need)) {
            ++stat.refused;
            return;
        }
        const auto r0 = bc::round_number();
        if (pipe.next == 0) {
            if (nn_near() <= 6) return;
            std::fill(pipe.f, pipe.f + kNF, static_cast<std::int16_t>(0));
            nn_feats(pipe.f, nn_near());
            bool any = false;
            for (int c = 0; c < kC; ++c) any |= pipe.f[kCOff + c * kCF] == 1;
            if (!any) {
                // out of distribution: no camp group in the features; v92 decides until the next event
                ++stat.ood;
                pipe.armed = false;
                if (held.tgt < 0) held.reason = fbOOD;
                return;
            }
            pipe.feat_round = round, pipe.start_round = round, pipe.used = 0, pipe.maxstep = 0, pipe.steps = 0;
#if JD_NN_REC
            rec_push(pipe.f, round, target_group); // written later, on its own admission (rec_flush)
#endif
        } else {
            nn::pipe_stage(pipe.p, pipe.f, pipe.next - 1);
        }
        const std::uint64_t now = bc::fuel_remaining();
        const bool over = bc::round_number() != r0;
        const std::uint64_t used = over ? left : left - now;
        if (over) {
            // finished on the next turn's fuel (that turn's play is lost): it needs more than was left. Agent 2's rule
            // (est = left + reserve) locks the pipeline for the game when the overrun happens on the 200k first turn
            // (golden run nn-golden-01: one decision per champion, then every turn refused), so the raise is capped.
            ++stat.overrun;
#if JD_NN_LOG
            std::printf("JDN O %d %d step %d left %llu est %llu now %llu\n", static_cast<int>(r0), slot, pipe.next,
                        static_cast<unsigned long long>(left), static_cast<unsigned long long>(pipe.est[pipe.next]),
                        static_cast<unsigned long long>(now));
#endif
            pipe.est[pipe.next] = std::max(pipe.est[pipe.next], std::min<std::uint64_t>(left, kStepCap / 2) + kStepReserve);
        } else if (pipe.ran[pipe.next] && left <= 100000) {
            // worst case so far (+1/8). Not learned from the first run (one-time setup) nor from a step that started
            // with more than an ordinary turn's fuel: on the 200k first turn nn_feats also builds group distance
            // fields down to 110k left (A2_NN_FAST), a one-off ~70k that would otherwise lock step 0 out.
            pipe.est[pipe.next] = std::max(pipe.est[pipe.next], used + used / 8);
        }
        pipe.est[pipe.next] = std::min(pipe.est[pipe.next], kStepCap);
        pipe.ran[pipe.next] = true;
        pipe.used += used, pipe.maxstep = std::max(pipe.maxstep, used), ++pipe.steps;
        if (++pipe.next < 1 + nn::kPipeStages) continue;
        // decision complete
        pipe.next = 0, pipe.armed = false;
        ++stat.decisions;
        const int r = static_cast<int>(bc::round_number());
        if (r - pipe.feat_round > JD_NN_STALE) {
            ++stat.stale;
            if (held.tgt < 0) held.reason = fbStale;
            return;
        }
        const float* lg = pipe.p.o.target;
        int t = static_cast<int>(std::max_element(lg, lg + kC + 1) - lg);
        int tg = t < kC && pipe.f[kCOff + t * kCF] == 1 ? pipe.f[kCOff + t * kCF + 1] : -1;
        const bool forced = pipe.event == evFirst || pipe.event == evRespawn || pipe.event == evContactExit ||
                            pipe.event == evFinished || pipe.event == evUnreach || pipe.event == evMaxDur;
        if (!forced && held.tgt >= 0 && tg != held.tgt) {
            // commitment: a periodic / bag / claim replan keeps the held target unless the new one is clearly better
            for (int c = 0; c < kC; ++c)
                if (pipe.f[kCOff + c * kCF] == 1 && pipe.f[kCOff + c * kCF + 1] == held.tgt && lg[t] < lg[c] + JD_NN_HYST) tg = held.tgt, t = c;
        }
        const int beh = nn::argmax(pipe.p.o.behaviour);
#if JD_NN_DUMP
        if (stat.dumps < JD_NN_DUMP) {
            ++stat.dumps;
            // one printf per line: the engine's stdout capture can split separate writes (NUL padding)
            std::string s = "JDNDUMP " + std::to_string(pipe.feat_round) + " " + std::to_string(slot) + " " + b64(pipe.f, kNF) + " T";
            char buf[32];
            auto add = [&](const float* v, int n) {
                for (int i = 0; i < n; ++i) std::snprintf(buf, sizeof buf, " %.6e", static_cast<double>(v[i])), s += buf;
            };
            add(lg, kC + 1);
            s += " B";
            add(pipe.p.o.behaviour, 8);
            s += " O";
            add(pipe.p.o.option, 5);
            std::printf("%s\n", s.c_str());
        }
#endif
        if (tg >= 0 && tg < static_cast<int>(w.groups.size())) {
            const auto& g = w.groups[static_cast<std::size_t>(tg)];
            const int st_now = static_cast<int>(g.state);
            const int st_feat = pipe.f[kCOff + t * kCF + 7];
            if (st_now == static_cast<int>(GroupState::respawning) && st_feat != st_now) tg = -1, held.reason = fbFinished;
            else if (w.has_field(tg) && w.group_distance(tg, pos) >= kUnreach) tg = -1, held.reason = fbUnreach;
        } else if (tg >= 0) {
            tg = -1, held.reason = fbUnreach;
        } else {
            held.reason = fbFar; // the network's "farther than the 10 nearest" slot: v92 chooses
        }
        if (tg != held.tgt) {
            end_hold(r);
            held.since = r;
        }
        held.tgt = tg, held.beh = beh, held.at = std::max(held.at, pipe.feat_round), held.bag = bag_bucket(gems);
        if (tg >= 0) held.st = static_cast<int>(w.groups[static_cast<std::size_t>(tg)].state), held.claims = claim_count(tg);
        ++stat.published;
#if JD_NN_LOG
        std::printf("JDN D %d %d %llu %llu %d %d %s %d %d\n", r, slot, static_cast<unsigned long long>(pipe.used),
                    static_cast<unsigned long long>(pipe.maxstep), pipe.steps, r - pipe.start_round, kEventName[pipe.event], tg, beh);
#endif
        return; // at most one decision per turn
    }
}
#endif
#endif
