#include "economy_trip.h"
#include "siege_model.h"
#include "ledger.h"
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
    graph={};graph.count=1;graph.nodes[0]={4,5,0,10,0,0,20,8,100,100};
    graph.arrival[0]=2;graph.delivery[0]=30;graph.travel[0][0]=2;
    graph.loss_budget=350;c={200,0,.1f,0,0};q=trip::best(c,graph,0,0,bank,budget);
    assert(q.count==3&&q.jobs[0]==4&&q.jobs[1]==4&&q.jobs[2]==4&&q.ends[0]==7&&q.ends[1]==35&&q.ends[2]==63);
    assert((q.ordinals==std::array<unsigned,3>({0,1,2})&&q.finish==95));
    graph.loss_budget=200;q=trip::best(c,graph,0,0,bank,budget);assert(q.count==1); // Exact HP floor is excluded.
    graph.nodes[0].renewal=0;graph.loss_budget=350;q=trip::best(c,graph,0,0,bank,budget);assert(q.count==1);
    // Exhaustively enumerate short schedules independently with replenishment,
    // asymmetric travel, full-generation work and a cumulative damage budget.
    for(unsigned trial=0;trial<1000;++trial) {
        graph={};graph.count=3;graph.loss_budget=1+random()%50;c={30+static_cast<int>(random()%100),float(random()%20),float(random()%10)/10,0,0};
        for(unsigned i=0;i<3;++i) {
            graph.nodes[i]={static_cast<int>(i),1+static_cast<int>(random()%8),static_cast<int>(random()%8),float(random()%30),0,0,
                static_cast<int>(random()%20),1+static_cast<int>(random()%9),float(random()%8),float(random()%15)};
            graph.arrival[i]=random()%7;graph.delivery[i]=random()%20;
            for(unsigned j=0;j<3;++j)graph.travel[i][j]=random()%8;
        }
        float reference=-std::numeric_limits<float>::infinity();
        for(int a=-1;a<3;++a)for(int b=-1;b<3;++b) {
            if(a<0&&b>=0)continue;const std::array<int,3> path{{0,a,b}};
            std::array<int,3> previous{{-1,-1,-1}};int elapsed=0,last=-1;float gems=0,loss=0;bool valid=true;
            for(const int u:path) {
                if(u<0)break;const auto& node=graph.nodes[u];const bool again=previous[u]>=0;
                if(again&&!node.renewal){valid=false;break;}
                elapsed+=last<0?graph.arrival[u]:graph.travel[last][u];
                elapsed=std::max(elapsed,std::max(node.ready,again?previous[u]+node.renewal:0));
                elapsed+=again?node.repeat_work:node.work;loss+=again?node.repeat_loss:node.loss;
                previous[u]=elapsed;last=u;gems+=node.gems;
            }
            elapsed+=graph.delivery[last]+2;
            if(!valid||elapsed>c.horizon||loss>=graph.loss_budget)continue;
            reference=std::max(reference,c.bag+gems+c.income*(c.horizon-elapsed));
        }
        q=trip::best(c,graph,0,0,bank,budget);
        assert((!q.count&&!std::isfinite(reference))||(q.count&&std::abs(macro::value(c,q.option)-reference)<.001f));
    }
    GroupBelief belief;std::vector<float> hp{10},initial{10};unsigned captures=0;
    GroupSample sample;sample.members.resize(1);sample.state=GroupState::Respawning;
    for(int round=100;round<170;++round) {
        sample.respawn_timer=std::max(0,150-round);
        captures+=conversion_observed(belief.state,sample.state);apply_group_sample(belief,hp,initial,sample,round);
    }
    assert(captures==1&&belief.ready==169); // Delayed respawn shifts ready without a second capture.
    sample.state=GroupState::Alive;sample.members[0]=10;
    captures+=conversion_observed(belief.state,sample.state);apply_group_sample(belief,hp,initial,sample,170);
    sample.state=GroupState::Respawning;captures+=conversion_observed(belief.state,sample.state);
    assert(captures==2);
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
    auto repeated=fixed;repeated.jobs={10,10,-1};repeated.ordinals={0,1,0};
    task.start(repeated,100,0,5);task.generations={4,5,0};task.advance(102,0,false,false);task.refresh_repeat(10,4);
    assert(task.job()==10&&task.generations[1]==4); // Skipping a visit cannot invent its conversion.
    fixed.shop=true;task.start(fixed,100,10,5);
    task.advance(108,20,true,true);task.advance(115,30,true,true);task.advance(120,0,false,true);
    assert(task.phase==trip::Phase::Shop);task.advance(150,0,false,true,true);assert(!task.active());
    siege::RecoveryLatch recovery;
    assert(recovery.update(true,false,300,1000));
    assert(recovery.update(false,false,300,1000)); // Leaving camp reach isn't healing.
    assert(recovery.update(false,false,1000,1000)); // A field heal doesn't prove the home leg completed.
    assert(recovery.update(false,true,999,1000));
    assert(!recovery.update(false,true,1000,1000));
    std::cout<<"2000 distinct/renewable circuit schedule references; cumulative HP, conversion generations, bank commitments and recovery passed\n";
}
