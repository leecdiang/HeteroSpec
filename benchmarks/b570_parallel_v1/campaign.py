"""Continue the registered blocks serially on the exclusive physical device."""
from deployments import *
from diagnostic import observe
from binding import bind_source
from reuse import check as check_reuse
from geometry_service import run_controls
import regression,poll,service
def controls():
    for fam,C in configs():
        control(fam,C)
def mechanism():
    check_reuse()
    run_controls(ROLE)
    for fam,C in configs():
        B=2048 if C==4096 else 256
        for cross in (False,True):
            observe(fam,C,B,16,cross,ROLE,['PQ','QB','WB'],profile=True)
def regress():
    if not (ROOT/'K1_REGRESSION.json').is_file():regression.qwen()
    if not (ROOT/'units/llama-controls-00/REGRESSION.json').is_file():regression.llama()
def freeze():
    from datetime import datetime,timezone
    bind_source(ROLE)
    checks=[r for f,C in configs() for r in read(ROOT/f'CONTROL-{f}-{C}.json')]
    errors=[r for r in checks if r['observed'] and r['ref'] and r['arm']!='FAST' and not r['equal']]
    if errors:
        put_once(ROOT/'NEW_COUNTEREXAMPLES-D.json',errors)
        raise RuntimeError('structured arithmetic counterexamples require diagnosis before freeze')
    required=read(ROOT/'REUSE.json')
    assert required['QB']['equal'] and required['WB']['equal']
    assert all(r['equal'] for r in read(ROOT/f'SMOL_INTACT-{ROLE}.json') if r['arm']!='FAST')
    assert all(any(r['family']==f and r['C']==C and r['arm']==a and r['q']==32 and r['equal'] for r in checks) for f,C in configs() for a in ('S1','PQ','QB','WB'))
    if not (ROOT/'FREEZE.json').exists():
        write(ROOT/'FREEZE.json',dict(utc=datetime.now(timezone.utc).isoformat(),role=ROLE,width=32,source=sha(ROOT/f'SOURCE_BINDING-{ROLE}.json'),core='a0baff824a1b54fb3867845372939b9a97c11115',
            geometry_plan=sha(PLAN),deployments=sha(ROOT/'DEPLOYMENTS-D.json'),validated_configs=configs(),
            controlled_files={f'CONTROL-{f}-{C}.json':sha(ROOT/f'CONTROL-{f}-{C}.json') for f,C in configs()},
            missing=sum(not r['observed'] or not r['ref'] for r in checks),natural='C1024 Qwen original pair of resident all-GPU models, target-only requests; 12 prompts, six balanced sessions, cap128',
            estimation='paired geometric ratios, numerical eligibility, report missing data and reversals'))
def costs():
    assert (ROOT/'FREEZE.json').is_file()
    for f,C in configs():fixed(f,C)
if __name__=='__main__':
    {'control':controls,'mechanism':mechanism,'regress':regress,'poll':poll.measure,'freeze':freeze,'fixed':costs,
     'blind':service.confirm,'paired':service.costs}[sys.argv[1]]()

