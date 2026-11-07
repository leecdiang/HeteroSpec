from common95 import *
import importlib,collections
PARENT_CODE=LOCAL/'parent-restored/repository/scripts/platform/rtx_evidence_closeout_v1'
sys.path.insert(0,str(PARENT_CODE))
legacy=importlib.import_module('run_common')
legacy.REPO=REPO;legacy.LOCAL=LOCAL;legacy.PUB=PUB;legacy.PORT=19595
legacy.DESIGN_HEAD=DESIGN_HEAD;legacy.BASE_HEAD=PARENT_HEAD
native=importlib.import_module('resident')
native.REPO=REPO;native.LOCAL=LOCAL;native.PUB=PUB;native.PORT=19595
ACTIVE={}
def env95(mask,trace):
    env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','LLAMA_ARG_','GGML_','CUDA_'))}
    env['HS_SCOPE_MASK']=str(mask);env['HS_NATIVE_CAPTURE']=str(trace);env['HS_Q95_LAYOUT']=ACTIVE['layout']
    if ACTIVE.get('capture'):env['HS_Q95_CAPTURE']=str(trace.parent/'snapshots')
    if ACTIVE.get('reuse_probe'):env['HS_Q95_REUSE_TRACE']=str(trace.parent/'reuse-rejection.jsonl')
    return env
native.clean_env=env95
class Ledger95:
    def __init__(self):
        self.root=LOCAL/'ledger';self.root.mkdir(exist_ok=True)
        self.events=[read(p) for p in sorted(self.root.glob('*.json'))]
        self.life=sum(read(p)['seconds'] for p in (LOCAL/'runs').rglob('LIFETIME.json'));self.active_start=None
    def lifetime(self):return self.life
    def owned_now(self):return self.life+(time.perf_counter()-self.active_start if self.active_start else 0)
    def count(self,family,phase,kind=None):return sum(e['family']==family and e['phase']==phase and (kind is None or e['kind']==kind) for e in self.events)
    def started(self,slot):return any(e['slot']==slot for e in self.events)
    def charge(self,family,phase,kind,slot):
        assert not self.started(slot),'started slot immutable; no retries'
        assert self.owned_now()<43200-252,'owned GPU12hour cap'
        if phase=='formal' and kind in ['request','warmup']:
            cap=2016 if kind=='request' else 84
            assert sum(e['phase']=='formal' and e['kind']==kind for e in self.events)<cap
        elif kind in ['request','warmup']:
            assert sum(e['phase']!='formal' and e['kind'] in ['request','warmup'] for e in self.events)<512
        if kind=='operator':assert sum(e['kind']=='operator' for e in self.events)<216
        e=dict(index=len(self.events),utc=now(),family=family,phase=phase,kind=kind,slot=slot)
        save(self.root/f'{len(self.events):06d}.json',e);self.events.append(e);return e
class Worker95(native.Resident):
    def __enter__(self):
        ACTIVE.clear();ACTIVE.update(self.c)
        try:
            result=super().__enter__();self.ledger.active_start=self.start;return result
        except BaseException:
            if hasattr(self,'start') and not (self.d/'LIFETIME.json').exists():
                if hasattr(self,'p') and self.p.poll() is None:self.p.kill();self.p.wait()
                if hasattr(self,'log'):self.log.close()
                seconds=time.perf_counter()-self.start
                save(self.d/'LIFETIME.json',dict(seconds=seconds,utc=now(),phase=self.phase,failed_load=True));self.ledger.life+=seconds
            raise
    def __exit__(self,*args):
        super().__exit__(*args);self.ledger.active_start=None
def condition(name,**extra):
    if name=='R':return dict(name=name,prefill_ub=1,maximum_k=0,mask=0,spec=False,required_output_rows=1,layout='QB',**extra)
    if name=='C_MQ':return dict(name=name,prefill_ub=4,maximum_k=3,mask=0,spec=True,required_output_rows=4,layout='QB',**extra)
    prefix,layout=name.split('_')
    return dict(name=name,prefill_ub=4,maximum_k=3 if prefix=='C' else 0,mask=3,spec=prefix=='C',required_output_rows=4 if prefix=='C' else 1,layout=layout,**extra)
def cooling(name):
    native.cooldown(LOCAL/'cooldown'/(name+'.json'))
def records(phase):return [read(p) for p in sorted((LOCAL/'runs'/phase).rglob('RECORD.json'))]
def signature(row):
    o=row['output'];return (o['ids'],o['eog_flags'],o['length'],o['terminal_id'],o['stop_reason'],o['cached_tokens'],o['truncated'])
