"""Prepare fixed inputs and qualification witnesses without new-task forwards."""
import gzip, hashlib, json, os, subprocess, sys, urllib.request
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent
DOC = ROOT / 'benchmarks/rtx_target_verification_intervention_v1'
OUT = ROOT / 'work/rtx-target-v1'
ASSET = Path(os.environ.get('HETEROSPEC_ASSET_ROOT', 'D:/HeteroSpec-PC'))
RUNTIME = ASSET / 'tools/llama-b10839'
PIN = ASSET / 'tools/llama-debug-src'
BASE = '6a3a7e2483d5b13a24518d27b8c1ff3eafaac08f'
UPSTREAM = '0cae43063cf15170e91a2ff4d034da0ecef4a1b2'
STUDY = 'RTX_TARGET_VERIFICATION_INTERVENTION_V1'
TASKS = ['HumanEval/'+str(i) for i in [143,31,25,81,15,141,142,18,136,99,148,140,87,76,26,49,40,109,66]]
G0TASKS = ['HumanEval/'+str(i) for i in [15,18,25,31,143]]
EOG = {128247,151643,151645,151662,151663,151664}

def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p, x):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_name(p.name+'.tmp')
    with q.open('w',encoding='utf-8',newline='\n') as f:
        json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(q,p)
def formatted(s):
    if s.endswith('\n'): s=s[:-1]
    return '<|im_start|>user\n'+s+'<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'

def main():
    DOC.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    if (DOC/'PREPARED.json').exists(): raise RuntimeError('Preparation already exists; inspect and resume')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=PIN,text=True).strip()==UPSTREAM
    save(DOC/'BUDGET.json', {'started_utc':'2026-10-04T05:49:30+00:00','deadline_utc':'2026-10-04T17:49:30+00:00','preparation_deadline_utc':'2026-10-04T08:49:30+00:00','measurement_deadline_utc':'2026-10-04T16:49:30+00:00','hours':12,'resume_resets_budget':False})
    old=ROOT/'benchmarks/rtx_trajectory_cost_v4'
    hist=read(old/'ASSET_IDENTITY.json');files={};matched={}
    for k,rec in hist['assets'].items():
        p=Path(rec['path']);h=sha(p);assert h==rec['sha256'],k
        files[k]={'path':str(p),'sha256':h,'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}
    for name,rec in hist['runtime'].items():
        p=RUNTIME/name;h=sha(p);assert h==rec['sha256'],name
        matched[name]=h
        files['runtime/'+name]={'path':str(p),'sha256':h,'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}
    env={'created_utc':utc(),'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,driver_version,pci.bus_id','--format=csv,noheader'],text=True).strip(),'python':sys.version,'runtime_version':subprocess.check_output([str(RUNTIME/'llama-cli.exe'),'--version'],stderr=subprocess.STDOUT,text=True).strip(),'os':json.loads(subprocess.check_output(['powershell','-NoProfile','-Command','Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber | ConvertTo-Json'],encoding='utf-8-sig')),'overrides':{k:v for k,v in os.environ.items() if k.startswith(('LLAMA_','GGML_','CUDA_'))}}
    assert 'NVIDIA GeForce RTX 5070 Ti Laptop GPU' in env['gpu']
    env['historical_os_equal']=env['os']==read(old/'ENVIRONMENT.json')['os']
    env['historical_driver_equal']=env['gpu'].split(', ')[2]==read(old/'ENVIRONMENT.json')['gpu']['values'][1]
    save(DOC/'ASSET_ENVIRONMENT.json',{'environment':env,'files':files,'historical_runtime_hashes_equal':True,'base':BASE,'upstream':UPSTREAM,'main_at_prepare':subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]})
    # Preserve historical arrays and map each new baseline to its actual V4 condition.
    predictions=read(old/'A_trajectory/RESERVED_PREDICTIONS.json')
    native=read(ROOT/'paper/mlsys2027/evidence/RTX_V4_INDEPENDENT_RAW_CLOSEOUT_20261002/A-live.ORIGINAL_RECORDS.json')['runs']
    expected={};inputs={}
    with gzip.open(ASSET/'datasets/humaneval/HumanEval.jsonl.gz','rt',encoding='utf-8') as f:
        data={x['task_id']:x for x in map(json.loads,f)}
    for row in predictions['rows']:
        t=row['task_id'];r=row['repetition']
        for c,oldc in [('R','A_REFERENCE_UB1'),('H0','A_H2_P_R')]:
            x=row['conditions'][oldc];expected[f'{t}/{c}/{r}']={'ids':x['generated_ids'],'endpoint':x['termination'],'source_condition':oldc}
        x=next(x for x in native if x['task_id']==t and x['repetition']==r)
        expected[f'{t}/N0/{r}']={'ids':x['generated_ids'],'endpoint':x['termination'],'source_condition':'A_NATIVE_BATCHED_LIVE'}
        text='Complete the following Python function. Return only the completed Python code, without Markdown fences.\n\n'+data[t]['prompt']
        assert hashlib.sha256(text.encode()).hexdigest()==row['input_sha256']
        p=OUT/'inputs'/t.replace('/','-');p.mkdir(parents=True,exist_ok=True)
        (p/'prompt.txt').write_text(text,encoding='utf-8',newline='\n')
        inputs[t]={'prompt':str((p/'prompt.txt').relative_to(ROOT)).replace('\\','/'),'prompt_sha256':sha(p/'prompt.txt'),'group':'old_regression'}
    assert len(expected)==171 and set(inputs)==set(TASKS)
    save(DOC/'HISTORICAL_EXPECTED.json',expected)
    save(DOC/'HISTORICAL_MAPPING.json',{'R':'A_trajectory/RESERVED_PREDICTIONS.json rows.conditions.A_REFERENCE_UB1','H0':'A_trajectory/RESERVED_PREDICTIONS.json rows.conditions.A_H2_P_R','N0':'paper/mlsys2027/evidence/RTX_V4_INDEPENDENT_RAW_CLOSEOUT_20261002/A-live.ORIGINAL_RECORDS.json runs','sources':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [old/'A_trajectory/RESERVED_PREDICTIONS.json',ROOT/'paper/mlsys2027/evidence/RTX_V4_INDEPENDENT_RAW_CLOSEOUT_20261002/A-live.ORIGINAL_RECORDS.json']}})
    save(OUT/'INPUTS.json',inputs)
    save(DOC/'PREPARED.json',{'status':'PREPARED','utc':utc(),'new_task_forwards':0,'formal_units':0,'qualification_pending':True})
    print(json.dumps({'environment':env,'runtime_dlls_verified':len(matched),'historical_expected':len(expected)}),flush=True)

if __name__=='__main__': main()
