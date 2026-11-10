"""Bounded standard-library-only logout probe. No CUDA or model imports."""
import argparse
import datetime
import json
import os
from pathlib import Path
import time


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--seconds', type=int, default=120)
    a = p.parse_args()
    if not 30 <= a.seconds <= 300:
        raise ValueError('Heartbeat bound must be 30..300 seconds')
    start = time.monotonic()
    with a.out.open('x') as f:
        n = 0
        while time.monotonic() - start < a.seconds:
            item = dict(counter=n, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        monotonic=time.monotonic(), pid=os.getpid(), native_requests=0,
                        cgroup=Path('/proc/self/cgroup').read_text().strip())
            f.write(json.dumps(item) + '\n')
            f.flush()
            os.fsync(f.fileno())
            n += 1
            time.sleep(2)


if __name__ == '__main__':
    main()
