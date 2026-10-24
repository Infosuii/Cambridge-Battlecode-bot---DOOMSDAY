"""Entry point for the offline data/training pipeline: python tools/nfs.py <command> ... (see python/nfs/cli.py).

Name-clash guard: other scripts in tools/ (e.g. install_models.py) run with tools/ as sys.path[0], so `import nfs`
would find THIS file before the real package in python/nfs. When imported as a module this shim therefore loads the
real package and replaces itself in sys.modules (the import system returns the replaced entry).
"""
import importlib
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
_PY = str(_TOOLS.parent / 'python')


def _real_package():
    saved = list(sys.path)
    try:
        sys.path[:] = [_PY] + [p for p in saved if Path(p or '.').resolve() != _TOOLS]
        if sys.modules.get('nfs') is not None and getattr(sys.modules['nfs'], '__file__', '') == __file__:
            del sys.modules['nfs']
        return importlib.import_module('nfs')
    finally:
        sys.path[:] = saved if _PY in saved else [_PY] + saved


if __name__ == '__main__':
    _real_package()
    from nfs.cli import main
    sys.exit(main())
else:
    sys.modules[__name__] = _real_package()
