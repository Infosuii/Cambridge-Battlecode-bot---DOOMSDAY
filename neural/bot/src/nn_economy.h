// Economy candidates. Pure POD builders are shared with native synthetic parity tests.
#pragma once
#include "nn_head.h"

namespace nne {
inline constexpr int kBankF = 20, kShopF = 20;
inline constexpr std::uint32_t kBankFeatureFuel = 1800, kShopFeatureFuel = 6500;

struct State {
    float hp = 0, max_hp = 1;
    int gems = 0, gold = 0, round = 0, ally_score = 0, enemy_score = 0;
};
struct BankTerms {
    bool go = false, safe = false, force = false, wins = false, late = false;
    bool end_bank = false, rhythm = false, edge = false, threatened = false;
    int dist = 0, raw_dist = -1;
};
struct BankChoice { bool go; bool safe; int dist; };

// Stable bank IDs: 0 continue, 1 static nearest reachable altar, 2 threat-avoiding nearest reachable altar.
int build_bank(const State& s, const BankTerms& t, nnh::Decision& d, BankChoice* choices);

enum class BuyKind : unsigned char { plan = 0, save = 1, shard = 2, consumable = 3 };
struct Buy {
    BuyKind kind = BuyKind::save;
    std::uint32_t item = 0;
    int count = 0, cost = 0, owned = 0;
    bool legal = true;
};
// Teacher plan is an opaque guarded option: its unchanged executor may make multiple purchases. Its item/count/
// cost/owned fields are always zero; no duplicate build_for preview is constructed. Alternatives buy one item.
// IDs: plan=0, save=1, shard=0x100+SDK item ID, consumable=0x200+SDK consumable ID.
int build_shop(const State& s, const Buy& ignored_preview, const Buy* options, int n,
               nnh::Decision& d, Buy* choices);

// SDK glue: admission precedes state/features/legality queries. Once per (round, champion).
BankChoice bank(const Bot& bot, const BankTerms& teacher);
// true means a neural save/single purchase completed; false means execute the complete unchanged teacher plan.
bool shop(Bot& bot);
} // namespace nne
