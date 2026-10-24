"""Generate the compact, legal direct-policy observation contract. No model fitting."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SELF=list(zip('hp_fraction hp max_hp gems gold strength focus attack_range round remaining_rounds ally_score enemy_score role goal_dx goal_dy spawn_distance cooldown0 cooldown1 spell0_present spell1_present alive can_move can_attack can_cast sight_dx sight_dy sight_age in_bush on_own_spawn near_allies near_enemies map_width map_height champion_type ability0_kind ability1_kind in_hot_zone ward_charges ward_cooldown reserved_zero'.split(),
 [1,1000,1000,100,1000,100,100,10,2000,2000,1000,1000,4,32,32,50,20,20,1,1,1,1,1,1,32,32,100,1,1,6,6,100,100,11,7,7,1,10,20,1]))
ALLY=list(zip('dx dy hp_fraction hp strength focus attack_range champion_type carried_gems shared_claim_code'.split(),[32,32,1,1000,100,100,10,11,100,127]))
ENEMY=list(zip('dx dy hp_fraction hp strength focus attack_range champion_type carried_gems recalling submitting distance'.split(),[32,32,1,1000,100,100,10,11,100,1,1,32]))
def main():
    schema=dict(name='nfs.compact_policy_observation',version=2,normalization='float32(raw/scale), clipped[-4,4]; masked rows zero; nonfinite valid fields reject',
                layout='self40,ally5x10,ally_mask5,enemy6x12,enemy_mask6',obs_dim=173,
                self=[dict(name=n,scale=s) for n,s in SELF],ally=[dict(name=n,scale=s) for n,s in ALLY],
                enemy=[dict(name=n,scale=s) for n,s in ENEMY],
                visibility='Self/public map and scores, own shared claims, current visible bodies, own remembered sighting with age. No hidden enemy fields or future targets.',
                coordinate_frame='nnobs canonical team frame; all dx/dy mirrored to own perspective',
                row_order='Visible alive bodies only; nearest Chebyshev distance to self then ascending global champion handle; exclude self; at most5 allies and6 enemies.',
                semantics='near_allies/enemies count current visible alive bodies at distance<=8. Goal is current direct-policy option goal or self when absent; role is current direct-policy role (initial farmer0). Sighting is newest own remembered enemy sighting, tie lowest canonical coordinate, absent dx/dy0 age10000. Shared claim is raw7bit own-team code; absent127. Unknown spawn distance10000. reserved_zero always0.',
                payload='173 normalized little-endian f32 values; no legacy RawTurn; NFS2 header supplies schema identity')
    raw=json.dumps(schema,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
    h=2166136261
    for b in raw:h=((h^b)*16777619)&0xffffffff
    schema['obs_schema_hash']=h
    (ROOT/'schemas/policy_observation_v2.json').write_text(json.dumps(schema,indent=2)+'\n',encoding='utf-8',newline='\n')
    scales=lambda rows:', '.join(str(s)+'.0f' for _,s in rows)
    header='''// GENERATED compact direct-policy observation. Pure, SDK-free, no initializers.
#pragma once
#include <cmath>
#include <cstdint>
class Bot;
namespace nnpobs {
inline constexpr std::uint32_t kObsSchemaHash = HASHu;
inline constexpr int kSelfGlobalDim=40,kAllyRows=5,kAllyDim=10,kEnemyRows=6,kEnemyDim=12;
inline constexpr int kObsDim=173;
inline constexpr float kSelfScale[40]={SELF};
inline constexpr float kAllyScale[10]={ALLY};
inline constexpr float kEnemyScale[12]={ENEMY};
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
'''.replace('HASH',f'0x{h:08X}').replace('SELF',scales(SELF)).replace('ALLY',scales(ALLY)).replace('ENEMY',scales(ENEMY))
    # Literal constants are kept on distinct declarations for the existing schema parser.
    header=header.replace('inline constexpr int kSelfGlobalDim=40,kAllyRows=5,kAllyDim=10,kEnemyRows=6,kEnemyDim=12;',
                          '\n'.join(f'inline constexpr int {n} = {v};' for n,v in [('kSelfGlobalDim',40),('kAllyRows',5),('kAllyDim',10),('kEnemyRows',6),('kEnemyDim',12)]))
    (ROOT/'bot/src/nn_policy_observation.h').write_text(header,encoding='utf-8',newline='\n')
    print(f'compact observation:173 floats, schema0x{h:08x}')
if __name__=='__main__':main()
