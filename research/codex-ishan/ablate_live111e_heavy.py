"""EXP271: all90dev families and fresh noise, unchanged frozen heavy arms."""
from pathlib import Path
import ablate_live111d_heavy as original

if __name__=='__main__':
    source=Path(original.__file__).read_text(encoding='utf8')
    source=source.replace('live111d-heavy','live111e-heavy').replace('LIVE111D','LIVE111E').replace('EXP238','EXP271')
    old='SEEDS = (77171, 80309)';assert source.count(old)==1;source=source.replace(old,'SEEDS = (88729, 91367)')
    first=source.index("    old = read(HERE/'LIVE111_HEAVY_PLAN.json')")
    last=source.index('    assert maps and all(',first)
    source=source[:first]+"    maps=sorted(partition('dev'),key=lambda p:bench.digest(p))\n    assert len(maps)==90\n"+source[last:]
    exec(compile(source,'<EXP271 broad heavy Discovery>','exec'),{'__name__':'__main__'})
