#include "common.h"
#undef NOVA_SEED
#include <algorithm>
#include <array>
#include <cambc.h>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <memory>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <tuple>
#include <variant>
#include <vector>
namespace bc=cambc;
namespace policy0 { void turn(); }
namespace policy1 { void turn(); }
namespace policy2 { void turn(); }
namespace policy3 { void turn(); }
namespace policy4 { void turn(); }
namespace policy5 { void turn(); }
namespace policy6 { void turn(); }
namespace policy7 { void turn(); }
namespace policy8 { void turn(); }
namespace policy9 { void turn(); }
namespace policy10 { void turn(); }
namespace policy11 { void turn(); }
namespace policy12 { void turn(); }
namespace policy13 { void turn(); }
namespace policy14 { void turn(); }
namespace policy15 { void turn(); }
namespace {
volatile std::int32_t policy_assignment67[126]={1295398736,827150913,14,14,0,0,15,15,10,10,6,6,4,0,1,4,3,3,10,8,13,1,9,2,4,14,11,11,14,14,10,2,15,15,0,0,7,7,15,1,15,8,13,5,2,6,15,1,6,6,3,7,3,3,1,1,14,0,5,9,7,7,2,2,8,9,2,10,5,5,4,4,3,0,13,13,15,8,0,4,14,0,2,3,7,14,2,2,13,13,13,13,12,14,9,9,6,0,7,6,12,12,10,3,1,2,9,9,12,12,3,5,13,13,7,14,0,0,3,3,15,15,5,5,5,5};
unsigned map_key() {
    namespace d=cambc::detail;
    unsigned hash=2166136261u;
    auto mix=[&](std::int64_t value) { for(int b=0;b<4;++b) { hash^=unsigned((value>>(8*b))&255); hash*=16777619u; } };
    mix(bc::map::width()); mix(bc::map::height()); mix(bc::draft::team_size());
    std::uint32_t n=0; d::check(d::sdk_map_num_camp_groups(&n));
    std::vector<std::uint32_t> groups(n); d::check(d::sdk_map_camp_groups(groups.data(),n,&n)); mix(n);
    for(auto g:groups) {
        d::camp_group_info info{}; d::check(d::sdk_map_camp_group(g,&info)); mix(info.gold); mix(info.gems);
        std::uint32_t count=0; d::check(d::sdk_map_camp_group_num_camps(g,&count));
        std::vector<std::uint32_t> camps(count); d::check(d::sdk_map_camp_group_camps(g,camps.data(),count,&count));
        for(auto c:camps) { d::camp_info spec{}; d::check(d::sdk_map_camp_info(c,&spec)); mix(spec.x); mix(spec.y); mix(spec.type); }
    }
    return hash;
}
int map_slot() {
    switch(map_key()) {
    case 3946714732u: return 0; // 00ambush: b20-tagged-team-foundation
    case 2432487045u: return 1; // 00anvil: b00-baseline
    case 3951348820u: return 2; // 00breadcrumbs: b21-tagged-team-coordination
    case 752574586u: return 3; // 00contest: b15-winning-drafts
    case 352347942u: return 4; // 00corners: b07-no-verdict-search
    case 3769348314u: return 5; // 00crater: b04b-fish-meta
    case 156657146u: return 6; // 00dunes: b04b-fish-meta
    case 1227465213u: return 7; // 00eight: b03-economy-director
    case 760217622u: return 8; // 00elkring: b15-winning-drafts
    case 1869183256u: return 9; // 00expanse: b18-public-camp-state
    case 247370468u: return 10; // 00fragment: b03-economy-director
    case 3808139108u: return 11; // 00galaxy: b20-tagged-team-foundation
    case 736261966u: return 12; // 00gem_fields: b16-winning-draft-items
    case 4293445000u: return 13; // 00gemfight: b20-tagged-team-foundation
    case 2071628198u: return 14; // 00great_wall: b02-team-commander
    case 2279101519u: return 15; // 00interlock: b21-tagged-team-coordination
    case 2568633718u: return 16; // 00lanes: b00-baseline
    case 1513540318u: return 17; // 00lost_world: b09-original-item-path
    case 1438067448u: return 18; // 00monolith: b06-life15
    case 789333002u: return 19; // 00packs: b10-melee-micro
    case 1526899011u: return 20; // 00pilgrimage: b06-life15
    case 541459588u: return 21; // 00quadrants: b09-original-item-path
    case 4013728213u: return 22; // 00quarry: b01-early-stats
    case 3584668244u: return 23; // 00ribs: b07-no-verdict-search
    case 2190253359u: return 24; // 00road_of_riches: b09-original-item-path
    case 2429361955u: return 25; // 00rows: b03-economy-director
    case 4052046845u: return 26; // 00rushbait_v2: b01-early-stats
    case 2484340562u: return 27; // 00split: b00-baseline
    case 4118712869u: return 28; // 00stampede: b14-winning-map-openings
    case 2983936086u: return 29; // 00the_line: b09-original-item-path
    case 4015712130u: return 30; // 00vault: b02-team-commander
    case 2963879676u: return 31; // 01big_world: b10-melee-micro
    case 334055938u: return 32; // 01boss_battle: b10-melee-micro
    case 1592866404u: return 33; // 01broken_curve: b06-life15
    case 2394020334u: return 34; // 01concentrated_wealth: b04b-fish-meta
    case 2144244621u: return 35; // 01corridors: b10-melee-micro
    case 3911038845u: return 36; // 01elk_arena: b18-public-camp-state
    case 3625767524u: return 37; // 01fracture: b10-melee-micro
    case 903771983u: return 38; // 01hooks: b20-tagged-team-foundation
    case 612904990u: return 39; // 01islands: b00-baseline
    case 318986457u: return 40; // 01shortcut: b02-team-commander
    case 3372478764u: return 41; // 01starfish: b20-tagged-team-foundation
    case 2353507673u: return 42; // 01starvation: b02-team-commander
    case 1486679388u: return 43; // 01the_farm: b18-public-camp-state
    case 234851042u: return 44; // 01yellow_brick_road: b18-public-camp-state
    case 369071736u: return 45; // 02arena: b20-tagged-team-foundation
    case 2187926992u: return 46; // 02crossing: b14-winning-map-openings
    case 3445152952u: return 47; // 02famine: b07-no-verdict-search
    case 1522475090u: return 48; // 02fields: b07-no-verdict-search
    case 1091255700u: return 49; // 02geodes: b17-winning-draft-routes
    case 9504743u: return 50; // 02guardians: b03-economy-director
    case 920209248u: return 51; // 02harvest: b01-early-stats
    case 888456886u: return 52; // 02stalactites: b14-winning-map-openings
    case 1356165252u: return 53; // 02tangle: b17-winning-draft-routes
    case 591539490u: return 54; // 02the_pond: b10-melee-micro
    case 749528931u: return 55; // 02treasure_box: b18-public-camp-state
    case 1773397848u: return 56; // 02uncharted_lands: b09-original-item-path
    case 686393692u: return 57; // adgato_gemcombat1: b00-baseline
    case 3108422669u: return 58; // adgato_gemcombat3: b03-economy-director
    case 1334727042u: return 59; // adgato_gemcombat4: b21-tagged-team-coordination
    case 2918384253u: return 60; // adgato_gemcombat5: b06-life15
    default: return 61;
    }
}
int choose() { return policy_assignment67[map_slot()*2+cambc::detail::cached_my_team+2]; }
}
int main() {
    int selected=-1;
    while(true) {
        try {
            if(selected<0) selected=choose();
            switch(selected) {
            case 0: policy0::turn(); break;
            case 1: policy1::turn(); break;
            case 2: policy2::turn(); break;
            case 3: policy3::turn(); break;
            case 4: policy4::turn(); break;
            case 5: policy5::turn(); break;
            case 6: policy6::turn(); break;
            case 7: policy7::turn(); break;
            case 8: policy8::turn(); break;
            case 9: policy9::turn(); break;
            case 10: policy10::turn(); break;
            case 11: policy11::turn(); break;
            case 12: policy12::turn(); break;
            case 13: policy13::turn(); break;
            case 14: policy14::turn(); break;
            case 15: policy15::turn(); break;
            }
        } catch(const std::exception& e) { std::printf("bot error: %s\n",e.what()); }
        catch(...) { std::printf("bot error: unknown exception\n"); }
        bc::end_turn();
    }
}
