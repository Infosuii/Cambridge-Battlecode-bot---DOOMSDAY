#pragma once
namespace bank_delivery {
struct Commitment {
    int until=-1;
    bool announced=false;
    bool begin(int round,int distance,int bag) {
        if (distance<0 || bag<=0) return false;
        if (until<round) until=round+2*distance+(bag+9)/10+10;
        return true;
    }
    bool active(int round,int bag,bool no_bank,bool cooling_down) {
        if (until<0) return false;
        if (bag<=0 || no_bank || cooling_down || round>until) {until=-1;return false;}
        return true;
    }
};
}
