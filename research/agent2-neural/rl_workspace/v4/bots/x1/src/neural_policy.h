#pragma once
#include <cstdint>
namespace ngp {
bool training();
float residual(const float* features);
float uniform(int slot);
void trace(std::uint32_t champion, int round, int n, int pick, float logp, const float* obs);
void map_trace(const float* features);
}
