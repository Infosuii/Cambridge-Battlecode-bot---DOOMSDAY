#include "../../bots/v67/src/team_memory.h"
#include <cassert>
#include <cstdio>

int main() {
    std::uint64_t memory = team67::put_plan(0, 5, 126);
    for (int s = 0; s < 6; ++s) memory = team67::put_position(memory, s, s * 17, s * 17, true);
    for (int s = 0; s < 6; ++s) {
        int x, y;
        assert(team67::position(memory, s, x, y));
        assert(x == (s * 17 / 5) * 5 + 2 && y == x);
    }
    assert(team67::focus(memory) == 5 && team67::rally(memory) == 126);
    const auto old = memory;
    memory = team67::put_plan(memory, -1, -1);
    assert((memory & ((std::uint64_t{1} << 54) - 1)) == (old & ((std::uint64_t{1} << 54) - 1)));
    assert(team67::focus(memory) == -1 && team67::rally(memory) == -1);
    for (int s = 0; s < 6; ++s) memory = team67::put_position(memory, s, 0, 0, false);
    assert(memory == 0);
    for (int x0 = 0; x0 < 100; ++x0) for (int y0 = 0; y0 < 100; ++y0) {
        const auto bits = team67::put_position(0, 5, x0, y0, true);
        int x, y;
        assert(team67::position(bits, 5, x, y));
        assert(x - x0 >= -2 && x - x0 <= 2 && y - y0 >= -2 && y - y0 <= 2);
    }
    std::puts("v67 shared-position/focus/rally protocol passed");
}
