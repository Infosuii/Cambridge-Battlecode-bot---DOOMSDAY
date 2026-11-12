// GENERATED compact direct-policy observation. Pure, SDK-free, no initializers.
#pragma once
#include <cmath>
#include <cstdint>
class Bot;
namespace nnpobs {
inline constexpr std::uint32_t kObsSchemaHash = 0x1346E3BAu;
inline constexpr int kSelfGlobalDim = 40;
inline constexpr int kAllyRows = 5;
inline constexpr int kAllyDim = 10;
inline constexpr int kEnemyRows = 6;
inline constexpr int kEnemyDim = 12;
inline constexpr int kObsDim=173;
inline constexpr float kSelfScale[40]={1.0f, 1000.0f, 1000.0f, 100.0f, 1000.0f, 100.0f, 100.0f, 10.0f, 2000.0f, 2000.0f, 1000.0f, 1000.0f, 4.0f, 32.0f, 32.0f, 50.0f, 20.0f, 20.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 32.0f, 32.0f, 100.0f, 1.0f, 1.0f, 6.0f, 6.0f, 100.0f, 100.0f, 11.0f, 7.0f, 7.0f, 1.0f, 10.0f, 20.0f, 1.0f};
inline constexpr float kAllyScale[10]={32.0f, 32.0f, 1.0f, 1000.0f, 100.0f, 100.0f, 10.0f, 11.0f, 100.0f, 127.0f};
inline constexpr float kEnemyScale[12]={32.0f, 32.0f, 1.0f, 1000.0f, 100.0f, 100.0f, 10.0f, 11.0f, 100.0f, 1.0f, 1.0f, 32.0f};
struct Raw { float self[40]{},ally[5][10]{},enemy[6][12]{}; std::uint8_t ally_mask[5]{},enemy_mask[6]{}; };
inline bool scalar(float raw,float scale,float& out) {
    if(!std::isfinite(raw))return false;
    out=raw/scale;out=out<-4?-4:out>4?4:out;return true;
}
inline bool encode(const Raw& r,float* out) {
    for(int j=0;j<173;++j)out[j]=0;
    for(int j=0;j<40;++j)if(!scalar(r.self[j],kSelfScale[j],out[j]))return false;
    for(int i=0;i<5;++i){if(r.ally_mask[i]>1)return false;if(!r.ally_mask[i])continue;
        out[90+i]=1;for(int j=0;j<10;++j)if(!scalar(r.ally[i][j],kAllyScale[j],out[40+i*10+j]))return false;}
    for(int i=0;i<6;++i){if(r.enemy_mask[i]>1)return false;if(!r.enemy_mask[i])continue;
        out[167+i]=1;for(int j=0;j<12;++j)if(!scalar(r.enemy[i][j],kEnemyScale[j],out[95+i*12+j]))return false;}
    return true;
}
bool capture(const Bot&,float* out);
}
