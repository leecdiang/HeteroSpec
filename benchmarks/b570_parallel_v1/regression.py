"""Two retained Llama controls and the original Qwen P1/k1 transactions."""
from experiment import *
import importlib.util
HIST=Path('C:/hs/b570-qwen-transfer/scripts/b570_qwen_transfer')
def llama():
    # Reuse the published independent parser, workload and exact assertions.
    sys.path.insert(0,str(HIST))
    import llama_controls as old
    old.ROOT=ROOT;old.run('00')
def qwen():
    original=read(ROOT/'units/original-P1-anchor/native/result.json')['records']
    slots=[r['slot'] for r in original]
    new=slots_run('D-P1-anchor',ROLE,'qwen',1024,slots)
    anchors=[dict(index=i,compared=len(r['vectors']) if r else 0,equal=bool(r and r['vectors']==old['vectors'] and r['greedy']==old['greedy'])) for i,r,old in zip((4,6,2),new,original)]
    put_once(ROOT/'D_P1_ANCHOR.json',anchors)
    role='legacy-D';dest=ROOT/role;bin=dest/'bin'
    if not (dest/'FILES.json').exists():
        bin.mkdir(parents=True)
        shutil.copyfile(ROOT/'poll3-C/build/bin/Release/boundary.exe',bin/'boundary.exe')
        for dll in (ROOT/'candidate-D/build/Release').glob('*.dll'):shutil.copyfile(dll,bin/dll.name)
        bind(role,bin,'boundary.exe')
    def args(u):return [str(u/'native'),*MODELS['qwen'],str(DATA),str(u/'JOB.json')]
    def replay(name,template,**extras):
        j=dict(template,runtime_sha256=sha(dest/'FILES.json'),payload_root=str(ROOT/'units'/name/'payload'),**extras)
        return run(name,role,j,args=args,allow_failure=True)
    reference=read(PR165/'units/retained-2-shared-01/JOB.json')
    g=replay('legacy-D-admit',reference,admit=True)
    results=[]
    for i in (4,6,2):
        u=PR165/f'units/retained-{i}-shared-01'
        if g['status']!='ZERO_FORWARD_ADMITTED':
            results.append(dict(index=i,status='NO_DUAL_CONTEXT_CAPACITY',reason=g.get('error',g['status'])));continue
        d=replay(f'legacy-D-retained-{i}',read(u/'JOB.json'))
        expected=read(u/'native/result.json')['requests']
        actual=d.get('requests',[])
        eq=len(actual)==len(expected) and all(a['endpoint']==b['endpoint'] and a['cycles']==b['cycles'] and {k:v['sha256'] for k,v in a['vectors'].items()}=={k:v['sha256'] for k,v in b['vectors'].items()} for a,b in zip(actual,expected))
        results.append(dict(index=i,status=d['status'],matches_PR165=eq))
    put_once(ROOT/'K1_REGRESSION.json',results)
if __name__=='__main__':{'llama':llama,'qwen':qwen}[sys.argv[1]]()

