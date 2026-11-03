#include "g70_arrival.h"
#include <cassert>
#include <cstdio>

int main() {
    using g70::ActionWindow;
    using g70::basic_shots;
    const ActionWindow ranged_two{2, false, true, true, false, false, true};
    const ActionWindow melee_two{2, true, true, true, false, false, true};
    const ActionWindow ranged_one{1, false, true, true, false, false, true};
    const ActionWindow melee_one{1, true, true, true, false, false, true};
    assert(basic_shots(ranged_two) == 0); // Two walks leave no ranged basic in this horizon.
    assert(basic_shots(melee_two) == 1);  // Melee can hit after the second approach step.
    assert(basic_shots(ranged_one) == 1);
    assert(basic_shots(melee_one) == 2);
    assert(basic_shots(ActionWindow{0, false, true, true, true, false, true}) == 1);
    assert(basic_shots(ActionWindow{1, false, true, true, true, false, true}) == 0);
    assert(basic_shots(ActionWindow{0, true, true, true, false, true, true}) == 0);
    assert(basic_shots(ActionWindow{-1, true, true, true, false, false, true}) == 0);
    assert(basic_shots(ActionWindow{0, true, true, false, false, false, true}) == 1);
    assert(basic_shots(ActionWindow{1, true, false, true, false, false, true}) == 1);
    assert(basic_shots(ActionWindow{0, true, true, false, false, false, false}) == 0);
    assert(basic_shots(melee_one, 1) == 1);
    assert(basic_shots(ranged_one, 1) == 0);
    assert(basic_shots(melee_one, 0) == 0);
    assert(basic_shots(melee_one, 10) == 2); // Fixed horizon bounds optional work.
    std::puts("15 arrival/action-budget cases passed; isolated prototype only.");
}
