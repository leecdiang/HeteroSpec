"""Three fixed sessions, one at a time; release GPU locks during date waits."""
import argparse
import datetime as dt
from pathlib import Path
import subprocess
import sys
import time
from native import read, write, utc
from analyze import analyze

STARTS = [('H1', '2026-11-13T15:00:00+00:00'),
          ('R1', '2026-11-13T19:00:00+00:00'),
          ('R2', '2026-11-14T19:10:00+00:00')]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    root = Path(read(args.config)['output_root'])
    root.mkdir(parents=True, exist_ok=True)
    for panel, start in STARTS:
        deadline = dt.datetime.fromisoformat(start)
        write(root / 'QUEUE.json', dict(status='WAITING', next_panel=panel, scheduled_utc=start, utc=utc()))
        while dt.datetime.now(dt.timezone.utc) < deadline:
            if (root / 'STOP_REQUESTED').exists():
                write(root / 'QUEUE.json', dict(status='STOP_REQUESTED', utc=utc()))
                sys.exit(2)
            time.sleep(min(30, max(0, (deadline - dt.datetime.now(dt.timezone.utc)).total_seconds())))
        write(root / 'QUEUE.json', dict(status='RUNNING', panel=panel, scheduled_utc=start, utc=utc()))
        rc = subprocess.call([sys.executable, '-B', str(Path(__file__).with_name('native.py')),
                              '--config', str(args.config.resolve()), '--panel', panel])
        analyze(root, root / 'ANALYSIS.json')
        if rc:
            write(root / 'QUEUE.json', dict(status='STOPPED', panel=panel, returncode=rc, utc=utc(),
                  reason='Inspect retained failure before any later panel; no automatic retry'))
            sys.exit(rc)
    write(root / 'QUEUE.json', dict(status='COMPLETE', utc=utc()))
