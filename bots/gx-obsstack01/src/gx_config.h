#pragma once

#ifndef GX_FIELD_GUARD
#define GX_FIELD_GUARD 0  // 1: reserve for field ordering; 2: also restrict first-turn builds.
#endif

#ifndef GX_SEEN_CAMPS
#define GX_SEEN_CAMPS 0  // 1: skip hidden member queries; 2: audit the visibility boundary.
#endif

#ifndef GX_MAP_CACHE
#define GX_MAP_CACHE 0  // 1: draft-built camp catalog; 2: compare cached and native observations.
#endif
