#include "feed_control.h"
#include <cassert>
#include <iostream>
int main() {
    using namespace feed_control;
    assert(collapsing(3,3,3,false));assert(!collapsing(3,3,3,true));
    assert(collapsing(4,1,3,true));assert(!collapsing(2,0,3,true));
    DeathWindow d;d.observe(0,42,false,1);assert(d.recent(1,150)==0);
    d.observe(0,42,true,2);d.observe(0,42,false,3);d.observe(0,42,false,4);
    assert(d.recent(4,150)==1);assert(d.recent(153,150)==1);assert(d.recent(154,150)==0);
    for (int i=0;i<40;++i) {d.observe(0,42,true,200+2*i);d.observe(0,42,false,201+2*i);}
    assert(d.recent(280,150)==40); // no 16-event clipping when comparing two busy teams
    d.observe(0,99,false,281);assert(d.recent(281,150)==40);
    d.observe(9,42,false,282);assert(d.recent(282,150)==40);
    assert(d.recent(500,150)==0);
    std::cout<<"Feeding control: balanced trades, net collapse, initialization, repeat observations, expiry and busy-window counts passed\n";
}
