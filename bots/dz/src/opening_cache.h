#pragma once
#include "kernel.h"
#include "opening_catalog.h"
namespace dz {
#if DZ_ECONOMY_V2 && DZ_LIFECYCLE
void publish_opening_cache(const TurnContext&,Actuator&);
const opening_catalog::Catalog& opening_cache();
opening_catalog::Design camp_design(const cambc::camp&);
#endif
}
