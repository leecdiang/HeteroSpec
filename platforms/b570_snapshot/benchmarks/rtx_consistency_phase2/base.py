import hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
PHASE1=Path(os.environ.get('HETEROSPEC_PHASE1_ROOT',str(HERE.parent/'continuity-state-v1')))
ASSET=Path(os.environ.get('HETEROSPEC_ASSET_ROOT','D:/HeteroSpec-PC'))
sys.path.insert(0,str(PHASE1))
from run import native_module,ORIGINAL,OLD
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n');q.replace(p)
def now():return datetime.now(timezone.utc).isoformat()
def head():
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=HERE,text=True).strip()
    return subprocess.check_output(['git','rev-parse','HEAD'],cwd=HERE,text=True).strip()
def env(mask=None,capture=None):
    e={k:v for k,v in os.environ.items() if not k.startswith(('HS_','LLAMA_ARG_','LLAMA_BATCH_DEBUG','GGML_','CUDA_'))}
    if mask is None:e['HS_ATTENTION_QUERY_BATCH']='1'
    else:e['HS_SCOPE_MASK']=str(mask)
    if capture:e['HS_NATIVE_CAPTURE']=str(capture)
    return e
def prepare():
    assert read(PHASE1/'generated/analysis/POST_AUDIT.json')['status']=='PASS'
    inputs=read(PHASE1/'COST_INPUTS.json');assert len(inputs)==19
    save(HERE/'INPUTS.json',inputs)
    save(HERE/'SOURCE_BINDINGS.json',{'phase1_source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=PHASE1,text=True).strip(),
        'phase1_inputs_sha256':sha(PHASE1/'COST_INPUTS.json'),'phase1_cli_sha256':sha(PHASE1/'generated/build/bin/llama-cli.exe'),
        'phase1_server_sha256':sha(PHASE1/'generated/build/bin/llama-server.exe'),'phase1_build_identity':read(PHASE1/'generated/BUILD_IDENTITY.json'),
        'model_runtime_pre':read(PHASE1/'generated/ASSET_CHECK_POST.json'),'native_contracts':read(PHASE1/'INPUT_CONTRACTS.json'),
        'phase1_scope_note':'Private snapshot; original source/assets remain untouched.'})
if __name__=='__main__':prepare()
