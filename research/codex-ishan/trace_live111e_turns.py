"""EXP270: fixed discovery own-view selection, including unavailable rosters."""
from pathlib import Path
import trace_live111d_turns_r2 as original
if __name__=='__main__':
    source=Path(original.__file__).read_text(encoding='utf8').replace('freeze_live111d_discovery','live111e_context').replace('EXP239','EXP270')
    exec(compile(source,'<EXP270 own-view turning points>','exec'),{'__name__':'__main__'})
