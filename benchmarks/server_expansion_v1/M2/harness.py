"""M2 native gates using unchanged independent trace/full-vector/KV readers."""
from pathlib import Path
from collections import Counter
from types import SimpleNamespace
import copy,datetime,hashlib,importlib.util,json,os,shutil,sys,time

ARMS={f'{cut}_{proj}_K{k}':(core,lower,k) for k in (3,7) for cut,lower in (('W','SIMPLE'),('L','LOCAL')) for proj,core in (('L4','loop4'),('P','packed'))}
def canonical(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
def load(runtime,repo):
    global need,read,save,sha,host,native,checks,trace,parse,freeze
    sys.dont_write_bytecode=True;sys.path.insert(0,str(runtime))
    from common import need,read,save,sha
    import host,qualify_native as native,native_checks as checks,freeze
    trace,parse=checks.legacy_readers(repo)

def prepare_runtime(root,out):
    need(not out.exists(),'Fresh M2 runtime epoch');shutil.copytree(root/'m1-runtime-01',out)
    p=out/'host.py';s=p.read_text();anchor='def reservation(job):'
    need(s.count(anchor)==1,'Pinned host reservation anchor')
    s=s.replace(anchor,anchor+"\n    if 'proposal_tape_requests' in job:\n        xs=job['proposal_tape_requests'];return len(xs),sum(len(x['prompt_ids'])+8*(len(x['greedy_ids'])-1) for x in xs)",1)
    anchor="        need(sum(r['requests'] for r in reserved)+req<=2048 and sum(r['rows'] for r in reserved)+rows<=4000000,'Study budget exhausted; no automatic extension')"
    need(s.count(anchor)==1,'Pinned cumulative budget guard')
    replacement="""        inherited=read(work/'INHERITED_ACCOUNTING.json')
        for x in inherited['ledgers']:need(sha(x['path'])==x['sha256'],'Immutable predecessor ledger changed')
        need(inherited['requests']+sum(r['requests'] for r in reserved)+req<=2048 and inherited['rows']+sum(r['rows'] for r in reserved)+rows<=8000000,'Cumulative PR197 envelope exhausted; preserve all failures, no refund')"""
    s=s.replace(anchor,replacement,1);p.write_text(s)
    save(out/'M2_SUPERVISOR_PORT.json',dict(original_host_sha256=sha(root/'m1-runtime-01/host.py'),host_sha256=sha(p),
        changes=['Native draft-only tape producer work reservation','Explicit cumulative original+M1+M2 2048 requests/8M conservative rows; original ledgers hash-locked'],
        unchanged=['GPU allocation/foreign-process/reserves/900s timeout','Original24 exact frozen slot guard','Reference freeze and all numerical comparisons']))

def capability(models,structures,core,cut,k,mode):
    topology=lambda s:{z:s[z] for z in ('layers','query_heads','kv_heads','head_k','head_v','K_elements','V_elements')}
    def ctx(ub,n):return dict(n_ctx=1024,n_batch=1024,n_ubatch=ub,outputs_max=n,outputs_per_seq=n,flash_attention=False,type_k='f16',type_v='f16')
    place=lambda s:dict(layers=['NVIDIA RTX A5000']*s['layers'],output='NVIDIA RTX A5000')
    return dict(schema='heterospec.m2.native-capability.v1',target_sha256=models['target_sha256'],draft_sha256=models['draft_sha256'],
        target_structure=topology(structures['target']),draft_structure=topology(structures['draft']),target_context=ctx(32,8),draft_context=ctx(4,1),
        target_placement=place(structures['target']),draft_placement=place(structures['draft']),k=k,draft_width=4,cut=cut,projection=core,
        proposal_mode=mode,target_output_reserve=8,threads=2,greedy=True,target_output_policy='PREFILL:last;VERIFY:all_original_rows',draft_output_policy='last',
        physical_rows_evidence='per-request executions and native physical width histograms')

def physical(r,x,draft=True):
    es=r['executions'];need(es,'Actual native executions required');k=r['k'];mode=r['proposal_mode'];need(k in (3,7) and r['target_output_reserve']==8,'Actual k/reserve')
    hist=dict(Counter(str(e['width']) for e in es));observed={z:v for z,v in r['target_physical_width_hist'].items() if v}
    need(hist==observed,'Actual frontend/core physical widths disagree')
    total=len(x['prompt_ids'])+(k+1)*len(r['cycles']);need(sum(e['width']for e in es)==total,'Actual target rows differ from transaction')
    need(all(0<e['width']<=32 and e['active_cells']==e['position']+e['width']<=1024 for e in es),'Actual capacity/active cells')
    verify_hist=Counter();verify_rows=[e for e in es if e['phase']=='VERIFY'];offset=0
    for c in r['cycles']:
        group=[];count=0
        while count<k+1:
            need(offset<len(verify_rows),'Missing physical verification group')
            e=verify_rows[offset];offset+=1
            need(e['position']==c['base']+count,'Actual verification append ordering')
            group.append(e);count+=e['width']
        need(sum(e['width']for e in group)==k+1,'Actual verification row count')
        need(sorted(i for e in group for i in e['requested_rows'])==list(range(k+1)),'All original requested row ownership')
        verify_hist.update(str(e['width'])for e in group)
        if mode=='replay':need(c['draft_before']==c['draft_after']=={'min':-1,'max':-1},'Replay must not manufacture draft KV')
    need(offset==len(verify_rows),'Unaccounted physical verification calls')
    dh=r['draft_physical_width_hist'];dr=sum(int(z)*v for z,v in dh.items())
    if mode=='live':
        need(r['draft_ubatch']==4 and dr==len(x['prompt_ids'])+(k+1)*len(r['cycles']),'Actual D4 live draft rows; k independent of UB')
        need(dh.get('4',0)>=len(x['prompt_ids'])//4,'Actual draft prefill UB4')
    else:need(mode=='replay' and dr==0 and not dh and r['draft_calls']==0 and r['draft_final_kv']=={'min':-1,'max':-1},'Target replay must execute zero draft calls and retain empty draft KV')
    return dict(target_histogram=hist,draft_histogram=dh,verify_width_histogram=dict(verify_hist),target_rows=total,draft_rows=dr,
        graphs_built=r['graphs_built'],graphs_reused=r['graphs_reused'],k=k,reserve=8,proposal_mode=mode)

class Study:
    def __init__(self,root,work,builds,repo):
        self.root=root;self.baseline=root/'run-01';self.w=work;self.builds=builds;self.repo=repo
        self.out=work/'qualification-01';self.out.mkdir();self.cfg=work/'config.json'
        self.models=read(self.baseline/'inputs-01/MODELS.json');self.profiles=read(self.baseline/'qualification-02/STATE_PROFILES.json')
        self.trace=trace;self.parse=parse;self.physical=physical;self.ref_build=self.baseline/'build-R-01/BUILD.json'
        self.structures={f:{r:checks.gguf_structure(m[r+'_model'])for r in ('target','draft')}for f,m in self.models.items()}
        old=root/'public-export-final-01'
        self.text={x['path']:x['raw_sha256']for x in read(old/'TEXT_INDEX.json')['files']}
        self.binary={x['path']:x['sha256']for x in read(old/'BINARY_CAPTURE_INDEX.json')['files']};self.verified=set();self.modules={};self.reports=[];self.banks={};self.counter=0;self.new_native_jobs=0;self.reuses=[];self.custom_reference={}
        self.prior=root/'m2-run-01';self.prior_manifest=None
        if (work/'PREDECESSOR_BINDING.json').exists():
            binding=read(work/'PREDECESSOR_BINDING.json');need(sha(binding['manifest'])==binding['sha256'],'Prior completed-native manifest changed')
            self.prior_manifest={x['path']:x for x in read(binding['manifest'])['files']}
        self.verify(self.baseline/'reference-01/REFERENCE_FREEZE.json');need(read(read(self.cfg)['reference_freeze'])['status']=='REFERENCE_FROZEN','Original R remains frozen')
        for name in ('vector_pair','state_pair'):
            original=getattr(native,name)
            def checked(a,b,*args,_original=original,**kwargs):self.verify(Path(a));self.verify(Path(b));return _original(a,b,*args,**kwargs)
            setattr(native,name,checked)
        # Reuse the original independently reconstructed transaction comparison.
        # Only replay's deliberately empty draft cache differs; live guard unchanged.
        import inspect
        src=inspect.getsource(native.Bank.check)
        anchor="cycle['draft_after']==cycle['target_after']"
        need(src.count(anchor)==1,'Pinned Bank replay state guard')
        src=src.replace(anchor,"cycle['draft_after']==({'min':-1,'max':-1} if r.get('proposal_mode')=='replay' else cycle['target_after'])",1)
        import textwrap
        ns=dict(native.__dict__);exec(compile(textwrap.dedent(src),'<M2 target replay Bank adapter>','exec'),ns)
        self.bank_check=ns['check']
        fill_original=inspect.getsource(native.Bank.fill);fill_src=fill_original
        need(fill_src.count('range(0,len(cases),12)')==1 and fill_src.count('cases[start:start+12]')==1,'Pinned independent R batch grouping')
        fill_src=fill_src.replace('range(0,len(cases),12)','range(0,len(cases),4)').replace('cases[start:start+12]','cases[start:start+4]')
        fn=dict(native.__dict__);exec(compile(textwrap.dedent(fill_src),'<M2 bounded independent R grouping>','exec'),fn);native.Bank.fill=fn['fill']
        original_add=native.Bank.add
        def verified_add(bank,out,cases):
            for c in cases:
                for n in c['observe_positions']:
                    directory=out/'native'/c['name']/'captures'/str(n);bank.s.verify(directory/'frontier.f32')
                    if n in c['state_positions']:bank.s.verify(directory/'sequence.bin')
            return original_add(bank,out,cases)
        native.Bank.add=verified_add
        save(self.out/'READER_ADAPTER.json',dict(original_bank_source_sha256=hashlib.sha256(inspect.getsource(native.Bank.check).encode()).hexdigest(),
            adapted_bank_source_sha256=hashlib.sha256(src.encode()).hexdigest(),change='Replay checks actual empty draft cache; original live target/draft rollback equality remains mandatory',
            full_vector_comparison_unchanged=True,float_vector_byte_multiplier=4,byte_multiplier_is_not_verification_width=True,
            state_reader_and_transaction_reconstruction_unchanged=True,reference_grouping='At most4 complete forced-prefix cases/job instead of12; no omitted prefixes, outputs or state bytes',
            original_reference_fill_sha256=hashlib.sha256(fill_original.encode()).hexdigest(),adapted_reference_fill_sha256=hashlib.sha256(fill_src.encode()).hexdigest()))
    def verify(self,p):
        if str(p) in self.verified:return
        if self.prior_manifest is not None and p.is_relative_to(self.prior):
            key=str(p.relative_to(self.prior));need(key in self.prior_manifest and sha(p)==self.prior_manifest[key]['sha256'],'Prior epoch operand changed '+key)
            self.verified.add(str(p));return
        if not p.is_relative_to(self.baseline) or str(p) in self.verified:return
        key=str(p.relative_to(self.baseline));need(key in self.text or key in self.binary,'Uncommitted historical operand '+key)
        need(sha(p)==self.text.get(key,self.binary.get(key)),'Historical byte commitment differs '+key);self.verified.add(str(p))
    def retained(self,label):
        out=self.baseline/'qualification-02/runs'/label;job=self.baseline/'qualification-02/jobs'/(label+'.json')
        for p in (job,out/'launch.json',out/'HOST.json',out/'native/result.json',out/'LOADED_MODULES.json'):self.verify(p)
        launch=read(out/'launch.json');need(read(out/'HOST.json')['status']=='COMPLETE' and launch['job_sha256']==sha(job) and launch['build_sha256']==sha(self.ref_build),'Original independent R launch')
        for p,x in read(out/'LOADED_MODULES.json').items():
            if x['kind']=='ELF_file':need(sha(p)==x['sha256'],'Original R module changed')
        return out
    def execute(self,label,family,job,core='reference',k=3,mode='live',phase=None,config=None):
        cutoff=datetime.datetime(2026,11,8,21,0,tzinfo=datetime.timezone.utc)
        need((cutoff-datetime.datetime.now(datetime.timezone.utc)).total_seconds()>=960,'Native start denied within960s of05:00 cutoff; preserve prior work')
        self.counter+=1;base=copy.deepcopy(self.models[family]);base.update(job)
        if core=='reference':
            base.pop('draft_model',None);base.pop('draft_sha256',None);base.update(draft=False,residency='target_only');build=self.ref_build
        else:
            base.update(draft=True,draft_width=4,residency='matched',profile=False,k=k,target_output_reserve=8,proposal_mode=mode)
            base['capability_request']=capability(self.models[family],self.structures[family],core,base['lowering'],k,mode);build=self.builds/core/'BUILD.json'
        path=self.out/'jobs'/(label+'.json');save(path,base);dest=self.out/'runs'/label
        retained=self.prior/'qualification-01/runs'/label;retained_job=self.prior/'qualification-01/jobs'/(label+'.json')
        if self.prior_manifest is not None and retained.exists():
            for p in (retained_job,retained/'HOST.json',retained/'launch.json',retained/'native/result.json',retained/'LOADED_MODULES.json'):self.verify(p)
            need(read(retained_job)==base and read(retained/'HOST.json')['status']=='COMPLETE','Never reuse a failed/incomplete native job or changed payload')
            launch=read(retained/'launch.json');need(launch['job_sha256']==sha(retained_job) and launch['build_sha256']==sha(build),'Retained job/build launch identity')
            for p,x in read(retained/'LOADED_MODULES.json').items():
                if x['kind']=='ELF_file':need(sha(p)==x['sha256'],'Retained ELF module changed')
            self.reuses.append(dict(label=label,prior=str(retained),prior_job_sha256=sha(retained_job),new_job_sha256=sha(path),native_replayed=False));dest=retained
            save(self.out/'reuse'/(label+'.json'),self.reuses[-1])
        else:
            host.run(config or self.cfg,build,path,dest,phase or ('reference' if core=='reference' else 'development'));self.new_native_jobs+=1
        self.modules.setdefault((core,family),dest/'LOADED_MODULES.json');need(read(self.modules[(core,family)])==read(dest/'LOADED_MODULES.json'),'Actual module map differs')
        if core!='reference':need(read(dest/'native/CAPABILITY.json')==base['capability_request'],'Complete native capability echo')
        return dest
    def bank(self,family,index,x):
        key=(family,index,x['cap'])
        if key in self.banks:return self.banks[key]
        if (family,index) in self.custom_reference:
            for p in self.custom_reference[(family,index)].rglob('*'):
                if p.is_file():self.verify(p)
            bank=native.Bank(self,family,index,x,self.custom_reference[(family,index)])
            self.banks[key]=bank;return bank
        free=self.retained(family+'-free-independent-R')/'native'/f'dev-{index}'
        self.verify(free/'receipt.json');old=read(free/'receipt.json');ids=old['ids'][:x['cap']];eog=old['eog'][:len(ids)]
        need(len(ids)==x['cap'] or eog[-1],'Derived frozen R prefix must terminate at cap/EOG')
        bank=native.Bank.__new__(native.Bank);bank.s=self;bank.family=family;bank.index=index;bank.input=x;bank.free=free;bank.entries={};bank.teacher_count=1000+len(self.banks)*1000
        bank.ep={**old,'ids':ids,'eog':eog,'terminal_kind':'EOG' if eog[-1] else 'CAP','stop_reason':'EOG' if eog[-1] else 'CAP'}
        for job in sorted((self.baseline/'qualification-02/jobs').glob(family+f'-root{index}-R-*.json')):
            out=self.retained(job.stem);bank.add(out,read(job)['cases'])
        # Share complete new independent prefix operands across cap variants.
        for (f,i,c),other in self.banks.items():
            if f==family and i==index:bank.entries.update(other.entries)
        self.banks[key]=bank;return bank
    def check_pair(self,family,index,x,actual,heavy,clean):
        meta=read(actual/'native/result.json');need(meta['total_observed_API_calls']['context_creates']==2,'Matched resident model/context pair')
        bank=self.bank(family,index,x);proof=self.bank_check(bank,actual/'native'/heavy,actual/'native'/clean,meta,True)
        need(proof['passed'],'Full vectors, active KV or frontier differs from independent R')
        for (f,i,c),other in self.banks.items():
            if f==family and i==index:other.entries.update(bank.entries)
        h=read(actual/'native'/heavy/'receipt.json');c=read(actual/'native'/clean/'receipt.json')
        need(native.endpoint(h)==native.endpoint(c),'Heavy/clean endpoint bridge')
        return dict(numerical=proof,k=h['k'],proposal_mode=h['proposal_mode'],heavy_receipt_sha256=sha(actual/'native'/heavy/'receipt.json'),
            clean_receipt_sha256=sha(actual/'native'/clean/'receipt.json'),branch_coverage=dict(rejection_accepted=sorted(set(z['accepted']for z in h['cycles']if z['rejected'])),
            accepted_any=any(z['accepted']>0 for z in h['cycles']),all_accepted=any(z['accepted']==h['k']for z in h['cycles']),
            commit_kinds=sorted(set(z['commit_kind']for z in h['cycles'])),terminal=h['stop_reason']),dispatch=self.dispatch(h))
    def dispatch(self,r):
        graph=[x for x in r['geometry']if x['op']=='MUL_MAT'];need(graph,'Actual GPU MUL_MAT graph descriptors required')
        packed=[x for x in graph if x['phase']=='VERIFY' and x['name'].startswith('frontier_packed_')]
        loop=[x for x in graph if x['phase']=='VERIFY' and x['name'].startswith('hs_backend_loop4_')]
        quant=[x for x in graph if x['phase']=='VERIFY' and x['sources'] and x['sources'][0]['type']=='q8_0']
        if r['k']==3:need(not packed,'q4 negative control cannot claim wide packing')
        if r['cycles'] and phase_widths(r).get(str(r['k']+1),0) and r['k']==7:
            # Packed/loop4 expectations are applied by the caller with its core.
            need(all(z['ne'][1]==4 and z['ne'][2]>=2 for z in packed),'Independent-group physical packed shapes')
        return dict(verify_physical_width_histogram=phase_widths(r),packed_verify_nodes=len(packed),marked_loop4_verify_nodes=len(loop),
            quantized_verify_nodes=len(quant),q4_plain_projection_shapes=all(x['ne'][1]<=4 and x['ne'][2]==1 for x in quant),
            packed_node_samples=packed[:3],loop4_node_samples=loop[:3],scope='Actual scheduled GPU MUL_MAT node/device descriptors plus core physical row counters; not CUDA kernel-symbol profiling')

def phase_widths(r):return dict(Counter(str(x['width'])for x in r['executions']if x['phase']=='VERIFY'))

def prepare_work(root,work,runtime,builds):
    need(not work.exists(),'Fresh independent M2 work root');work.mkdir()
    cfg=read(root/'run-01/config-reference-frozen-01.json');cfg.update(work_root=str(work),freeze=None,freeze_sha256=None);save(work/'config.json',cfg)
    ledgers=[];requests=rows=0
    for name in ('run-01','m1-run-01','m2-run-01'):
        p=root/name/'ledger.jsonl';xs=[json.loads(z)for z in p.read_text().splitlines()if json.loads(z)['event']=='RESERVE']
        requests+=sum(z['requests']for z in xs);rows+=sum(z['rows']for z in xs);ledgers.append(dict(path=str(p),sha256=sha(p)))
    save(work/'INHERITED_ACCOUNTING.json',dict(ledgers=ledgers,requests=requests,rows=rows,ceiling_requests=2048,ceiling_rows=8000000,
        original_ledger_counters_not_reset=True,failures_charged=True,reserved_rows_are_bounds_not_actual_physical_work=True))
    save(work/'SOURCE_FREEZE.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        qualified_M1_head='55f501e9a93013a4b4d82cc4967e82b8d9054a81',native_source_commit='61bcce0552b1a80e9345fa199238ebb7bc63e6ff',
        native_source_tar_sha256=sha(root/'m2-native-source-01.tar.gz'),build_complete_sha256=sha(builds/'BUILD_COMPLETE.json'),
        R_freeze_sha256=sha(root/'run-01/reference-01/REFERENCE_FREEZE.json'),R_unchanged=True,
        driver_sources={str(p):sha(p)for p in Path(__file__).parent.rglob('*')if p.is_file()},
        M2='Implementation/native qualification only until all gates pass; pilot descriptive64 live tests, separate32 target replay tests; never576 confirmation'))
