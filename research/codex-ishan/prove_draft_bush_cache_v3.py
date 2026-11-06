"""EXP266: same frozen8smoke with compact interval runtime representation."""
from pathlib import Path
import live111_draft_bush_cache as cache
import prove_draft_bush_cache as original
from engine3_pool import HERE

prepare_v1=cache.prepare
def prepare(src,enabled,probe=False):
    prepare_v1(src,enabled,probe)
    (src/'grouped_bush_codec.h').write_bytes((HERE/'grouped_bush_codec_v3.h').read_bytes())

if __name__=='__main__':
    cache.prepare=prepare
    source=Path(original.__file__).read_text(encoding='utf8')
    source=source.replace("'draft-bush-cache-smoke-20261106'","'draft-bush-cache-smoke-v3-20261106'")
    source=source.replace("'bots/draft-bush-cache-smoke-off-20261106'","'bots/draft-bush-cache-smoke-v3-off-20261106'")
    source=source.replace("'bots/draft-bush-cache-smoke-probe-20261106'","'bots/draft-bush-cache-smoke-v3-probe-20261106'")
    source=source.replace("'DRAFT_BUSH_CACHE_SMOKE_PLAN.json'","'DRAFT_BUSH_CACHE_SMOKE_V3_PLAN.json'").replace("'DRAFT_BUSH_CACHE_SMOKE.json'","'DRAFT_BUSH_CACHE_SMOKE_V3.json'")
    source=source.replace("'draft_bush_cache_probe.inc'","'draft_bush_cache_probe_v2.inc'")
    exec(compile(source,'<EXP266 unchanged smoke driver>','exec'),{'__name__':'__main__'})
