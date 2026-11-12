"""EXP290 same fixed corpus/metrics, comparable endpoint, new paths only."""
from pathlib import Path
import census_live111e_occupation as original
if __name__=='__main__':
    source=Path(original.__file__).read_text(encoding='utf8').replace('reward_occupation_episodes.mjs','reward_occupation_episodes_r2.mjs')
    source=source.replace('LIVE111E_OCCUPATION_','LIVE111E_OCCUPATION_R2_').replace('live111e-occupation-20261106','live111e-occupation-r2-20261106')
    exec(compile(source,'<EXP290 comparable endpoint census>','exec'),{'__name__':'__main__'})
