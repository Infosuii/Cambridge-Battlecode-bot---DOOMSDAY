"""EXP270: unchanged native clear/capture attribution in the E namespace."""
from pathlib import Path
import attribute_live111d_camps as original
if __name__=='__main__':
    source=Path(original.__file__).read_text(encoding='utf8').replace('freeze_live111d_discovery','live111e_context')
    exec(compile(source,'<EXP270 clear and capture attribution>','exec'),{'__name__':'__main__'})
