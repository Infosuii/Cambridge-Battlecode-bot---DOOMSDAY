#pragma once
#include "common.h"
#include "gx_config.h"
#if GX_CONTACT_MODEL
#include "lanch_model.h"
namespace gx_contact {
inline volatile unsigned action = 1000u + GX_CONTACT_ARM;

inline float power(bc::champion_type t, float health, float strength, float focus) {
    const auto i = std::clamp(static_cast<int>(t),0,12);
    return health / 1000.0f * (lanch::kW[i] * strength / 70.0f + lanch::kWf * focus / 100.0f);
}

// Logistic score fitted to short-horizon individual casualty risk. The
// training threshold is the 95th percentile of training contact scores.
inline bool alert(float health, float z, int foe, int allies, int distance, int bag) {
    const float risk = -0.69701254f - 3.11973678f * health - 0.13960588f * z +
        0.21758631f * foe - 0.06028573f * allies - 0.26713547f * distance +
        0.07492093f * (std::min(bag,120) / 60.0f);
    return risk >= -1.81878473f;
}
} // namespace gx_contact
#endif
