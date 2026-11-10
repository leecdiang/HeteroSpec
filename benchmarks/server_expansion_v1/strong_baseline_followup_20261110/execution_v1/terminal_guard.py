"""Read-only terminal proof plus this phase's lifecycle lock, no GPU calls."""
from contextlib import contextmanager
import fcntl
from pathlib import Path
from support import need,read


@contextmanager
def terminal_phase(configuration,allowed):
    root=Path(configuration['output_root']);status=read(root/'STATE.json')['status']
    need(status in allowed,'Refuse export of a live/unknown phase')
    need((root/'LOCK_RELEASED.private.json').is_file(),'No phase supervisor exit/lock release proof')
    with (root/'lifecycle.lock').open('a+')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for launch in (root/'workers').glob('*/LAUNCH.private.json'):
            j=read(launch);p=Path('/proc/'+str(j['pid'])+'/stat')
            if not p.exists():continue
            try:parts=p.read_text().rsplit(')',1)[1].split()
            except FileNotFoundError:continue
            need(parts[19]!=j['start_ticks']or parts[0]=='Z','Native worker is still alive; export forbidden')
        yield


def telemetry_public(value):
    g=value['selected_gpu']
    return {**{k:v for k,v in value.items()if k not in ('selected_gpu','selected_processes')},
            'allocated_GPU_metrics':dict(zip(('total_MiB','used_MiB','GPU_util_pct','temperature_C','SM_MHz','power_W'),g[1:]))}
