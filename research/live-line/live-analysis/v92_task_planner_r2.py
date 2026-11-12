"""EXP291 source-prep correction: distinguish low-fuel continuation from buddy capture."""
from pathlib import Path
import v92_task_planner as original
source=Path(original.__file__).read_text(encoding='utf8')
anchor="anchor='        best = target_group;';assert selector.count(anchor)==1"
assert source.count(anchor)==1
source=source.replace(anchor,"anchor='        best = target_group;';assert selector.count(anchor)==2\n    assert selector.index(anchor)<selector.index('    // Escort')")
anchor="#endif''')\n    data=data[:start]"
assert source.count(anchor)==1
source=source.replace(anchor,"#endif''',1)\n    data=data[:start]")
namespace={}
exec(compile(source,'<EXP291 contextual source prep>','exec'),namespace)
prepare=namespace['prepare']
BASE=namespace['BASE']
REFERENCE=namespace['REFERENCE']
