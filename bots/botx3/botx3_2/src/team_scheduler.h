#pragma once
#include <algorithm>
#include <array>
#include <cmath>

// Bounded team job auction. All state is supplied by a legal-view adapter.
// A bid includes synchronized arrivals, pooled camp service, one capture owner,
// and amortized gem delivery. Greedy disjoint bids reserve entire crews.
namespace team_scheduler {
constexpr int workers = 6, jobs = 16, unreachable = 30000;
constexpr int idle = -1, bank = -3;
struct Actor {
    bool available = false;
    float hp = 0, dps = 1;
    int carried = 0, bank_distance = unreachable, threshold = 60;
    int current = idle, fixed = idle;
};
struct Job {
    int id = idle, ready = 0;
    float hp = 0, soak = 0, gems = 0, gold_value = 0, risk = 1;
    int bank_distance = unreachable, capture = 5;
    std::array<int, workers> travel{};
    unsigned excluded = 0;
};
struct Result {
    std::array<int, workers> target{};
    std::array<int, workers> crew{};
    float predicted_value = 0;
    int bids = 0;
    Result() { target.fill(idle); crew.fill(1); }
};
// Fastest visible cohort whose existing bags can finish the race. No hidden
// inventory is inferred. A capture in progress keeps its owner until completed.
inline unsigned bank_cohort(const std::array<Actor,workers>& actor,int remaining) {
    if (remaining<=0) return 0;
    int order[workers],n=0,available=0;
    for (int i=0;i<workers;++i) if (actor[i].available && actor[i].fixed<0 && actor[i].carried>0 && actor[i].bank_distance<unreachable) {
        const int finish=actor[i].bank_distance+(actor[i].carried+9)/10;
        int j=n++;
        while (j && actor[order[j-1]].bank_distance+(actor[order[j-1]].carried+9)/10>finish) {
            order[j]=order[j-1];--j;
        }
        order[j]=i;available+=actor[i].carried;
    }
    if (available<remaining) return 0;
    unsigned mask=0;
    for (int i=0;i<n && remaining>0;++i) {mask|=1u<<order[i];remaining-=actor[order[i]].carried;}
    return mask;
}
inline Result assign(const std::array<Actor, workers>& actors, const Job* job, int count) {
    Result out;
    unsigned used = 0;
    for (int i=0;i<workers;++i) {
        if (!actors[i].available) used |= 1u<<i;
        else if (actors[i].fixed >= 0) {out.target[i]=actors[i].fixed; used|=1u<<i;}
        else if (actors[i].carried >= actors[i].threshold && actors[i].bank_distance < unreachable) {
            out.target[i]=bank;used|=1u<<i;
        }
    }
    struct Bid { unsigned mask=0; int job=-1, size=0; float rate=0, value=0; };
    count=std::min(count,jobs);
    unsigned taken=0;
    for (int step=0;step<workers;++step) {
    Bid best;
    for (int k=0;k<count;++k) {
        const auto& g=job[k];
        if (g.id<0 || g.risk<=0 || (taken&(1u<<k))) continue;
        bool fixed_owner=false;
        for (int i=0;i<workers;++i) fixed_owner |= actors[i].available && actors[i].fixed==g.id;
        if (fixed_owner && g.hp<=0) continue;
        int order[workers],n=0;
        float key[workers];
        for (int i=0;i<workers;++i) {
            if ((used|g.excluded)&(1u<<i) || g.travel[i]>=unreachable) continue;
            const float value=(g.travel[i]+g.hp/std::max(1.0f,actors[i].dps)) /
                (actors[i].current==g.id ? 1.2f : 1.0f);
            int p=n++;
            while (p && key[p-1]>value) {key[p]=key[p-1];order[p]=order[p-1];--p;}
            key[p]=value;order[p]=i;
        }
        float power=0,pool=0;
        int arrive=0,bag=0;
        unsigned mask=0;
        for (int m=0;m<std::min(n,g.hp<=0 ? 1 : 3);++m) {
            const int i=order[m];mask|=1u<<i;
            power+=actors[i].dps;pool+=actors[i].hp;
            arrive=std::max(arrive,g.travel[i]);
            bag=std::max(bag,actors[i].carried);
            const float clear=g.hp/std::max(1.0f,power);
            if (g.soak/std::max(1.0f,power)>pool*0.65f) continue;
            const int wait=std::max(0,g.ready-arrive);
            // Travel plus synchronization/service are paid by each crew member;
            // only one owner captures and delivers the reward.
            const float service=(m+1)*(arrive+wait+clear)+g.capture;
            float delivery=0;
            if (g.gems>0 && g.bank_distance<unreachable)
                delivery=(g.bank_distance+std::ceil((bag+g.gems)/10.0f))*g.gems/std::max(1.0f,bag+g.gems);
            const float cost=std::max(1.0f,service+delivery);
            float value=(g.gems+g.gold_value)*g.risk;
            bool keep=false;
            for (int a=0;a<workers;++a) if ((mask&(1u<<a)) && actors[a].current==g.id) keep=true;
            const float rate=value/cost*(keep ? 1.15f : 1.0f);
            ++out.bids;
            if (rate>best.rate) best={mask,k,m+1,rate,value};
        }
    }
        if (best.job<0) break;
        const auto& b=best;used|=b.mask;taken|=1u<<b.job;
        out.predicted_value+=b.value;
        for (int a=0;a<workers;++a) if (b.mask&(1u<<a)) {
            out.target[a]=job[b.job].id;out.crew[a]=b.size;
        }
    }
    return out;
}
}
