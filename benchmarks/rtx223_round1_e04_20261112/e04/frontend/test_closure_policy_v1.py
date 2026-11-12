"""New failure-boundary tests for conservative archive evidence, disk reads only."""
from pathlib import Path
import json
from closure_witness_v1 import analyze
from link_witness import WitnessError
HERE=Path(__file__).resolve().parent
run=HERE/'run-v4';recipe=json.loads((run/'RECIPE.json').read_bytes());info=recipe['cores']['loop4']
trace=(run/'loop4-link.stdout.log').read_text(encoding='utf8')+(run/'loop4-link.stderr.log').read_text(encoding='utf8')
mapping=(run/'build/loop4/worker.map').read_text(encoding='utf8')
objects=[arg for arg in info['link'] if Path(arg).is_absolute() and Path(arg).suffix.casefold()=='.obj']
bad_cases=[('',mapping),('lld-link: Reading C:\\not-frozen\\injected.lib\n'+trace,mapping),('lld-link: Reading C:\\not-frozen\\injected.obj\n'+trace,mapping),(trace,mapping+'\n 0001:00000000 injected_symbol 1400010000 unfrozen_archive:member.obj\n')]
for bad_trace,bad_map in bad_cases:
    try:analyze(bad_trace,info['archives'],objects,bad_map)
    except WitnessError:pass
    else:raise RuntimeError('incomplete or unfrozen archive evidence was admitted')
print(json.dumps({'status':'PASS','new_rejection_checks':len(bad_cases),'GPU_launches':0,'normal_numeric_DLL_loads':0,'EXE_runs':0}))
