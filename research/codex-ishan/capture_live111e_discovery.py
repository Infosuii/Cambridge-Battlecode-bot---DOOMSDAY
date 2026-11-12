"""EXP270: reuse exact capture/profile definitions in the new E namespace."""
from pathlib import Path
import capture_live111d_discovery as original
if __name__=='__main__':
    source=Path(original.__file__).read_text(encoding='utf8').replace('freeze_live111d_discovery','live111e_context')
    exec(compile(source,'<EXP270 capture and profiles>','exec'),{'__name__':'__main__'})
