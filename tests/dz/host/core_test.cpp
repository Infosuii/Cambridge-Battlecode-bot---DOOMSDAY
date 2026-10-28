#include "core.h"
#include "protocol.h"
#include <cassert>
#include <iostream>

int main() {
    using namespace dz;
    static_assert(tier_for(60000) == Tier::Full);
    static_assert(tier_for(59999) == Tier::Lean);
    static_assert(tier_for(24999) == Tier::Fallback);
    unsigned checks = 0;
    const std::uint64_t sentinel = 0xa5379876543210ffULL;
    for (unsigned index = 0; index < protocol::slots; ++index) for (unsigned obj = 0; obj < 128; ++obj)
        for (bool onsite : {false, true}) {
            auto word = protocol::with_slot(sentinel, index, {static_cast<std::uint8_t>(obj), onsite});
            const auto got = protocol::slot(word, index);
            assert(got.objective == obj && got.onsite == onsite);
            assert((word >> 48) == (sentinel >> 48));
            for (unsigned other = 0; other < protocol::slots; ++other) if (other != index) {
                assert(protocol::slot(word, other).objective == protocol::slot(sentinel, other).objective);
                assert(protocol::slot(word, other).onsite == protocol::slot(sentinel, other).onsite);
            }
            ++checks;
        }
    for (unsigned i = 0; i < 6; ++i) assert(protocol::slot(protocol::empty_word(), i).objective == protocol::idle);
    assert(protocol::group_code(111) == 111 && protocol::group_code(112) == protocol::idle);
    assert(protocol::with_slot(sentinel, 6, {0,false}) == sentinel);
    bool stale = false, action_ran = false;
    try { require_current(4, [] { return 5u; }); action_ran = true; } catch (const StaleTurn&) { stale = true; }
    assert(stale && !action_ran);
    require_current(5, [] { return 5u; });
    Contract contract;
    contract.start(2, 0, 20, 500, 5);
    assert(contract.progressing(5, 20, 500, 5));
    assert(!contract.progressing(6, 20, 500, 5));
    assert(contract.progressing(6, 19, 500, 5));
    assert(contract.progressing(11, 19, 400, 5));
    assert(contract.progressing(16, 19, 400, 4));
    assert(!contract.progressing(22, 19, 400, 4));
    GroupBelief b; b.state = GroupState::Partial; b.hp = 123;
    assert(b.available(100) && b.hp == 123); // Unattended partial HP is retained.
    b.state = GroupState::Respawning; b.ready = 150;
    assert(!b.available(149) && b.available(150));
    assert(!bank_now(0, 0, 999, 1000));
    assert(bank_now(1, 40, 999, 1000));
    assert(bank_now(30, 40, 0, 1000));
    assert(bank_now(1, 8, 0, 1000));
    assert(!bank_now(29, 9, 0, 1000));
    std::cout << checks << " protocol cases; guard, contract, ledger and bank checks passed\n";
}
