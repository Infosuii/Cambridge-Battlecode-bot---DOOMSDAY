// Team opening schedule (A2_SCHED, E62): which champion clears which camp group and when, searched on the first draft
// turn (~10M fuel; later draft turns, the final pick included, have 100k: measured with A2_FUELPROBE). Our lineup is
// not known yet, so every slot gets the average stats of the twelve champion designs.
// Model: walking distances from the draft precompute (mappre.h: spawn and group-to-group, unreachable groups left out),
// 1 tile a round; camp health and strength from the camp designs; a crew of c champions kills a group in
// health / (c x camp damage) rounds and is sized so each member takes at most 60% of its health (live camps hit back
// at ~60% of full strength on average); capture 5 rounds; groups return their respawn time after capture; value =
// gems + w_gold x gold, groups nearer the enemy spawn (walking) x (1 - contested penalty). Search: randomised greedy
// rollouts, then local moves on the best job list (swap, change group, change crew, drop, insert) while fuel lasts.
// The result is the DPLAN step format (draft memory byte 8: 'P', slots, per slot a count and (group, start / 2)).
// Knobs (lab.h 48-55, 0 = these defaults): 48 horizon, 49 follow strength, 50 lateness, 51 gold weight,
// 52 contested penalty, 53 max crew, 54 rollout noise.
#pragma once
#if A2_SCHED
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>
#include "mappre.h"

