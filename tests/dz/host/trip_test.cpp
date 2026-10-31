#include "economy_trip.h"
#include "siege_model.h"
#include <cassert>
#include <iostream>
#include <random>
using namespace dz;
int main() {
    trip::Network graph;graph.count=3;
    graph.nodes[0]={10,4,0,10,20,0};graph.nodes[1]={11,4,0,10,20,0};graph.nodes[2]={12,4,0,10,20,0};
    graph.arrival.fill(3);graph.delivery.fill(5);
    for(auto& row:graph.travel)row.fill(2);
    macro::Context c{100,20,.1f,.25f,.1f};
    auto bank=[](float){return 2;};auto budget=[] {return true;};
    auto q=trip::best(c,graph,0,0,bank,budget);
    assert(q.count==3&&q.jobs[0]==10&&q.jobs[1]!=q.jobs[2]&&q.finish==26);
    assert(q.option.gems==30&&q.option.gold==60);
    c.horizon=14;q=trip::best(c,graph,0,0,bank,budget);
    assert(q.count==1&&q.finish==14); // Delivery fits exactly, a second job does not.
    c.horizon=13;assert(trip::best(c,graph,0,0,bank,budget).count==0);
    c.horizon=100;graph.travel[0][1]=trip::unreachable;graph.travel[0][2]=trip::unreachable;
    assert(trip::best(c,graph,0,0,bank,budget).count==1);
    graph.nodes[0].ready=90;assert(trip::best(c,graph,0,0,bank,budget).count==0);
    graph.nodes[0].ready=0;assert(trip::best(c,graph,0,0,bank,[]{return false;}).count==0);
    graph.nodes[1].id=10;assert(trip::best(c,graph,0,0,bank,budget).count==0);
    graph.nodes[1].id=11;
    for(auto& row:graph.travel)row.fill(2);
    // Independent explicit-schedule enumeration checks complete delivery and
    // every route permutation on small random asymmetric travel networks.
    std::mt19937 random(92371);
    for(unsigned trial=0;trial<1000;++trial) {
        graph.count=4;c.horizon=20+random()%80;c.bag=random()%30;c.income=(random()%20)/20.f;
        for(unsigned i=0;i<4;++i) {
            graph.nodes[i]={static_cast<int>(i),1+static_cast<int>(random()%9),static_cast<int>(random()%15),
                static_cast<float>(random()%20),static_cast<float>(random()%30),0};
            graph.arrival[i]=random()%9;graph.delivery[i]=random()%12;
            for(unsigned j=0;j<4;++j)graph.travel[i][j]=random()%12;
        }
        float reference=-std::numeric_limits<float>::infinity();
        for(int second=-1;second<4;++second)for(int third=-1;third<4;++third) {
            if(second==0||third==0||(second<0&&third>=0)||(second>=0&&second==third))continue;
            const std::array<int,3> path{{0,second,third}};
            int time=0,last=-1;float gems=0,gold=0;
            for(int u:path) {
                if(u<0)break;
                time+=last<0?graph.arrival[u]:graph.travel[last][u];
                time=std::max(time,graph.nodes[u].ready)+graph.nodes[u].work;
                gems+=graph.nodes[u].gems;gold+=graph.nodes[u].gold;last=u;
            }
            time+=graph.delivery[last]+2;if(time>c.horizon)continue;
            const float score=c.bag+gems+c.gold_price*gold+(c.income+c.gold_price*c.gold_income)*(c.horizon-time);
            reference=std::max(reference,score);
        }
        q=trip::best(c,graph,0,0,bank,budget);
        assert((!q.count&&!std::isfinite(reference))||(q.count&&std::abs(macro::value(c,q.option)-reference)<.001f));
    }
    trip::Commitment task;trip::Plan fixed;fixed.count=2;fixed.jobs={10,11,-1};fixed.ends={8,15,0};fixed.finish=22;fixed.altar=0;
    task.start(fixed,100,10,5);const int deadline=task.deadline;
    task.advance(101,15,false,true);assert(task.job()==10); // Unrelated kill income isn't capture evidence.
    task.advance(108,20,true,true);assert(task.job()==11&&task.deadline==deadline);
    task.advance(115,30,true,true);assert(task.phase==trip::Phase::Deliver);
    task.advance(300,30,false,true);assert(task.phase==trip::Phase::Deliver); // Actually bank before another circuit.
    task.advance(301,0,false,true);assert(!task.active());
    task.start(fixed,100,10,5);task.advance(114,10,false,true);
    assert(task.phase==trip::Phase::Deliver); // Absolute missed first-job deadline can't slide.
    task.start(fixed,100,0,5);task.advance(114,0,false,true);assert(!task.active());
    task.start(fixed,100,10,5);task.advance(102,5,false,true);assert(!task.active());
    task.start(fixed,100,10,5);task.advance(102,10,false,false);assert(task.job()==11); // Task stolen/abandoned.
    fixed.shop=true;task.start(fixed,100,10,5);
    task.advance(108,20,true,true);task.advance(115,30,true,true);task.advance(120,0,false,true);
    assert(task.phase==trip::Phase::Shop);task.advance(150,0,false,true,true);assert(!task.active());
    siege::RecoveryLatch recovery;
    assert(recovery.update(true,false,300,1000));
    assert(recovery.update(false,false,300,1000)); // Leaving camp reach isn't healing.
    assert(recovery.update(false,false,1000,1000)); // A field heal doesn't prove the home leg completed.
    assert(recovery.update(false,true,999,1000));
    assert(!recovery.update(false,true,1000,1000));
    std::cout<<"1000 complete-circuit schedule references; bank commitments, deadlines, stolen jobs and partial-shard counterfactuals passed\n";
}
