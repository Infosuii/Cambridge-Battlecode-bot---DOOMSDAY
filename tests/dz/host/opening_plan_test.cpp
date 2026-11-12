#include "opening_plan.h"
#include <cassert>
#include <functional>
#include <iostream>
#include <random>
using namespace dz;
int main() {
    std::mt19937 rng(71281);
    for(unsigned test=0;test<600;++test) {
        const unsigned workers=1+rng()%4,jobs=1+rng()%4;
        std::array<economy::Assignment,6> first{};
        std::vector<opening::Leg> legs;
        for(unsigned s=0;s<workers;++s) {
            first[s]={static_cast<int>(s),1u<<s,s};
            for(unsigned g=0;g<jobs;++g)legs.push_back({s,static_cast<int>(s),static_cast<int>(10+g),10,
                static_cast<int>(rng()%30),5,static_cast<float>(1+rng()%50),2,3});
        }
        auto plans=opening::extend(first,legs,90);
        float actual=0;unsigned sold=0;
        for(unsigned s=0;s<workers;++s)if(plans[s].valid()) {
            assert(plans[s].first==static_cast<int>(s)&&!(sold&(1u<<(plans[s].next-10))));sold|=1u<<(plans[s].next-10);
            auto leg=std::find_if(legs.begin(),legs.end(),[&](const auto& q){return q.slot==s&&q.to==plans[s].next;});
            assert(leg!=legs.end()&&plans[s].finish==leg->first_finish+leg->travel+leg->work);
            actual+=leg->value/(leg->travel+leg->work);
        }
        std::function<float(unsigned,unsigned)> reference=[&](unsigned s,unsigned used) {
            if(s==workers)return 0.f;float best=reference(s+1,used);
            for(const auto& q:legs)if(q.slot==s&&!(used&(1u<<(q.to-10))))
                best=std::max(best,q.value/(q.travel+q.work)+reference(s+1,used|(1u<<(q.to-10))));
            return best;
        };
        assert(std::abs(actual-reference(0,0))<.0001f);
    }
    std::array<economy::Assignment,6> first{};first[0]={1,1,0};first[1]={2,2,1};
    std::array<opening::Leg,3> legs{{{0,1,2,10,1,5,100},{0,1,3,10,2,5,20},{1,2,3,10,1,5,10}}};
    auto result=opening::extend(first,legs,30);assert(result[0].next==3&&!result[1].valid());
    assert(!opening::extend(first,legs,14)[0].valid());
    assert(!opening::extend(first,legs,30,[]{return false;})[0].valid());
    opening::Commitment commit;assert(commit.start({1,3,20,7,4},10,0,0));
    assert(commit.deadline==120&&commit.current(15,1,4));
    assert(!commit.ready(15,8,0,0)); // Other capturer's generation is insufficient.
    assert(commit.ready(15,8,1,0));
    assert(!commit.current(15,2,4)&&!commit.current(15,1,5));
    assert(!commit.ready(120,8,1,0));
    assert(!commit.start({1,3,20,7,4},110,0,0));
    std::cout<<"600 exhaustive residual opening assignments, finite deadlines, receipts and invalidation passed\n";
}