namespace sched {
namespace d = cambc::detail;
inline float knob(int) { return 0.0f; } // (v92's lab knobs 48-54 mean other things: this copy keeps its defaults)
inline float horizon() { return std::clamp(200.0f * std::exp(0.5f * knob(48)), 60.0f, 600.0f); }
inline float follow_mult() { return A2_DP_MULT * std::exp(knob(49)); }
inline int lateness() { return static_cast<int>(std::clamp(static_cast<float>(A2_DP_LATE) * std::exp(0.5f * knob(50)), 5.0f, 300.0f)); }
inline float gold_weight() { return 0.1f * std::exp(knob(51)); }
inline float contested_penalty() { return std::clamp(0.3f + 0.3f * knob(52), 0.0f, 0.95f); }
inline int max_crew() { return std::clamp(3 + static_cast<int>(std::lround(knob(53))), 1, 5); }
inline float noise() { return std::clamp(0.3f * std::exp(knob(54)), 0.0f, 2.0f); }

constexpr int kSlots = 6, kSteps = 12;
struct Job {
    int g;
    unsigned crew; // bit mask of slots
};
struct Model {
    int n = 0, slots = 0;
    float H = 200;
    std::vector<int> need;          // crew size per group (99 = not planned)
    std::vector<float> val, kill;   // value, kill rounds with the needed crew
    std::vector<int> respawn;
    const std::vector<int>* mat = nullptr; // (n + 1) x n walking distances, row 0 = our spawn
    int walk(int from, int g) const { return (*mat)[static_cast<std::size_t>((1 + from) * n + g)]; }
};
struct Sim {
    float value = 0;
    int start[64][2]{}; // per job: start round, valid
};
// Plays a job list in order; jobs that cannot finish by the horizon are skipped.
inline float simulate(const Model& M, const std::vector<Job>& jobs, Sim* out = nullptr) {
    float fr[kSlots];
    int at[kSlots];
    for (int k = 0; k < M.slots; ++k) fr[k] = 3.0f, at[k] = -1;
    float avail[400];
    for (int g = 0; g < M.n && g < 400; ++g) avail[g] = 0.0f;
    float value = 0;
    for (std::size_t j = 0; j < jobs.size(); ++j) {
        const Job& job = jobs[j];
        float arrive = 0;
        bool ok = true;
        for (int k = 0; k < M.slots; ++k) {
            if (!(job.crew >> k & 1u)) continue;
            const int w = M.walk(at[k], job.g);
            if (w == mappre::kUnreach) ok = false;
            arrive = std::max(arrive, fr[k] + static_cast<float>(w));
        }
        const float start = std::max(arrive, avail[job.g]);
        const float done = start + M.kill[static_cast<std::size_t>(job.g)] + 5.0f;
        if (out && j < 64) out->start[j][1] = 0;
        if (!ok || done > M.H) continue;
        for (int k = 0; k < M.slots; ++k)
            if (job.crew >> k & 1u) fr[k] = done, at[k] = job.g;
        avail[job.g] = done + static_cast<float>(M.respawn[static_cast<std::size_t>(job.g)]);
        value += M.val[static_cast<std::size_t>(job.g)];
        if (out && j < 64) out->start[j][0] = static_cast<int>(start), out->start[j][1] = 1;
    }
    if (out) out->value = value;
    return value;
}
inline std::uint32_t rng = 2463534242u;
inline float rnd() { rng ^= rng << 13, rng ^= rng >> 17, rng ^= rng << 5; return static_cast<float>(rng >> 8) / 16777216.0f; }
// Greedy: the champion free soonest takes the group with the best value per crew-round (noisy), with the crew members
// who arrive soonest.
inline std::vector<Job> rollout(const Model& M, float nz) {
    std::vector<Job> jobs;
    float fr[kSlots];
    int at[kSlots];
    for (int k = 0; k < M.slots; ++k) fr[k] = 3.0f, at[k] = -1;
    std::vector<float> avail(static_cast<std::size_t>(M.n), 0.0f);
    for (int guard = 0; guard < 64; ++guard) {
        int i = 0;
        for (int k = 1; k < M.slots; ++k)
            if (fr[k] < fr[i]) i = k;
        const float t = fr[i];
        if (t >= M.H) break;
        int best = -1;
        unsigned best_crew = 0;
        float best_s = 0, best_done = 0;
        for (int g = 0; g < M.n; ++g) {
            const int c = M.need[static_cast<std::size_t>(g)];
            if (c > M.slots || M.walk(at[i], g) == mappre::kUnreach) continue;
            unsigned crew = 1u << i;
            float arrive = std::max(fr[i], t) + static_cast<float>(M.walk(at[i], g));
            for (int need = 1; need < c; ++need) {
                int pick = -1;
                float pt = 1e30f;
                for (int k = 0; k < M.slots; ++k) {
                    if (crew >> k & 1u) continue;
                    const int w = M.walk(at[k], g);
                    if (w == mappre::kUnreach) continue;
                    const float a = std::max(fr[k], t) + static_cast<float>(w);
                    if (a < pt) pt = a, pick = k;
                }
                if (pick < 0) break;
                crew |= 1u << pick;
                arrive = std::max(arrive, pt);
            }
            if (__builtin_popcount(crew) < c) continue;
            const float done = std::max(arrive, avail[static_cast<std::size_t>(g)]) + M.kill[static_cast<std::size_t>(g)] + 5.0f;
            if (done > M.H) continue;
            float s = M.val[static_cast<std::size_t>(g)] / ((done - t) * static_cast<float>(c));
            if (nz > 0) s *= 1.0f + nz * (2.0f * rnd() - 1.0f);
            if (s > best_s) best_s = s, best = g, best_crew = crew, best_done = done;
        }
        if (best < 0) {
            fr[i] = M.H;
            continue;
        }
        jobs.push_back({best, best_crew});
        for (int k = 0; k < M.slots; ++k)
            if (best_crew >> k & 1u) fr[k] = best_done, at[k] = best;
        avail[static_cast<std::size_t>(best)] = best_done + static_cast<float>(M.respawn[static_cast<std::size_t>(best)]);
    }
    return jobs;
}
inline unsigned random_crew(const Model& M, int c) {
    unsigned crew = 0;
    for (int tries = 0; __builtin_popcount(crew) < c && tries < 40; ++tries) crew |= 1u << static_cast<int>(rnd() * static_cast<float>(M.slots));
    return __builtin_popcount(crew) == c ? crew : 0u;
}
// A champion design's camp damage per round and health.
struct Stats {
    float dps = 0, health = 0;
};
inline Stats champion_stats(int type) {
    d::champion_design design{};
    if (d::sdk_champion_design(type, &design) != 0) return {};
    const auto& s = design.base_stats;
    // Basic attacks plus about one camp-hitting spell cast per 8 turns (the bot's own my_dps uses focus / 8 a spell).
    return {s.base_strength * std::max(s.camp_damage_multiplier, 0.1f) + 0.15f * s.base_focus, s.base_health};
}

// The schedule's step bytes (DPLAN format), built once.
inline std::vector<std::uint8_t> build(std::uint32_t size) {
    std::vector<std::uint8_t> bytes;
    const auto& A = mappre::analysis();
    if (!A.ok || !A.have_mat) return bytes;
    Model M;
    M.n = static_cast<int>(A.G.size());
    if (M.n == 0 || M.n > 400) return bytes;
    M.slots = static_cast<int>(std::clamp<std::uint32_t>(size, 1, kSlots));
    M.H = horizon();
    M.mat = &A.mat;
    Stats avg;
    int cnt = 0;
    for (int t = 0; t < 13; ++t) {
        const Stats s = champion_stats(t);
        if (s.health <= 0) continue;
        avg.dps += s.dps, avg.health += s.health, ++cnt;
    }
    if (!cnt) return bytes;
    avg.dps /= static_cast<float>(cnt), avg.health /= static_cast<float>(cnt);
    const float wg = gold_weight(), pen = contested_penalty();
    const int cmax = std::min(max_crew(), M.slots);
    M.need.assign(static_cast<std::size_t>(M.n), 99);
    M.val.assign(static_cast<std::size_t>(M.n), 0.0f);
    M.kill.assign(static_cast<std::size_t>(M.n), 0.0f);
    M.respawn.assign(static_cast<std::size_t>(M.n), 60);
    d::camp_design designs[16]{};
    bool have[16]{};
    for (int g = 0; g < M.n; ++g) {
        const auto& G = A.G[static_cast<std::size_t>(g)];
        M.respawn[static_cast<std::size_t>(g)] = G.respawn;
        if (G.tiles.empty() || A.dA[static_cast<std::size_t>(g)] == mappre::kUnreach) continue;
        float hp = 0, str = 0;
        for (int k : G.types) {
            const int kind = k & 15;
            if (!have[kind]) {
                if (d::sdk_camp_design(k, &designs[kind]) != 0) continue;
                have[kind] = true;
            }
            hp += designs[kind].base_stats.base_health, str += designs[kind].base_stats.base_strength;
        }
        if (hp <= 0) continue;
        for (int c = 1; c <= cmax; ++c) {
            const float t = hp / (static_cast<float>(c) * std::max(avg.dps, 1.0f));
            if (0.6f * str * t / static_cast<float>(c) <= 0.6f * avg.health) {
                M.need[static_cast<std::size_t>(g)] = c;
                M.kill[static_cast<std::size_t>(g)] = t;
                break;
            }
        }
        float v = G.gems + wg * G.gold;
        if (A.dE[static_cast<std::size_t>(g)] < A.dA[static_cast<std::size_t>(g)]) v *= 1.0f - pen;
        M.val[static_cast<std::size_t>(g)] = v;
    }
    // Search: rollouts, then local moves, within fuel (real engine) and iteration caps (the lab does not meter fuel).
    constexpr std::uint64_t kFloor = 2500000;
    std::vector<Job> best = rollout(M, 0.0f);
    float best_v = simulate(M, best);
    const float nz = noise();
    for (int r = 0; r < A2_SCHED_ROLLOUTS && bc::fuel_remaining() > kFloor + 300000; ++r) {
        auto jobs = rollout(M, nz);
        const float v = simulate(M, jobs);
        if (v > best_v) best_v = v, best = std::move(jobs);
    }
    for (int it = 0; it < A2_SCHED_MOVES && bc::fuel_remaining() > kFloor && !best.empty(); ++it) {
        auto cand = best;
        const int j = static_cast<int>(rnd() * static_cast<float>(cand.size()));
        const float u = rnd();
        if (u < 0.3f && cand.size() > 1) { // swap two jobs
            const int j2 = static_cast<int>(rnd() * static_cast<float>(cand.size()));
            std::swap(cand[static_cast<std::size_t>(j)], cand[static_cast<std::size_t>(j2)]);
        } else if (u < 0.5f) { // another group for this job
            const int g = static_cast<int>(rnd() * static_cast<float>(M.n));
            const int c = M.need[static_cast<std::size_t>(g)];
            if (c > M.slots) continue;
            const unsigned crew = __builtin_popcount(cand[static_cast<std::size_t>(j)].crew) == c ? cand[static_cast<std::size_t>(j)].crew : random_crew(M, c);
            if (!crew) continue;
            cand[static_cast<std::size_t>(j)] = {g, crew};
        } else if (u < 0.75f) { // another crew for this job
            const unsigned crew = random_crew(M, M.need[static_cast<std::size_t>(cand[static_cast<std::size_t>(j)].g)]);
            if (!crew) continue;
            cand[static_cast<std::size_t>(j)].crew = crew;
        } else if (u < 0.85f) { // drop a job
            cand.erase(cand.begin() + j);
        } else { // insert a job
            const int g = static_cast<int>(rnd() * static_cast<float>(M.n));
            const int c = M.need[static_cast<std::size_t>(g)];
            if (c > M.slots) continue;
            const unsigned crew = random_crew(M, c);
            if (!crew || cand.size() >= 60) continue;
            cand.insert(cand.begin() + j, Job{g, crew});
        }
        const float v = simulate(M, cand);
        if (v > best_v) best_v = v, best = std::move(cand);
    }
    Sim sim;
    simulate(M, best, &sim);
    std::vector<std::pair<int, int>> steps[kSlots];
    for (std::size_t j = 0; j < best.size() && j < 64; ++j) {
        if (!sim.start[j][1]) continue;
        for (int k = 0; k < M.slots; ++k)
            if (best[j].crew >> k & 1u && steps[k].size() < kSteps) steps[k].emplace_back(best[j].g, sim.start[j][0]);
    }
    bytes.push_back('P');
    bytes.push_back(static_cast<std::uint8_t>(M.slots));
    for (int k = 0; k < M.slots; ++k) {
        bytes.push_back(static_cast<std::uint8_t>(steps[k].size()));
        for (const auto& [g, s] : steps[k]) {
            bytes.push_back(static_cast<std::uint8_t>(std::min(g, 255)));
            bytes.push_back(static_cast<std::uint8_t>(std::min(255, s / 2)));
        }
    }
#ifdef A2_SCHED_DIAG
    std::printf("SCHED value %.0f jobs %zu H %.0f fuel_left %llu%c", best_v, best.size(), M.H,
        static_cast<unsigned long long>(bc::fuel_remaining()), 10);
#endif
    return bytes;
}
} // namespace sched
#endif
