#pragma once
#include "common.h"
inline constexpr int kClaimSlots=6,kClaimBits=7;
inline constexpr std::uint64_t kClaimMask=127,kClaimCodeDead=126;
enum class GroupState:std::uint8_t {alive,reward,respawning};
struct CampRec {vec2 pos;float hp=120,strength=8;bool dead=false;int range=2;};
struct GroupRec {
    std::uint32_t handle=0,gems=20,gold=40;std::vector<int> camps;
    float strength=8;GroupState state=GroupState::alive;int respawn_round=0,seen_round=-1;
};
struct AllyRec {vec2 pos;float hp=100,strength=20;std::uint32_t id=0;};
struct EnemyRec {vec2 pos;float hp=100,strength=30;std::uint32_t id=0,state=1;int range=2;};
struct Sighting {vec2 pos;int round;};
struct World {
    int width=64,height=64;bool no_bank=false,altar_ready=false;
    bc::bitboard visible;bc::distance_field spawn_field,altar_field;
    std::vector<vec2> spawn_tiles,altars;std::vector<CampRec> camps;std::vector<GroupRec> groups;
    std::vector<AllyRec> allies;std::vector<EnemyRec> enemies;std::vector<Sighting> sightings;
    std::vector<std::uint8_t> camp_visible;std::vector<int> distances;
    bool has_field(int gi)const{return gi>=0&&gi<static_cast<int>(distances.size())&&distances[gi]>=0;}
    int group_distance(int gi,vec2)const{return distances[gi];}
};
class Bot {
public:
    bool inited=true;float hp=50,max_hp=100,strength=30;vec2 pos{32,32};World w;
    int round=40,gems=50,gold=900,slot=0,team_size=3,ally_score=300,enemy_score=250,range=2;
    std::uint32_t my_id=1;std::uint64_t shared=~std::uint64_t{0};int target_group=-1,published=-1,claim_writes=0;
    const char* mode="";bool flip_x=false,flip_y=false;
    void write_claim(int group) {published=group;++claim_writes;shared=(shared&~(kClaimMask<<(slot*kClaimBits)))|((group<0?kClaimMask:static_cast<std::uint64_t>(group))<<(slot*kClaimBits));}
};
