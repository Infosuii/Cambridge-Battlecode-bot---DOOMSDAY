// Lanchester combat model (agent2/lab/lanch_fit.py on lanch_arena.js forced fights, E81).
// L(side) = |side|^(n-1) * sum h * (w[type] * s + w_f * f); h = hp/1000, s = str/70, f = focus/100;
// P(we win) = sigmoid(L(us) - L(them)).
#pragma once
namespace lanch {
inline constexpr float kOrder = 1.000f;
inline constexpr float kW[13] = {0.5910f, 0.6160f, 0.3645f, 0.3898f, -0.2671f, 0.2456f, 0.2456f, 0.9425f, 0.2456f, 0.0850f, 0.5014f, 0.1200f, 0.3822f};
inline constexpr float kWf = 0.7256f;
} // namespace lanch

