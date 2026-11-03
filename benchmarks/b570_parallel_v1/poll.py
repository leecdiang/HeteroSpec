"""Fixed old-panel hot-path memory polling isolation; no historical timings overwritten."""
from host import *
import itertools,math
def build():
    for role,oldrole in [('poll3-R','original-final'),('poll3-C','shared-01')]:
        dest=ROOT/role;shutil.copytree(PR165/oldrole/'kit',dest/'kit')
        kit=dest/'kit/b570_producer_consumer_boundary_v1';p=kit/'native/boundary.cpp';s=p.read_text(encoding='utf-8')
        s=once(s,'struct NativeContext {','static bool poll_decode=false; static double poll_seconds=0; static int poll_queries=0;\nstruct NativeContext {')
        s=once(s,'DecodeScope scope(role,phase); capacity_check();','DecodeScope scope(role,phase); if(poll_decode){auto tick=Clock::now();capacity_check();poll_seconds+=seconds(tick);++poll_queries;}')
        s=once(s,'auto service=Clock::now();auto result_row=', 'capacity_check();poll_decode=slot.value("poll",false);poll_seconds=0;poll_queries=0;auto service=Clock::now();auto result_row=')
        s=once(s,'row.update(result_row);','row.update(result_row);row["poll_seconds"]=poll_seconds;row["poll_queries"]=poll_queries;capacity_check();')
        s=once(s,'NativeContext draft(d,1,false,"draft");capacity_check();','std::unique_ptr<NativeContext> draft; if(job.value("admit_draft",true))draft=std::make_unique<NativeContext>(d,1,false,"draft");capacity_check();')
        p.write_text('#include <memory>\n'+s,encoding='utf-8')
        hdr=kit/'native/transfer_scope.hpp'
        hdr.write_text(once(hdr.read_text(encoding='utf-8'),'need(available >= 128ULL','need(available <= total && available >= 128ULL'),encoding='utf-8')
        libs=(OLD_LIB/'build') if role=='poll3-R' else PR165/'build-01'
        src=next((OLD_LIB/'clean-source2').glob('llama.cpp-*')) if role=='poll3-R' else PR165/'source-01'
        command(['cmake','-S',kit,'-B',dest/'build','-G','Visual Studio 17 2022','-A','x64','-DLLAMA_SOURCE='+src.as_posix(),'-DQUALIFIED_BUILD='+libs.as_posix()],dest/'configure.log')
        command(['cmake','--build',dest/'build','--config','Release','--parallel','4'],dest/'compile.log')
        bin=dest/'build/bin/Release'
        for f in (libs/'bin/Release').glob('*.dll'):shutil.copyfile(f,bin/f.name)
        bind(role,bin,'boundary.exe')
def measure():
    panel=read(PR165/'UNSEEN.json');order=sorted(panel,key=lambda i:(len(panel[i]['prompt_ids']),i));selected=[order[0],order[-1]]
    plan=[dict(session=s,id=i,arm=arm,poll=p) for s in range(3) for i in selected for arm in ('R','M_PQ','M_QB','C_PQ','C_QB') for p in (False,True)]
    plan.sort(key=lambda v:(v['session'],hashval(['poll-isolation',v])))
    if not (ROOT/'POLL_PLAN.json').exists():write(ROOT/'POLL_PLAN.json',plan)
    assert read(ROOT/'POLL_PLAN.json')==plan
    totals=[];admissions={}
    for n,b in enumerate(plan):
        i=list(panel).index(b['id']);arm=b['arm']
        qual=PR165/'units'/f"qual-{i}-{'R' if arm=='R' else 'candidate'}"
        idx=0 if arm=='R' else ['M_PQ','M_QB','C_PQ','C_QB'].index(arm)
        template=read(qual/'JOB.json');s=template['slots'][idx];role='poll3-R' if arm=='R' else 'poll3-C'
        name=f'poll-{n:03d}';j=dict(template,payload_root=str(ROOT/'units'/name/'payload'),runtime_sha256=sha(ROOT/role/'FILES.json'),
             slots=[dict(s,slot_id=f'{stage}/{arm}',stage=stage,clean=True,observer='off',trace=False,poll=b['poll']) for stage in ('warmup','measured')])
        def args(u):return [str(u/'native'),*MODELS['qwen'],str(PR165/'UNSEEN.json'),str(u/'JOB.json')]
        dual=arm.startswith('C_')
        if (role,dual) not in admissions:
            gate=f'pollgate-{role}-draft{int(dual)}'
            z=run(gate,role,dict(j,payload_root=str(ROOT/'units'/gate/'payload'),admit=True,admit_draft=dual),args=args,allow_failure=True)
            admissions[role,dual]=z['status']=='ZERO_FORWARD_ADMITTED'
        if not admissions[role,dual]:
            totals.append(dict(**b,seconds=None,error='zero-forward capacity admission failed'));continue
        native=run(name,role,j,args=args,allow_failure=True);reference=read(qual/'native/result.json')['requests'][idx]
        if native['status']!='WORKER_COMPLETE':
            totals.append(dict(**b,seconds=None,error=native.get('error',native['status'])));continue
        assert all(r['endpoint']==reference['endpoint'] and r['cycles']==reference['cycles'] for r in native['requests'])
        rec=native['requests'][1];totals.append(dict(**b,seconds=rec['service_seconds'],poll_seconds=rec['poll_seconds'],queries=rec['poll_queries']))
    comp={}
    for arm in ('R','M_PQ','M_QB','C_PQ','C_QB'):
        vals={(r['id'],r['session'],r['poll']):r for r in totals if r['arm']==arm}
        ratios=[vals[i,s,True]['seconds']/vals[i,s,False]['seconds'] for i in selected for s in range(3) if vals[i,s,True]['seconds'] and vals[i,s,False]['seconds']]
        comp[arm]={'on/off':math.exp(math.fsum(map(math.log,ratios))/len(ratios)) if ratios else None,'ratios':ratios,'pairs':len(ratios)}
    write(ROOT/'POLL_RESULT.json',dict(rows=totals,contrasts=comp))
if __name__=='__main__':setup();{'build':build,'run':measure}[sys.argv[1]]()
