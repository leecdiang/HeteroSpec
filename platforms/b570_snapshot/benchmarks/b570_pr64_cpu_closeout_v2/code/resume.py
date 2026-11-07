"""Finite CPU units; reuse only when exact code, input and stage outputs still match."""
from evidence import *
import subprocess
def main():
    if (OUT/'INPUT_BINDINGS.json').exists():
        for n,v in json.loads((OUT/'INPUT_BINDINGS.json').read_text())['files'].items():assert digest((RAW/n).read_bytes())==v['sha256'], 'resume input changed '+n
    for stage,script in [('qualification','qualification.py'),('cross','cross.py'),('cost_work','cost_work.py'),('figures','figures.py'),('log_timers','log_timers.py')]:
        path=pathlib.Path(__file__).parent/script
        units=json.loads((OUT/'UNIT_MANIFEST.json').read_text()) if (OUT/'UNIT_MANIFEST.json').exists() else {}
        u=units.get(stage,{})
        valid=u.get('source_sha256')==digest(path.read_bytes()) and u.get('reader_sha256')==digest((path.parent/'evidence.py').read_bytes()) and all((OUT/n).exists() and digest((OUT/n).read_bytes())==h for n,h in u.get('output_hashes',{}).items())
        if valid:event('CPU_REUSE',stage=stage)
        else:
            result=subprocess.run([sys.executable,str(path)])
            if result.returncode:event('CPU_FAILURE',stage=stage,exit_code=result.returncode);sys.exit(result.returncode)
    print('Finite raw CPU stages complete; run handoff, independent verification and seal next.')
if __name__=='__main__':main()
