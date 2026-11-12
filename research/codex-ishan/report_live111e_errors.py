"""EXP270: preserve the frozen definitions and descriptive units, new data only."""
from pathlib import Path
import report_live111d_errors as original
if __name__=='__main__':
    source=Path(original.__file__).read_text(encoding='utf8').replace('LIVE111D','LIVE111E')
    exec(compile(source,'<EXP270 descriptive error table>','exec'),{'__name__':'__main__'})
