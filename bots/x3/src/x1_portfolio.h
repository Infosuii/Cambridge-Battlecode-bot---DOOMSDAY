// Strategy portfolio (X1_PORTFOLIO, research/x3/losses48/PLAYBOOK.md): at game start the bot computes its map
// features (x1_atlas.h), puts the map in a category (x1_categories.h, rules that also cover unseen maps) and plays
// that category's strategy profile. Profiles and the category -> profile table are volatile data, so every build
// (and every forced test build, X1_PORTFOLIO_FORCE = profile) runs the same instructions.
#pragma once
#include "x1_atlas.h"
#include "x1_categories.h"

namespace x1_portfolio {

// Profile fields (floats; -1 = keep the base value):
//  0 terr      enemy-side camp value (tune::kTerritory), -1 keep
//  1 aggr      aggression multiplier
//  2 carry     bank threshold multiplier (tune::kTributeCarry)
//  3 carry_until  round the carry multiplier stops (0 = all game)
//  4 hunt      hunt range offset (0 = keep)
//  5 raid      1 = raider on (A2_RAID gate, lab knob 53), 0 = keep
//  6 numbers   1 = engage only with a numbers edge (A3_NUMBERS)
//  7 focus     focus-fire weight (A3_FOCUS)
//  8 antifeed  1 = antifeed on (X1_ANTIFEED with the fight-balance trigger)
//  9 items     0 = v92 plan, 1 = Treasure + Bruiser stacks (V54_ITEMS 3), 2 = top-team opening (A3_ITEMS)
// 10 terr_from round the territory value starts to apply (0 = all game)
// 11 vision    1 = spend every ward charge on scouting wards (ward_vision)
inline constexpr int kFields = 12;
inline constexpr int kMaxProfiles = 16;
// Profile 0 is v92's own play. The rest are written from the strategies of the teams that beat us (PLAYBOOK.md).
inline volatile float kProfiles[kMaxProfiles * kFields] = {
    // terr  aggr  carry until hunt raid  num  focus anti items tfrom vision
    -1.0f, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f,   // 0 base (v92)
};
inline volatile int kNumProfiles = 1;
inline volatile int kCatProfile[x1_categories::kNumCats] = {0, 0, 0, 0, 0, 0, 0};
inline volatile int kForce = X1_PORTFOLIO_FORCE + 1000; // test builds: one profile everywhere (+1000: never zero)

inline int category = -1, profile = 0;
// Runtime values read by the bot (set once by select(), used every turn).
inline float terr = -1.0f, aggr = 1.0f, carry = 1.0f, focus = 0.0f;
inline int carry_until = 0, hunt = 0, raid = 0, numbers = 0, antifeed = 0, items = 0, terr_from = 0, vision = 0;

inline float field(int p, int f) { return kProfiles[p * kFields + f]; }

inline void select(World& w, int team_size) {
    const auto feat = x1_atlas::compute(w, team_size);
    category = x1_categories::classify(feat);
    int p = kCatProfile[category < 0 ? 0 : category];
    const int forced = kForce - 1000;
    if (forced >= 0) p = forced;
    if (p < 0 || p >= kNumProfiles) p = 0;
    profile = p;
    terr = field(p, 0); aggr = field(p, 1); carry = field(p, 2); carry_until = static_cast<int>(field(p, 3));
    hunt = static_cast<int>(field(p, 4)); raid = static_cast<int>(field(p, 5)); numbers = static_cast<int>(field(p, 6));
    focus = field(p, 7); antifeed = static_cast<int>(field(p, 8)); items = static_cast<int>(field(p, 9)); terr_from = static_cast<int>(field(p, 10)); vision = static_cast<int>(field(p, 11));
}

} // namespace x1_portfolio
