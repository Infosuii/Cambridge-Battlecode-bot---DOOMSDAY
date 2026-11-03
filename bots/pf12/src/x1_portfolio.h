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
// 11 vision    1 = spend every ward charge on scouting wards (ward_vision) + world update; 2 = light (spare fuel, no update)
// 12 terr_ramp rounds to move from the base territory value to terr, starting at terr_from (0 = a step)
// 13 coh_mult  cohesion multiplier (tune::kCohesion) until coh_until (1 = keep)
// 14 coh_until round the cohesion multiplier stops
// 15 pack      1 = pack play: v92's buddy pair farming (NOVA_DUO) on every map, regroup to a teammate when caught
// 16 pack_until round pack farming stops (0 = NOVA_DUO_UNTIL)
// 17 buddy_k   group value falls by this per tile beyond NOVA_BUDDY_DIST from the buddy's target (0 = NOVA_BUDDY)
inline constexpr int kFields = 18;
inline constexpr int kMaxProfiles = 16;
// Profile 0 is v92's own play. The rest are written from the strategies of the teams that beat us (PLAYBOOK.md).
inline volatile float kProfiles[kMaxProfiles * kFields] = {
    // terr  aggr  carry until hunt raid  num  focus anti items tfrom vision
    -1.0f, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f,   // 0 base (v92)
    -1.0f, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f,   // 1 vision: every ward charge scouts
     0.7f, 1.0f, 0.75f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 300.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f,   // 2 raid and bank (no vision: profile 1 lost 47-57 on the ladder): enemy-half camps from round 300, raider, smaller bags
    -1.0f, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 1.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f,   // 3 stat fighter: Treasure + Bruiser, numbers edge, focus fire
    -1.0f, 1.0f, 0.6f, 400.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f,   // 4 early bank: bank at 0.6x bag until round 400
    -1.0f, 1.0f, 0.8f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 2.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f,   // 5 top-team economy: Treasure / Jungle / Bruiser / Power opening
     0.0f, 0.8f, 0.7f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f,   // 6 fortress: own half, calmer fights, small bags, antifeed
     1.0f, 1.2f, 1.0f, 0.0f, 2.0f, 0.0f, 1.0f, 1.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f,   // 7 push: invade, fight harder, hunt further, Bruiser, numbers, focus
    -1.0f, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 2.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f,   // 8 vision light: wards with spare fuel only, no extra world update
     1.0f, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 300.0f, 0.0f, 600.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f,   // 9 progressive expansion: enemy-half value from base at round 300 to full by 900
    -1.0f, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 4.0f, 250.0f, 0.0f, 0.0f, 0.0f,   // 10 pack opening: cohesion x4 until round 250
     1.0f, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 300.0f, 2.0f, 600.0f, 4.0f, 250.0f, 0.0f, 0.0f, 0.0f,   // 11 pack + expand + vision light
     0.7f, 1.0f, 0.75f, 0.0f, 0.0f, 1.0f, 1.0f, 1.0f, 0.0f, 1.0f, 300.0f, 2.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f,   // 12 combo: vision light + raid and bank + stat fighter
    -1.0f, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 1.0f, 400.0f, 0.15f, // 13 pack play: pair farming to round 400, buddy-near camps, regroup, numbers edge
};
inline volatile int kNumProfiles = 14;
inline volatile int kCatProfile[x1_categories::kNumCats] = {0, 0, 0, 0, 0, 0, 0};
inline volatile int kForce = X1_PORTFOLIO_FORCE + 1000; // test builds: one profile everywhere (+1000: never zero)

inline int category = -1, profile = 0;
// Runtime values read by the bot (set once by select(), used every turn).
inline float terr = -1.0f, aggr = 1.0f, carry = 1.0f, focus = 0.0f;
inline int carry_until = 0, hunt = 0, raid = 0, numbers = 0, antifeed = 0, items = 0, terr_from = 0, vision = 0;
inline float terr_ramp = 0.0f, coh_mult = 1.0f; inline int coh_until = 0;
inline int pack = 0, pack_until = 0; inline float buddy_k = 0.0f;

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
    terr_ramp = field(p, 12); coh_mult = field(p, 13); coh_until = static_cast<int>(field(p, 14));
    pack = static_cast<int>(field(p, 15)); pack_until = static_cast<int>(field(p, 16)); buddy_k = field(p, 17);
}

} // namespace x1_portfolio
