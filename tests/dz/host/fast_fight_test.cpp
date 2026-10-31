#include "fight.h"
#include <cstdio>
#include <random>
// simulate_fight_fast must reproduce simulate_fight exactly (same float operations in the same order).
int main() {
    std::mt19937 rng(12345);
    std::uniform_real_distribution<float> hp(0.f, 1600.f), dmg(0.f, 120.f);
    std::uniform_int_distribution<int> n(1, 12), m(0, 12), zero(0, 9), rounds(1, 60);
    for (int t = 0; t < 200000; ++t) {
        std::array<dz::Fighter, 12> a{}, b{};
        const int na = n(rng), nb = m(rng);
        for (int i = 0; i < na; ++i) a[i] = {zero(rng) ? hp(rng) : 0.f, zero(rng) ? dmg(rng) : 0.f};
        for (int i = 0; i < nb; ++i) b[i] = {zero(rng) ? hp(rng) : 0.f, zero(rng) ? dmg(rng) : 0.f};
        if (t % 7 == 0 && nb > 1) b[1].hp = b[0].hp; // Ties for the weakest target.
        const unsigned r = static_cast<unsigned>(rounds(rng));
        const auto x = dz::simulate_fight(std::span<const dz::Fighter>(a.data(), na), std::span<const dz::Fighter>(b.data(), nb), r);
        const auto y = dz::simulate_fight_fast(std::span<const dz::Fighter>(a.data(), na), std::span<const dz::Fighter>(b.data(), nb), r);
        if (x.valid != y.valid || x.ours_alive != y.ours_alive || x.theirs_alive != y.theirs_alive || x.rounds != y.rounds || x.self_alive != y.self_alive) {
            std::printf("fast fight mismatch at case %d", t); std::puts(""); return 1;
        }
    }
    std::puts("200000 random fights: event-stepped simulate_fight_fast matches simulate_fight exactly");
}
