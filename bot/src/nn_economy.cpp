#include "nn_economy.h"

#if NN_ANY_HEAD || defined(NN_HOST_TEST)
#include <cmath>

namespace nne {
namespace {
float norm(float x, float scale, float lo = 0, float hi = 1) {
    const float v = x / scale;
    // Preserve NaN for the central runtime's explicit rejection path.
    return v < lo ? lo : v > hi ? hi : v;
}
std::uint32_t bank_id(const BankChoice& c) { return !c.go ? 0u : c.safe ? 2u : 1u; }
std::uint32_t buy_id(const Buy& b) {
    return b.kind == BuyKind::plan ? 0u : b.kind == BuyKind::save ? 1u :
           b.kind == BuyKind::shard ? 0x100u + b.item : 0x200u + b.item;
}
void bank_row(const State& s, const BankTerms& t, const BankChoice& c, bool teacher, float* f) {
    f[0] = teacher; f[1] = c.go; f[2] = c.safe;
    f[3] = norm(static_cast<float>(c.dist), 128);
    f[4] = norm(static_cast<float>(s.gems), 200);
    f[5] = norm(s.hp, s.max_hp > 0 ? s.max_hp : 1);
    f[6] = norm(static_cast<float>(s.gold), 600);
    f[7] = norm(static_cast<float>(s.round), 2000);
    f[8] = norm(static_cast<float>(s.ally_score), 1000);
    f[9] = norm(static_cast<float>(s.enemy_score), 1000);
    f[10] = norm(static_cast<float>(s.ally_score) - static_cast<float>(s.enemy_score), 1000, -1, 1);
    f[11] = t.force; f[12] = t.wins; f[13] = t.late; f[14] = t.end_bank;
    f[15] = t.rhythm; f[16] = t.edge; f[17] = t.threatened;
    f[18] = norm(static_cast<float>(s.gems / 10 + (s.gems % 10 > 0)), 20);
    f[19] = norm(static_cast<float>(s.gems), 10.0f * (static_cast<float>(c.dist) + 1));
}
void shop_row(const State& s, const Buy& b, bool teacher, float* f) {
    const bool shard = b.kind == BuyKind::shard;
    f[0] = teacher; f[1] = b.kind == BuyKind::save; f[2] = b.kind == BuyKind::plan;
    f[3] = shard; f[4] = b.kind == BuyKind::consumable;
    f[5] = shard ? norm(static_cast<float>(b.item / 6), 6) : 0;
    f[6] = shard ? norm(static_cast<float>((b.item % 6) / 2), 2) : 0;
    f[7] = norm(static_cast<float>(b.count), 20);
    f[8] = norm(static_cast<float>(b.cost), 600);
    f[9] = b.kind == BuyKind::plan ? 0 : norm(static_cast<float>(s.gold) - static_cast<float>(b.cost), 600);
    f[10] = norm(static_cast<float>(b.owned), 100);
    f[11] = shard ? norm(static_cast<float>(b.owned % 5), 4) : 0;
    f[12] = norm(s.hp, s.max_hp > 0 ? s.max_hp : 1);
    f[13] = norm(static_cast<float>(s.gems), 200);
    f[14] = norm(static_cast<float>(s.gold), 600);
    f[15] = norm(static_cast<float>(s.round), 2000);
    f[16] = norm(static_cast<float>(s.ally_score) - static_cast<float>(s.enemy_score), 1000, -1, 1);
    f[17] = b.kind == BuyKind::consumable ? norm(static_cast<float>(b.item), 4) : 0;
    f[18] = norm(static_cast<float>(s.ally_score), 1000);
    f[19] = norm(static_cast<float>(s.enemy_score), 1000);
}
} // namespace

int build_bank(const State& s, const BankTerms& t, nnh::Decision& d, BankChoice* choices) {
    d.head = nncfg::H::bank; d.F = kBankF; d.K = 1; d.context = 0;
    choices[0] = {t.go, t.safe, t.dist};
    auto add = [&](BankChoice c) {
        for (int i = 0; i < d.K; ++i) if (bank_id(choices[i]) == bank_id(c)) return;
        choices[d.K++] = c;
    };
    // Forced, winning and deadline-critical deposits are deterministic priorities.
    if (!t.force && !t.wins && !t.late) add({false, t.safe, t.dist});
    add({true, t.safe, t.dist});
    if (t.safe && t.raw_dist >= 0) add({true, false, t.raw_dist});
    for (int i = 0; i < d.K; ++i) {
        d.id[i] = bank_id(choices[i]); d.legal[i] = 1; d.prior[i] = i ? -0.25f : 0;
        bank_row(s, t, choices[i], i == 0, d.feat + i * kBankF);
    }
    return d.K;
}

int build_shop(const State& s, const Buy& ignored_preview, const Buy* options, int n, nnh::Decision& d, Buy* choices) {
    d.head = nncfg::H::shop; d.F = kShopF; d.K = 2; d.context = 0;
    (void)ignored_preview; // Compatibility argument; teacher option never reconstructs/duplicates its buy plan.
    choices[0] = Buy{}; choices[0].kind = BuyKind::plan;
    choices[1] = Buy{};
    const int limit = n < 0 ? 0 : n > nnh::kMaxK - 2 ? nnh::kMaxK - 2 : n;
    for (int i = 0; i < limit; ++i) {
        const auto& c = options[i];
        if (c.kind != BuyKind::shard && c.kind != BuyKind::consumable) continue;
        bool duplicate = false;
        for (int j = 2; j < d.K; ++j) duplicate |= buy_id(choices[j]) == buy_id(c);
        if (!duplicate) choices[d.K++] = c;
    }
    for (int i = 0; i < d.K; ++i) {
        d.id[i] = buy_id(choices[i]);
        d.legal[i] = i == 0 || (choices[i].legal && choices[i].cost <= s.gold);
        d.prior[i] = i ? -0.25f : 0;
        shop_row(s, choices[i], i == 0, d.feat + i * kShopF);
    }
    return d.K;
}
} // namespace nne

