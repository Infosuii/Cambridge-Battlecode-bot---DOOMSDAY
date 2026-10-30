"""Describe frozen opponent owner-turn observations; never infer live intent."""
import json
from pathlib import Path
import statistics


def summarize(turns):
    result={}
    for kind in (10,12):
        rows=[r for r in turns if r['type']==kind]
        shield=[(r,c) for r in rows for c in r['casts'] if c['kind']==7]
        reset=[c for r in rows for c in r['casts'] if c['kind']==1]
        fractions=[c['hp_fraction'] for _,c in shield]
        increase=lambda r,c:c['hp']>r['start']['hp']+.03 or c['max_hp']>r['start']['max_hp']+.03
        competing=[r for r in rows if kind==10 and r['start']['ready_by_start_fields']
                   and r['start']['hp_fraction']<.85 and r['start']['cooldowns'][0]==0
                   and r['basics'] and r['basics'][0]['target_alive_after'] is True]
        chosen=sum(bool(r['casts']) and r['casts'][0]['kind']==7 for r in competing)
        result[str(kind)]=dict(turns=len(rows),basics=sum(len(r['basics']) for r in rows),
            shield_casts=len(shield),shield_before_basic=sum(c['basics_before']==0 for _,c in shield),
            shield_before_basic_fraction=sum(c['basics_before']==0 for _,c in shield)/len(shield) if shield else None,
            reset_casts=len(reset),reset_after_basic=sum(c['basics_before']>0 for c in reset),
            reset_after_basic_fraction=sum(c['basics_before']>0 for c in reset)/len(reset) if reset else None,
            dash_casts=sum(c['kind']==6 for r in rows for c in r['casts']),
            shield_hp_fraction=dict(min=min(fractions) if fractions else None,median=statistics.median(fractions) if fractions else None,
                                    max=max(fractions) if fractions else None),
            shield_at_or_above_85=sum(c['hp_fraction']>=.85 for _,c in shield),
            shield_above_85_without_turn_increase=sum(c['hp_fraction']>=.85 and not increase(r,c) for r,c in shield),
            competing_ready_combat_turns=len(competing),competing_shield_first=chosen,
            competing_shield_first_fraction=chosen/len(competing) if competing else None)
    return result


def load_manifest(folder,filename):
    folder=Path(folder);manifest=json.loads((folder/filename).read_text(encoding='utf-8'))
    return [r for cell in manifest['cells'] for r in json.loads((folder/cell['file']).read_text(encoding='utf-8'))['turns']]
