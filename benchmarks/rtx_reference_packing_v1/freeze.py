"""Generate actual execution F0 after H1 tests and before formal starts."""
import ctypes
import json
import platform
import shutil
import sys
import time
from pathlib import Path
from prepare import ROOT,sha,save

def main():
    assert not (ROOT/'formal').exists() and not (ROOT/'CPU_F0.json').exists()
    tests=ROOT/'child_ledger/000-H1_R1_tests-EXIT.json';assert json.loads(tests.read_bytes())['exit_code']==0
    plan=json.loads((ROOT/'PLAN.json').read_bytes());assert len(plan['cells'])==390
    class Status(ctypes.Structure):
        _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(k,ctypes.c_ulonglong) for k in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
    mem=Status();mem.length=ctypes.sizeof(mem);assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
    # Exclude this currently running watchdog's unresolved receipt; completed prior jobs are frozen.
    files={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='CPU_JOB.lock' and not (p.parent.name=='child_ledger' and 'H1_F0' in p.name)}
    exe=Path(sys.executable);runtime={str(p):sha(p) for p in sorted(exe.parent.iterdir()) if p.is_file() and (p.suffix.lower() in ('.exe','.dll','.zip') or p.name=='pyvenv.cfg')}
    save(ROOT/'CPU_F0.json',dict(schema=1,utc_epoch=time.time(),study='PR110_AV_PARITY_v1',
        prerequisite_PR104_commit='f997262d6b0accb126a1217c9356745cc8bbf708',design_commit='324dbb7ccd07d5a5fc787fc56cc6f07ff18725f9',
        reference='DECLARED_ARCHITECTURE_REFERENCE',files=files,runtime=runtime,python=sys.version,platform=platform.platform(),
        host=dict(machine=platform.node(),physical_memory_bytes=mem.total,available_memory_bytes=mem.available,disk_free_bytes=shutil.disk_usage(ROOT).free),
        prefreeze_completed_child_seconds=sum(json.loads(p.read_text())['seconds'] for p in (ROOT/'child_ledger').glob('*-EXIT.json')),
        current_F0_job='Charged on watchdog exit; formal watchdog sums all prior EXIT seconds without reset',
        budget=plan['budget'],formal_cells=390,native_groups=24,synthetic_inputs=2,new_GPU_model_operator_starts=0,
        estimation='deterministic finite panel; no significance or bootstrap; ratio baseline/candidate cycles',
        stop_rule='all five same-capability mappings on all frozen cells; retain failed attempts; no search expansion; SOFTWARE_FIRST if parity',
        acceptance='commit and push F0 then authenticated remote bytes readback required before first CELL_STARTED'))
    print(json.dumps(dict(files=len(files),runtime_files=len(runtime),formal_cells=390)))
if __name__=='__main__':main()
