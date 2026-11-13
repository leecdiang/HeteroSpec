"""Block our other research work during formal timing; never signal foreign work."""
import os
from pathlib import Path

def check(root):
    root=str(Path(root).resolve());uid=os.getuid()
    scripts={'acquire_exact.py','acquire_official_mirror.py','acquire_ranges.py','acquire_models.py','acquire_curl_ranges.py',
        'build_deployment.py','build_vocabulary.py','build_admission.py','build_native.py','build_dispatch.py',
        'prepare.py','export_transfer-v3.py','check_assets.py','prepare_eog.py','freeze_rules.py','export_evidence.py','export_m1.py','readback_export.py','integrate.py'}
    tools={'curl','nvcc','cc1plus','cicc','c++','g++','gcc','ld'}
    for proc in Path('/proc').iterdir():
        if not proc.name.isdecimal() or int(proc.name)==os.getpid():continue
        try:
            if proc.stat().st_uid!=uid:continue
            argv=[x.decode(errors='replace') for x in (proc/'cmdline').read_bytes().split(b'\0') if x]
        except (FileNotFoundError,PermissionError,ProcessLookupError):continue
        if not argv or not any(root in x for x in argv):continue
        base=Path(argv[0]).name
        script=next((Path(x).name for x in argv[1:] if x.endswith('.py')),'') if base.startswith('python') else ''
        if base in tools or script in scripts:
            raise RuntimeError('Our concurrent research work violates the formal quiet window; retain own slot, never kill the other task: PID='+proc.name+', kind='+(script or base))
