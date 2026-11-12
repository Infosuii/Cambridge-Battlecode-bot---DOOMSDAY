"""EXP270: same frozen Discovery definitions, new post-D cells and fresh output."""
from pathlib import Path
import freeze_live111d_discovery as original

if __name__=='__main__':
    source=Path(original.__file__).read_text(encoding='utf8')
    source=source.replace('live111d-discovery-20261106','live111e-discovery-20261106').replace("PREFIX='LIVE111D'","PREFIX='LIVE111E'")
    source=source.replace('LIVE111C_DISCOVERY_SPLIT.json','LIVE111D_DISCOVERY_SPLIT.json')
    old="('LIVE111_DISCOVERY_SPLIT.json','LIVE111B_DISCOVERY_SPLIT.json')"
    assert source.count(old)==1
    source=source.replace(old,"('LIVE111_DISCOVERY_SPLIT.json','LIVE111B_DISCOVERY_SPLIT.json','LIVE111C_DISCOVERY_SPLIT.json')")
    source=source.replace('EXP237','EXP270')
    exec(compile(source,'<EXP270 fresh post-D Discovery>','exec'),{'__name__':'__main__'})
