// Synthetic direct-policy model parity and descriptor refusal checks. No SDK or match execution.
#include "nn_policy_weights_synthetic_v2.h"
#include <iostream>
#include <string>
#include <vector>
#include <limits>
#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#endif

int main(int argc,char** argv) {
    using namespace nnpw_synthetic_v2;
    if (argc>1 && std::string(argv[1])=="checks") {
        int passed=0,failed=0;
        auto check=[&](bool ok){ if(ok) ++passed; else ++failed; };
        check(nnpm::desc_ok(kDesc)); check(nnpm::verify(kDesc));
        check(nnpm::desc_ok(kDesc,kKernel.obs_schema_hash,kKernel.action_schema_hash));
        std::uint32_t hashes[13]={}; for(int i=1;i<=8;++i) hashes[i]=kKernel.head[i].action_hash;
        check(nnpm::desc_ok(kDesc,kKernel.obs_schema_hash,kKernel.action_schema_hash,hashes));
        hashes[6]^=1; check(!nnpm::desc_ok(kDesc,kKernel.obs_schema_hash,kKernel.action_schema_hash,hashes));
        check(!nnpm::desc_ok(kDesc,kKernel.obs_schema_hash^1u,kKernel.action_schema_hash));
        auto p=kDesc; p.interpretation_version=1; check(!nnpm::desc_ok(p));
        auto m=kKernel; p={2,&m}; m.arch_version=2; check(!nnpm::desc_ok(p));
        m=kKernel; m.head[1].F=24; check(!nnpm::desc_ok(p));
        m=kKernel; m.head[1].R=2; check(!nnpm::desc_ok(p));
        m=kKernel; m.head[1].action_hash=0; check(!nnpm::desc_ok(p));
        m=kKernel; m.action_schema_hash=0; check(!nnpm::desc_ok(p));
        m=kKernel; m.head[0]=m.head[1]; check(!nnpm::desc_ok(p));
        m=kKernel; m.checksum^=1; check(!nnpm::verify(p));
        m=kKernel; m.head[1].seg.checksum^=1; check(!nnpm::verify(p));
        m=kKernel; m.head[1].wf=m.head[2].wf; check(!nnpm::desc_ok(p));
        m=kKernel; m.head[1].wf=0xffffffffu-4; check(!nnpm::desc_ok(p));
        std::vector<float> bad(kBlob,kBlob+kKernel.n_params); bad[0]=std::numeric_limits<float>::quiet_NaN();
        m=kKernel; m.blob=bad.data(); check(!nnpm::verify(p));
        float h[nnm::kMaxCtx]={},f[16*12]={},out[16]; std::uint8_t legal[16]={1,1};
        check(nnpm::logits(kDesc,1,0,h,f,2,legal,out));
        check(!nnpm::logits(kDesc,0,0,h,f,2,legal,out));
        check(!nnpm::logits(kDesc,1,4,h,f,2,legal,out));
        check(!nnpm::logits(kDesc,1,0,h,f,0,legal,out));
        legal[0]=legal[1]=0; check(!nnpm::logits(kDesc,1,0,h,f,2,legal,out));
        legal[0]=1; f[0]=std::numeric_limits<float>::infinity(); check(!nnpm::logits(kDesc,1,0,h,f,2,legal,out));
        std::cout<<passed<<" checks, "<<failed<<" failures\n";
        return failed ? 1:0;
    }
#ifdef _WIN32
    _setmode(_fileno(stdin),_O_BINARY); _setmode(_fileno(stdout),_O_BINARY);
#endif
    struct Input {std::uint32_t head,context,K;}; Input in;
    while(std::cin.read(reinterpret_cast<char*>(&in),sizeof(in))) {
        if(in.K>16) return 2;
        std::vector<float> obs(nnm::obs_dim(kKernel)),feat(in.K*12);
        std::vector<std::uint8_t> legal(in.K);
        std::cin.read(reinterpret_cast<char*>(obs.data()),obs.size()*4);
        std::cin.read(reinterpret_cast<char*>(feat.data()),feat.size()*4);
        std::cin.read(reinterpret_cast<char*>(legal.data()),legal.size());
        if(!std::cin) return 3;
        float h[nnm::kMaxCtx],out[16]; nnm::Scratch scratch;
        nnm::encode(kKernel,obs.data(),h,scratch);
        const std::uint32_t ok=nnpm::logits(kDesc,in.head,in.context,h,feat.data(),in.K,legal.data(),out);
        std::cout.write(reinterpret_cast<const char*>(&ok),4);
        std::cout.write(reinterpret_cast<const char*>(h),kKernel.ctx*4);
        if(ok) std::cout.write(reinterpret_cast<const char*>(out),in.K*4);
    }
}
