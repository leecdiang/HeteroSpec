"""Resolve the deployed runtime from the entry file, never cwd or PYTHONPATH."""
import importlib
import json
from pathlib import Path
import sys

DEPENDENCIES={
 'observe.py':{'observer_policy':'source','job_census':'source'},
 'outer_watchdog.py':{'source_guard':'source'},
 'stall_supervisor.py':{},
 'stall_harness.py':{'verify':'src/rev2'},
}
def expected_modules(root,entry):
    locations={n:'src/rev2' for n in ('win','guards','history')}
    locations.update(DEPENDENCIES[Path(entry).name])
    return {n:(root/d/(n+'.py')).resolve() for n,d in locations.items()}

def bootstrap(entry):
    root = Path(entry).resolve().parents[1]
    runtime = root / 'src/rev2'
    if not runtime.is_dir():
        raise RuntimeError('DEPLOYED_RUNTIME_MISSING')
    # -I removes the script directory too; callers explicitly install source first.
    sys.path.insert(0, str(runtime))
    modules = {}
    for name,expected in expected_modules(root,entry).items():
        module = importlib.import_module(name)
        if Path(module.__file__).resolve() != expected:
            raise RuntimeError('RUNTIME_IMPORT_ORIGIN: '+name)
        modules[name] = module
    if '--startup-check' in sys.argv[1:]:
        if sys.argv[1:] != ['--startup-check']:
            raise RuntimeError('startup check takes no operational arguments')
        print(json.dumps(dict(status='ENTRY_IMPORT_READY',entry=str(Path(entry).resolve()),
                              root=str(root),python=str(Path(sys.executable).resolve()),
                              modules={n:str(Path(m.__file__).resolve()) for n,m in modules.items()})),flush=True)
        raise SystemExit(0)
    return root
