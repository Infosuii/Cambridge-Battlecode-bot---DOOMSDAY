"""EXP270: unchanged exact native resource ledger in the E namespace."""
from pathlib import Path
import resource_live111d_discovery as original
if __name__=='__main__':
    source=Path(original.__file__).read_text(encoding='utf8').replace('freeze_live111d_discovery','live111e_context')
    exec(compile(source,'<EXP270 resource ledger>','exec'),{'__name__':'__main__'})
