#include "draft_alias.h"
#include <array>
#include <cassert>
#include <iostream>
int main() {
    draft_alias::Consumed alias;
    const std::array<int,4> lineup{2,6,7,11};
    std::array<bool,32> actual{};
    auto next=[&] {for (int c:lineup) if (!actual[c] && !alias.contains(c)) return c;return -1;};
    assert(next()==2);actual[2]=true;alias.picked(2,2);
    assert(next()==6);actual[6]=true;alias.picked(6,6);
    assert(next()==7);actual[1]=true;alias.picked(7,1);
    assert(next()==11); // replacement fills slot 7; it must not steal every later pick
    assert(alias.contains(7) && !alias.contains(1));
    alias.picked(-1,4);alias.picked(32,4);assert(!alias.contains(-1) && !alias.contains(32));
    draft_alias::Consumed separate;assert(!separate.contains(7));
    draft_alias::Projection projection;
    projection.add(1,false);projection.add(4,false);projection.add(0,true);
    projection.add(0,true);projection.add(0,true); // repeated padding is not three frontliners
    assert(projection.count==3 && projection.front==1);
    projection.add(7,false);assert(projection.count==4 && projection.front==1);
    std::cout<<"Draft replacement: one substitution consumes one slot; later lineup entries and per-team isolation preserved\n";
}
