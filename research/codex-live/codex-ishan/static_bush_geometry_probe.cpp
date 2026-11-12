#include <cambc.h>
#include <algorithm>
#include <cstdio>
namespace bc=cambc;
int main(){
    bool done=false;
    for(;;){
        if(!bc::is_draft())bc::resign();
        if(!done){
            const auto start=bc::fuel_remaining();
            const int w=bc::map::width(),h=bc::map::height();
            const auto& board=bc::map::bushes();
            const auto packed=board.export_linear_buffer();
            int mismatch=0;
            for(int i=0;i<w*h;++i)mismatch+=board.is_set({i%w,i/w})!=((packed[i>>3]>>(i&7))&1);
            const auto cost=start-bc::fuel_remaining();
            std::printf("STATIC_BUSH %d %d %zu %d %llu ",w,h,bc::map::camp_groups().size(),mismatch,static_cast<unsigned long long>(cost));
            for(auto b:packed)std::printf("%02x",static_cast<unsigned>(b));
            std::printf("\n");done=true;
        }
        const auto picks=bc::draft::current_draft(bc::team::ally);
        for(int i=0;i<11;++i){const auto p=static_cast<bc::champion_draft>(i);if(std::find(picks.begin(),picks.end(),p)==picks.end()){bc::draft::pick(p);break;}}
        bc::end_turn();
    }
}
