#include <cambc.h>
#include <cstdio>
#include "exact_base64.h"
namespace bc=cambc;
static std::uint8_t data[4096];static char out[8193];
static void fill(int n){for(int i=0;i<n;++i)data[i]=std::uint8_t((i*73+n*17)^n);}
int main(){
    for(int n=0;n<=129;++n){fill(n);const auto len=jd_codec::base64(data,n,out,sizeof out);std::printf("ENC %d %zu %s\n",n,len,out);jd_codec::hex_simd(data,n,out,sizeof out);std::printf("HEX %d %s\n",n,out);}
    fill(257);const auto bad=jd_codec::base64(data,257,out,3);std::printf("CAPACITY_REJECT %zu\n",bad);
    for(int n:{256,640,896,1024,4096})for(int mode:{0,1,2}){
        fill(n);const auto a=bc::fuel_remaining();
        const auto len=mode==2?jd_codec::hex_simd(data,n,out,sizeof out):mode==1?jd_codec::base64(data,n,out,sizeof out):jd_codec::hex(data,n,out,sizeof out);
        const auto b=bc::fuel_remaining();
        std::printf("BYTES %d %d ",n,mode);const auto c=bc::fuel_remaining();std::fwrite(out,1,len,stdout);const auto d=bc::fuel_remaining();std::printf("\n");
        std::printf("CODEC_FUEL %d %d %zu %llu %llu\n",n,mode,len,(unsigned long long)(a-b),(unsigned long long)(c-d));
    }
    std::fflush(stdout);bc::resign();bc::end_turn();
}
