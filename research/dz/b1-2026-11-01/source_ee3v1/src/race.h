#pragma once
#include <algorithm>
#include <cmath>
namespace dz {
struct RaceClock {
    int sampled=-1,ours=0,theirs=0;
    float our_rate=0,their_rate=0;
    void observe(int round,int own,int enemy) {
        if(round<0||own<0||enemy<0||round<=sampled)return;
        if(sampled>=0) {
            const float span=round-sampled,weight=std::min(1.f,span/100.f);
            our_rate=(1-weight)*our_rate+weight*std::max(0,own-ours)/span;
            their_rate=(1-weight)*their_rate+weight*std::max(0,enemy-theirs)/span;
        }
        sampled=round;ours=own;theirs=enemy;
    }
    int remaining(int round,int maximum,int winning,float carried) const {
        int horizon=std::max(1,maximum-round);
        // Only a team already near the finish can shorten the hard game clock.
        // Early banking bursts do not manufacture an imminent endgame.
        auto estimate=[&](int bank,float rate,float bag) {
            if(bank<winning-200||rate<.05f)return horizon;
            return std::max(1,static_cast<int>(std::ceil(std::max(0.f,winning-bank-.7f*bag)/rate)));
        };
        return std::min({horizon,estimate(ours,our_rate,carried),estimate(theirs,their_rate,0)});
    }
};
}
