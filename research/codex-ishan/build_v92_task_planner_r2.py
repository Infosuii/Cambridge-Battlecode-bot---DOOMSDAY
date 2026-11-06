"""EXP291 same unplayed prototype, contextual source conversion/fresh build paths."""
from pathlib import Path
import build_v92_task_planner as original
if __name__=='__main__':
    source=Path(original.__file__).read_text(encoding='utf8')
    source=source.replace('from v92_task_planner import','from v92_task_planner_r2 import').replace('codex-task-planner-','codex-task-planner-r2-')
    source=source.replace('V92_TASK_PLANNER_','V92_TASK_PLANNER_R2_')
    source=source.replace("'recipe':bench.digest(HERE/'v92_task_planner.py')","'recipe':bench.digest(HERE/'v92_task_planner_r2.py'),'original_recipe':bench.digest(HERE/'v92_task_planner.py')")
    exec(compile(source,'<EXP291 corrected contextual builds>','exec'),{'__name__':'__main__'})
