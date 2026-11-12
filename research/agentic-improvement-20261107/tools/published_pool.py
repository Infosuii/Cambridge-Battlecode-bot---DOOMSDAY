"""Only current catalog IDs with verified official bytes count as published maps."""
from pathlib import Path
import hashlib

def canonical(name):return name.lower().replace('-','_')
def verified_pool(local_folder, official_folder, catalog):
    catalog_by_name={canonical(row['name']):row for row in catalog}
    assert len(catalog_by_name)==len(catalog)==len({r['mapId'] for r in catalog})
    official={}
    for p in Path(official_folder).glob('*.map26a'):
        key=canonical(p.stem)
        if key not in catalog_by_name: continue
        assert key not in official, 'Duplicate official filename alias'
        official[key]=hashlib.sha256(p.read_bytes()).hexdigest()
    assert set(official)==set(catalog_by_name), 'Official downloaded pool is incomplete'
    result=[];seen=set()
    for p in sorted(Path(local_folder).glob('*.map26a')):
        key=canonical(p.stem)
        if key not in official:continue
        digest=hashlib.sha256(p.read_bytes()).hexdigest()
        assert digest==official[key], 'Local file differs from current official bytes: '+str(p)
        assert key not in seen, 'Duplicate local alias for one official map'
        seen.add(key)
        result.append({'file':str(p),'sha256':digest,**catalog_by_name[key]})
    return result
