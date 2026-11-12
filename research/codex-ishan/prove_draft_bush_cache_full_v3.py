"""EXP267: unchanged full same-game controls with the interval representation."""
from pathlib import Path
import prove_draft_bush_cache_full_v2 as original

if __name__=='__main__':
    source=Path(original.__file__).read_text(encoding='utf8').replace('v2','v3').replace('V2','V3')
    exec(compile(source,'<EXP267 full interval cache>','exec'),{'__name__':'__main__'})
