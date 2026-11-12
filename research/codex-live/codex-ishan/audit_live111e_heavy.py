"""EXP271: original native outcome/safety/stratum recount on the E dataset."""
from pathlib import Path
import audit_live111d_heavy as original
if __name__=='__main__':
    source=Path(original.__file__).read_text(encoding='utf8').replace('live111d-heavy','live111e-heavy').replace('LIVE111D','LIVE111E').replace('EXP238','EXP271')
    exec(compile(source,'<EXP271 raw heavy recount>','exec'),{'__name__':'__main__'})
