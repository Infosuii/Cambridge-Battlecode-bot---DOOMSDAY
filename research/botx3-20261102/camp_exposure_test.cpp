#include "camp_exposure.h"
#include <array>
#include <cassert>
#include <iostream>
int main() {
    std::array<camp_exposure::Camp,camp_exposure::capacity> camps;
    int n=0;
    for (int y=0;y<7;++y) for (int x=0;x<7;++x) camps[n++]={x,y,20,3};
    assert(camp_exposure::incoming(camps.data(),n,3,3)==980);
    assert(camp_exposure::incoming(camps.data(),32,3,3)==640);
    assert(camp_exposure::incoming(camps.data(),n,0,3)==560);
    assert(camp_exposure::incoming(camps.data(),n,20,20)==0);
    n=0;for (int y=0;y<15;++y) for (int x=0;x<15;++x) camps[n++]={x,y,1,5};
    assert(n<camp_exposure::capacity);
    assert(camp_exposure::incoming(camps.data(),n,7,7)==121);
    std::cout<<"Camp safety: 49-monster truncation reproduced, full damage/range/edge counts and 225-tile bound passed\n";
}