#if !defined(NN_HOST_TEST)
#include "bot.h"
#include "nn_budget.h"

struct nn_economy_access {
    static nne::State state(const Bot& b) {
        return {b.hp, b.max_hp, b.gems, b.gold, b.round, b.ally_score, b.enemy_score};
    }
    static void spent(Bot& b, int gold) { b.gold -= gold; }
    static int altar_distance(const Bot& b) {
        const auto dist = fdist(b.w.altar_field, b.pos);
        return dist == kUnreach ? -1 : static_cast<int>(dist);
    }
};

namespace nne {
namespace {
struct Stamp { std::uint32_t round = 0, champion = 0; bool valid = false; };
bool once(Stamp& s) {
    const auto r = nnb::round_now(), c = nnb::champion_now();
    if (s.valid && s.round == r && s.champion == c) return false;
    s = {r, c, true};
    return true;
}
Stamp bank_stamp, shop_stamp;
} // namespace

BankChoice bank(const Bot& bot, const BankTerms& teacher) {
    const BankChoice fallback{teacher.go, teacher.safe, teacher.dist};
    if (!once(bank_stamp) || !nnh::admit(bot, nncfg::H::bank, 3, kBankFeatureFuel)) return fallback;
    BankTerms t = teacher;
    if (t.safe) t.raw_dist = nn_economy_access::altar_distance(bot);
    static nnh::Decision d;
    static BankChoice choices[3];
    build_bank(nn_economy_access::state(bot), t, d, choices);
    const auto r = nnh::decide(bot, d);
    return r.choice >= 0 && r.choice < d.K ? choices[r.choice] : fallback;
}

bool shop(Bot& bot) {
    if (!once(shop_stamp) || !nnh::admit(bot, nncfg::H::shop, nnh::kMaxK, kShopFeatureFuel)) return false;
    const State s = nn_economy_access::state(bot);
    Buy teacher; teacher.kind = BuyKind::plan; // Opaque guarded executor, no first-purchase preview.
    static Buy options[14], choices[nnh::kMaxK];
    static nnh::Decision d;
    using it = bc::item_type;
    const it shards[] = {it::monster_shard_of_strength, it::monster_shard_of_focus,
        it::jungle_shard_of_health, it::power_shard_of_strength, it::power_shard_of_focus,
        it::power_shard_of_health, it::durability_shard_of_health, it::home_shard_of_health,
        it::treasure_shard_of_strength, it::treasure_shard_of_focus,
        it::bruiser_shard_of_strength, it::bruiser_shard_of_focus};
    auto& me = bc::self();
    try {
        const auto counts = me.item_count();
        for (int i = 0; i < 12; ++i) {
            const int cost = static_cast<int>(shards[i].info().cost);
            int owned = static_cast<int>(counts[shards[i]]);
            if (const auto emblem = shards[i].result()) owned += 5 * static_cast<int>(counts[*emblem]);
            options[i] = {BuyKind::shard, static_cast<std::uint32_t>(shards[i]), 1, cost, owned,
                          s.gold >= cost && me.can_buy(shards[i])};
        }
        const bc::consumable_type cons[] = {bc::consumable_type::tp_crystal, bc::consumable_type::altar_lock};
        for (int i = 0; i < 2; ++i) options[12+i] = {BuyKind::consumable, static_cast<std::uint32_t>(cons[i]),
            1, static_cast<int>(cons[i].cost()), 0, me.can_buy(cons[i])};
    } catch (...) {
        // Complete the admitted decision with a legal teacher-only set; no stale partially built options.
        build_shop(s, teacher, nullptr, 0, d, choices);
        d.K = 1;
        (void)nnh::decide(bot, d);
        return false;
    }
    build_shop(s, teacher, options, 14, d, choices);
    const auto r = nnh::decide(bot, d);
    if (r.choice <= 0 || r.choice >= d.K) return false;
    const Buy b = choices[r.choice];
    if (b.kind == BuyKind::save) return true;
    // SDK state may have changed since generation: execution always rechecks exact affordability/location.
    try {
        if (b.kind == BuyKind::shard) {
            const it item{b.item};
            if (!me.can_buy(item, static_cast<std::uint32_t>(b.count))) return true;
            me.buy(item, static_cast<std::uint32_t>(b.count));
        } else {
            const bc::consumable_type item{b.item};
            if (!me.can_buy(item)) return true;
            me.buy(item);
        }
        nn_economy_access::spent(bot, b.cost);
        return true;
    } catch (...) { return true; }
}
} // namespace nne
#endif // !NN_HOST_TEST
#endif // NN_ANY_HEAD || NN_HOST_TEST
