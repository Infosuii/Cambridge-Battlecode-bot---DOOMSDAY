"""EXP267: target first cache lookup after a normal charged turn boundary."""
from pathlib import Path
import live111_draft_bush_cache as cache
from prove_draft_bush_cache_v3 import prepare
import prove_draft_bush_cache as original

if __name__=='__main__':
    cache.prepare=prepare
    source=Path(original.__file__).read_text(encoding='utf8')
    source=source.replace("'draft-bush-cache-smoke-20261106'","'draft-bush-cache-steady-v3-20261106'")
    source=source.replace("'bots/draft-bush-cache-smoke-off-20261106'","'bots/draft-bush-cache-steady-v3-off-20261106'")
    source=source.replace("'bots/draft-bush-cache-smoke-probe-20261106'","'bots/draft-bush-cache-steady-v3-probe-20261106'")
    source=source.replace("'DRAFT_BUSH_CACHE_SMOKE_PLAN.json'","'DRAFT_BUSH_CACHE_STEADY_V3_PLAN.json'").replace("'DRAFT_BUSH_CACHE_SMOKE.json'","'DRAFT_BUSH_CACHE_STEADY_V3.json'")
    source=source.replace("'draft_bush_cache_probe.inc'","'draft_bush_cache_probe_steady_v3.inc'")
    exec(compile(source,'<EXP267 steady100k cache>','exec'),{'__name__':'__main__'})
