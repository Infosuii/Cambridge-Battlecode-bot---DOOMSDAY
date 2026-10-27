// Focused regressions for the camp-routing and coordination failures found in the v6 trace.
#include "../../bots/mimic/src/core.h"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <initializer_list>

static mc::Map map;
static mc::Obs obs;
static mc::Memory mem;
static float feat[mc::kMaxObj * mc::NF_OBJ];
static std::uint8_t blocked[mc::kMaxTiles], roots[mc::kMaxTiles];
static std::uint16_t field[mc::kMaxTiles];

int main() {
    mc::begin_map(map, 16, 16, mc::SYM_ROT);
    mc::add_camp(map, 0, 6, 6, 0, 1350, 20, 3);
    mc::add_camp(map, 0, 7, 6, 0, 1350, 20, 3);
    mc::add_camp(map, 0, 8, 6, 0, 1350, 20, 3);
    mc::set_group(map, 0, 100, 25, 30);
    mc::finish_map(map);
    mc::blocked_mask(map, blocked);
    mc::group_roots(map, 0, roots);
    mc::bfs(map, blocked, roots, field);
    map.gfield[0] = field;
    mc::reset_obs(obs);
    obs.me.id = 0; obs.me.x = 5; obs.me.y = 6; obs.me.range = 1;
    obs.me.hp = obs.me.max_hp = 1000; obs.me.strength = 50;
    obs.camp[obs.n_camp++] = {2, 1000, true};
    obs.group[obs.n_group++] = {0, 1, 0};
    mc::finalize_obs(map, obs);
    mc::observe(map, obs, mem);
    const mc::Objective farm{mc::O_FARM, 0};
    assert(field[map.idx(5, 6)] == 1); // the stale field points at the dead root
    assert(mc::objective_distance(map, obs, farm, 5, 6) == 3);
    assert(mc::objective_distance(map, obs, farm, 6, 6) == 2);
    assert(!mc::at_goal(map, obs, mem, farm, 5, 6));
    assert(mc::at_goal(map, obs, mem, farm, 7, 6));
    mc::Objective objectives[mc::kMaxObj];
    mc::objective_candidates(map, obs, mem, objectives, feat);
    const float solo = feat[mc::OF_CREW_TURNS];
    obs.ally[obs.n_ally++] = obs.me;
    obs.ally[0].id = 1; obs.ally[0].x = 7; obs.ally[0].y = 5;
    mc::objective_candidates(map, obs, mem, objectives, feat);
    assert(feat[mc::OF_CREW_TURNS] < solo);
    assert(feat[mc::OF_READY_NEAR] == 1);
    obs.round = 1; obs.group[0] = {0, 3, 30}; obs.n_camp = 0;
    mc::finalize_obs(map, obs); mc::observe(map, obs, mem);
    mc::objective_candidates(map, obs, mem, objectives, feat);
    assert(objectives[0].kind == mc::O_HOME); // empty group is not a job yet
    obs.group[0] = {0, 2, 0}; obs.ally[0].x = 7; obs.ally[0].y = 6;
    mc::finalize_obs(map, obs); mc::observe(map, obs, mem);
    mc::objective_candidates(map, obs, mem, objectives, feat);
    assert(objectives[0].kind == mc::O_HOME); // the closer ally captures while I leave
    obs.me.x = 6;
    mc::objective_candidates(map, obs, mem, objectives, feat);
    assert(objectives[0].kind == mc::O_FARM && feat[mc::OF_CAPTURE_COVERED] == 1); // tied on-region: lower id owns it
    obs.ally[0].exact = false;
    obs.me.x = 5;
    mc::objective_candidates(map, obs, mem, objectives, feat);
    assert(objectives[0].kind == mc::O_FARM); // a coarse remembered position cannot claim a reward
    obs.me.x = 6;
    mc::MoveCand moves[mc::kMaxMoves];
    mc::move_candidates(map, obs, mem, farm, false, moves, feat);
    assert(feat[32] == 1); // stay on the reward region until capture completes
    std::uint8_t shared[8] = {};
    for (int i = 0; i < 6; ++i) mc::write_slot(shared, i, mc::encode_slot(4 * i, 4 * i));
    for (int i = 0; i < 6; ++i) {
        int x, y;
        assert(mc::decode_slot(mc::read_slot(shared, i), x, y));
        assert(x == 4 * i + 1 && y == x);
    }
    float weights[mc::NF_OBJ], scores[mc::kMaxObj];
    for (int j = 0; j < mc::NF_OBJ; ++j) weights[j] = static_cast<float>(j % 11 - 5) / 7;
    const int n = mc::objective_candidates(map, obs, mem, objectives, feat);
    mc::score_objectives(weights, feat, objectives, n, scores);
    for (int i = 0; i < n; ++i) {
        float ref = 0;
        for (int j = 0; j < mc::NF_OBJ; ++j) ref += weights[j] * feat[i * mc::NF_OBJ + j];
        assert(std::abs(scores[i] - ref) < 1e-5f);
    }
    for (int nf : {mc::NF_MOVE, mc::NF_TGT, mc::NF_CAST, mc::NF_OBJ}) {
        for (int j = 0; j < 7 * nf; ++j) feat[j] = static_cast<float>(j % 17 - 8) / 9;
        mc::score(weights, feat, 7, nf, scores);
        for (int i = 0; i < 7; ++i) {
            float ref = 0;
            for (int j = 0; j < nf; ++j) ref += weights[j] * feat[i * nf + j];
            assert(std::abs(scores[i] - ref) < 1e-5f);
        }
    }
    std::puts("mimic core regressions passed");
}
