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
namespace policy9 {
#include "policies/p9/bot.h"
#include "policies/p9/draft.h"
void turn() {
    static Bot bot;
    if(bc::is_draft()) {
        play_draft();
#if V58_DIRECTOR
        economy_record_roster();
#endif
    } else bot.play_turn();
}
}
