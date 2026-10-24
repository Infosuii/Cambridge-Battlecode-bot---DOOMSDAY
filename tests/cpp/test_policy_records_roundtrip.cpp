// NFS2 synthetic-only native round trip and queue/validation checks. No engine or learning.
#include "nn_policy_log.h"
#include "nn_rt.h"
#include <cstdlib>
#include <cmath>
int main(int argc,char** argv) {
    using namespace nnp_log;
    const std::uint32_t obs=argc>1?static_cast<std::uint32_t>(std::strtoul(argv[1],nullptr,0)):0x12345678u;
    const int dim=argc>2?std::atoi(argv[2]):173;
    if(dim<1||dim>1024)return 1;
    float raw[1024];for(int i=0;i<dim;++i)raw[i]=i<40?float(i%13)/13.0f:0.0f; // valid zero-padded compact observation
    Header h{obs,0xabcdef01u,7,99,1,0};
    if(argc>3 && std::strcmp(argv[3],"varied")==0) {
        std::uint32_t ids[16];std::uint8_t legal[16];float features[16*12],logits[16];
        for(int i=0;i<16;++i){ids[i]=100+i*7;legal[i]=(i%3)!=1;logits[i]=legal[i]?float((i*7)%11-5)*.7f:-INFINITY;}
        for(int i=0;i<16*12;++i)features[i]=float(i%11-5)*.05f;
        for(int head=1;head<=8;++head)for(int K=1;K<=16;++K){
            DecisionRec r;r.h=h;r.h.decision_id=10000+head*100+K;r.head=head;r.K=K;r.context=K%4;r.sampled=1;
            r.chosen=nnrt::masked_sample(logits,legal,K,float(K%7)/7.0f,&r.logp);r.selected_id=ids[r.chosen];
            r.id=ids;r.legal=legal;r.logits=logits;r.feat=features;
            if(!enqueue_decision(r)||!flush_one())return 15;
        }
        return 0;
    }
    if(!enqueue_context({h,raw,static_cast<std::uint32_t>(4*dim)}))return 2;
    std::uint32_t ids[3]={10,20,30};std::uint8_t legal[3]={1,0,1};float logits[3]={.25f,-INFINITY,1.25f};
    float feat[36];for(int i=0;i<36;++i)feat[i]=float(i)/100.0f;
    h.decision_id=42;
    DecisionRec d;d.h=h;d.head=6;d.K=3;d.chosen=2;d.selected_id=30;d.sampled=1;
    d.logp=nnrt::masked_log_prob(logits,legal,3,2);d.id=ids;d.legal=legal;d.feat=feat;d.logits=logits;d.fuel={100,200,300,400};
    if(!enqueue_decision(d))return 3;
    if(!enqueue_execution({h,30,kExecuted,kDirectPolicy,0,0,50,10}))return 4;
    d.h.decision_id=43;d.chosen=0;d.selected_id=10;d.teacher=0;d.teacher_id=10;d.sampled=0;d.logp=0;d.source=kTeacherFallback;
    if(!enqueue_decision(d))return 5;
    if(!enqueue_execution({d.h,10,kExecuted,kTeacherFallback,0,0,40,10}))return 6;
    while(!queue_empty())if(!flush_one())return 7;
    // Direct action may be index0, but no teacher0 is invented. Invalid rows are refused, not sanitised.
    d.teacher=-1;d.teacher_id=kNoAction;d.source=kDirectPolicy;d.h.decision_id=44;
    feat[0]=NAN;if(enqueue_decision(d))return 8;feat[0]=0;
    ids[1]=10;if(enqueue_decision(d))return 9;ids[1]=20;
    d.teacher=0;if(enqueue_decision(d))return 10;d.teacher=-1;
    if(g_invalid!=3)return 11;
    // Ring wraps without compaction or overflowing fixed storage.
    reset();
    for(int i=0;i<500;++i){d.h.decision_id=100+i;if(!enqueue_decision(d)||!flush_one(stderr))return 12;}
    // Queue overflow is bounded, counted and harmless.
    reset();int accepted=0;while(enqueue_decision(d)){if(++accepted>1000)return 13;}
    if(g_dropped!=1||g_bytes>kQueueBytes||accepted==0)return 14;
    std::printf("NFS2_TEST invalid=3 ring=500 overflow=1\n");
    return 0;
}
