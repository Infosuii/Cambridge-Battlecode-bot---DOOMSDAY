"""Port cl_patches' `table` (CL_NEWMAP_TABLE) and `goldtrip_all` (CL_GOLDTRIP) to v130's stripped source.
The table code is cl_patches.newmap_table's, inserted at v130's equivalent anchor (the #endif lines v113 had there are
gone); the gold trip's anchors are unchanged in v130, so cl_patches.goldtrip runs as is.
usage: port_v130.py REPO SRC table|goldtrip_all ..."""
import os, shutil, sys

repo, src = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(repo, "tools", "rl_env_1104"))
import cl_patches as cp

TABLE_CODE = """#if CL_NEWMAP_TABLE
        if (!ladder_known)
            for (const auto& row : cl_newmap::kRows)
                if (row.w == w.width && row.h == w.height && row.groups == n_groups && row.gems == total_gems) {
                    for (int i = 0; i < 48; ++i) lab::knobs[i] += cl_newmap::kDelta[row.profile][i];
                    break;
                }
#endif
"""
ANCHOR = "                break;\n            }\n        }\n    }\n    {\n        // Engine-lab joint search"


def table(s):
    shutil.copy(cp.TABLE_G3, os.path.join(s, "cl_newmap_table.h"))
    cp.patch(s, "common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_NEWMAP_TABLE 1\n")
    cp.patch(s, "bot.cpp", '#include "a2map.h"\n', '#include "a2map.h"\n#if CL_NEWMAP_TABLE\n#include "cl_newmap_table.h"\n#endif\n')
    cp.patch(s, "bot.cpp", ANCHOR, ANCHOR.replace("        }\n    }\n    {", "        }\n" + TABLE_CODE + "    }\n    {", 1))


for name in sys.argv[3:]:
    {"table": table, "goldtrip_all": lambda s: cp.goldtrip(s, until=100000)}[name](src)
    print("applied", name)
