#pragma once
#include "common.h"
#include "v67_tables.h"
#include "map_plans.h"
namespace v67meta {
const proxy::Team& selected();
bool draft(std::uint32_t size);
const plan67::Plan* opening();
}
