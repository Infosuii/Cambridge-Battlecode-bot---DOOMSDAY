# EXP-201 result — Correct walking-cache miss on a travel-dash champion

MEASURED: LIVE109_RUNTIME_TARGET_CACHEMODE111.json matches the original rejected-cache candidate own view/action/nativeR1,off0b73e25c. Field mode has bridges_on1,36groups. Preparation beginsR1with13817andendsR2with96675:17142charged. The version1decoder explicitly rejects bridged worlds,so this call follows the original calculation as designed.

Source Bot::init bot.cpp546 calls World::enable_bridges for travel-dash champions; world.cpp364-378 builds their hole-gap travel model only where walking cuts off sufficient value. This is a champion-specific static travel model,not a timed global bridge opening. Extend coverage with separately computed/validated walking and travel-dash orders; do not remove coherence validation. EXP202 will prove both formats before a new candidate. No policy/threshold change or platform action.
