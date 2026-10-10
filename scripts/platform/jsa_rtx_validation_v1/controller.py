"""Sequential GPU pipeline, finite engineering and separately frozen confirmation."""
from common import *
import sys
PY=sys.executable;HERE=Path(__file__).parent
def call(name,*args):subprocess.run([PY,str(HERE/name),*args],check=True)
def main():
    receipt=read(LOCAL/'F_E_ENGINEERING_REMOTE_RECEIPT.json');assert receipt['remote_sha']==receipt['frozen_sha'] and receipt['manifest_sha256']==sha(PUB/'F_E_ENGINEERING_F0.json')
    plan=read(PUB/'F_E_ENGINEERING_F0.json')
    for name,h in plan['code_sha256'].items():assert sha(HERE/name)==h,'engineering code drift'
    assert sha(PUB/'MODEL_CHOICE.json')==plan['model_choice_sha256'] and sha(PUB/'NATIVE_BUILD.json')==plan['native_build_sha256']
    for name,h in plan['resolved_inputs'].items():assert sha(PUB/name)==h
    family_cfg=read(LOCAL/'F_MODEL_CONFIG.json');assert family_cfg['models']==read(PUB/'MODEL_CHOICE.json')['models']
    native=read(PUB/'NATIVE_BUILD.json');binroot=LOCAL/'native/build/bin'
    for name,h in native['all_runtime_dlls'].items():assert sha(binroot/name)==h
    for name,h in native['binaries'].items():assert sha(binroot/name)==h
    for m in family_cfg['models'].values():assert sha(m['path'])==m['sha256']
    while not (LOCAL/'runs/S_formal/COMPLETE.json').exists():time.sleep(20)
    call('verify_s.py');call('engineering.py','bridge');call('verify_engineering.py','bridge')
    call('engineering.py','family_proof');family=True
    try:call('verify_engineering.py','family_graph')
    except subprocess.CalledProcessError:family=False
    for model in ['Qwen','SmolLM2']:
        try:call('engineering.py',model);call('verify_engineering.py',model)
        except subprocess.CalledProcessError:
            if not (PUB/('E_ENGINEERING_'+model+'.json')).exists():
                save(PUB/('E_ENGINEERING_'+model+'.json'),{'status':'IMPLEMENTATION_BLOCKED','model':model,'reason':'engineering operation failed; all partial attempts retained; no automatic retry'})
    if family:
        call('engineering.py','discovery');call('verify_engineering.py','discovery');assert read(PUB/'F_DISCOVERY.json')['capture_on_off_qualified'],'family capture qualification failed'
        call('natural.py');assert read(PUB/'F_NATURAL_DIAGNOSTICS.json')['status'] in ['NOT_TRIGGERED','ALIGNMENT_UNSUPPORTED'],'supported natural crosses need completion'
    models=[]
    for model in ['Qwen','SmolLM2']:
        if model=='SmolLM2' and not family:continue
        call('formal.py','prepare',model)
        if (PUB/(model+'_F0.json')).exists():models.append(model)
    for model in models:call('freeze.py','Freeze '+model+' paid balanced confirmation',model+'_F0.json')
    for model in models:call('formal.py','run',model);call('verify_confirmation.py',model)
    save(LOCAL/'PIPELINE_COMPLETE.json',{'utc':now(),'confirmation_models':models,'family_implementation_qualified':family});print('GPU PIPELINE COMPLETE',flush=True)
if __name__=='__main__':main()
