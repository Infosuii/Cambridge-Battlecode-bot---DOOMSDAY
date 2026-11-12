"""EXP272: original profiler with exact native death cutoffs; preserve raw snapshots."""
from pathlib import Path
import profile_engine3_replays as original

if __name__=='__main__':
    source=Path(original.__file__).read_text(encoding='utf8')
    source=source.replace('from freeze_engine3_discovery import OUT, write','from freeze_engine3_discovery import OUT, write\nfrom native_round_deaths import correlate')
    old='            dead = [d for d in deaths[mid] if d["team"] == team]';assert source.count(old)==1
    source=source.replace(old,'            dead, alignment = correlate(deaths[mid],native,team,600)\n            rec.setdefault("death_native_alignment",{})[name]=alignment')
    source=source.replace('"native_death_counts_match": True,','"native_death_counts_match": True, "exact_native_cutoff_correlated":True,')
    exec(compile(source,'<EXP272 native-round replay profile>','exec'),{'__name__':'__main__'})
