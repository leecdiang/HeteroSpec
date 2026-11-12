"""One explicit entry point. CPU commands never chain into a GPU command."""
import argparse
from pathlib import Path
import subprocess
import sys


def main():
    modes={'build':'cpu_pipeline.py','prepare':'prepare.py','freeze':'freeze_cpu.py',
           'admit':'admit.py','qualify':'qualify.py','f1':'f1.py','run-s2':'run_s2.py',
           'analyze':'analyze.py','archive':'archive.py','deliver':'deliver.py','historical-reader':'fixture_replay.py'}
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=sorted(modes))
    args,remaining=p.parse_known_args();program=Path(__file__).parent/modes[args.mode]
    result=subprocess.run([sys.executable,'-B',str(program),*remaining],stdin=subprocess.DEVNULL)
    raise SystemExit(result.returncode)


if __name__=='__main__':main()
