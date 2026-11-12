"""EXP285 same fixed controls, corrected champion-instance setup, fresh paths."""
from pathlib import Path
import prove_varg_wrapper as original
if __name__=='__main__':
    source=Path(original.__file__).read_text(encoding='utf8')
    source=source.replace('varg-wrapper-proof-20261106','varg-wrapper-proof-r2-20261106').replace('VARG_WRAPPER_PROOF','VARG_WRAPPER_PROOF_R2').replace('varg_wrapper_probe.cpp','varg_wrapper_probe_r2.cpp')
    exec(compile(source,'<EXP285 wrapper corrected setup>','exec'),{'__name__':'__main__'})
