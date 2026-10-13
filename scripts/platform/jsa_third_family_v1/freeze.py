"""Publish immutable prospective boundaries and verify actual authenticated remote bytes."""
from common import *
import base64,shutil

def gh_json(route):return json.loads(subprocess.check_output(['gh','api',route],text=True,encoding='utf-8'))
def code_hashes():return {p.name:sha(p) for p in sorted(Path(__file__).parent.iterdir()) if p.suffix in ['.py','.cpp']}
def runtime_hashes():
    build=read(PUB/'NATIVE_BUILD.json');bin=LOCAL/'native/build/bin'
    files={str(bin/'llama-server.exe'):build['binary_sha256'],str(bin/'llama-cli.exe'):build['cli_sha256'],**{str(bin/n):h for n,h in build['runtime_dlls'].items()}}
    for p,h in files.items():assert sha(p)==h
    return files

def prepare(phase):
    assert phase in ['F0A','F0B'];assert read(PUB/'EXPOSURE_AUDIT.json')['status']=='PASS';assert read(PUB/'STATIC_INPUT_SELECTION.json')['status']=='PASS'
    if phase=='F0A':
        from engineering import jobs
        assert not list((LOCAL/'runs').rglob('REQUEST_STARTED.json'))
        for family in ['Qwen','SmolLM2','Llama']:
            z=read(PUB/f'ZERO_LOAD_{family}_02.json');assert z['status']=='PASS' and z['model_forwards']==0 and z['binary_sha256']==read(PUB/'NATIVE_BUILD.json')['binary_sha256']
        assert read(PUB/'DISPLAY_CHANGE_ADMISSION.json')['status']=='PASS'
        shutil.copyfile(LOCAL/'native/SOURCE_HASHES_FINAL.json',PUB/'NATIVE_SOURCE_HASHES.json')
        save(PUB/'ENGINEERING_PLAN.json',{'jobs':jobs(),'paid_requests_including_warmups':624,'hard_cap':640,'auxiliary_decodes_planned':0,'owned_GPU_process_hours_cap':8,'configuration_search':'NONE','confirmation_inputs_not_loaded_by_runner':True})
    else:
        from formal import schedule
        assert not list((LOCAL/'runs/formal').rglob('REQUEST_STARTED.json'))
        assert (LOCAL/'F0A_REMOTE_RECEIPT.json').exists() and (PUB/'ENGINEERING_RESULTS.json').exists()
        save(PUB/'FORMAL_PLAN.json',{'conditions':read(DESIGN/'DESIGN.json')['conditions'],'blocks':schedule(),'formal_requests':3456,'warmups':144,'sessions_per_family':2,'rounds_per_session':4,'planned_per_family_condition':192,'owned_GPU_process_hours_cap':24,'formal_retries':0,'actual_calendar_dates_retained':True,'independent_days':False,'cooling':'idle120s +3samples10s apart util<=5 temp<=55 range<=2 AC1, max600s','qualification':'comparison-specific full192 native-array gate plus stable complete paid R; no suffix truncation/subset/imputation','statistic':'median4 absolute costs per task/condition/session, average24 paired logs, average2sessions; date CIs/cross-date decisions null','primary':'Llama M3/C3_K3; k1/k2 predeclared secondary; no winner selection'})
    payload={p.name:sha(p) for p in sorted(PUB.iterdir()) if p.is_file()}
    save(PUB/(phase+'.json'),{'study_id':'JSA_THIRD_FAMILY_V1','phase':phase,'utc':now(),'design_PR':83,'design_SHA':DESIGN_SHA,'starting_head':head(),'payload_sha256':payload,'code_sha256':code_hashes(),'runtime_binaries':runtime_hashes(),'native_source_inventory_sha256':sha(PUB/'NATIVE_SOURCE_HASHES.json'),'source_runtime_note':'requested logical_batch2048 is natively clamped to effective n_batch1024 by ctx1024; both requested/effective logs retained; physical targetUB1/4 draftUB1','amendment_sha256':sha(PUB/'AMENDMENT_FAST.md'),'statistics_inference':'descriptive two-session effects; six-date CIs and cross-date positive claims untested/null','request_budget':{'engineering_cap_including_warmups':640,'engineering_planned_including_warmups':624,'formal':3456,'formal_warmups':144,'maximum_full_requests':4240,'owned_GPU_process_hours_cap':32,'calendar_days_cap':14},'code_status':'preliminary engineering' if phase=='F0A' else 'immutable confirmation','official_conversion_lineage':'publisher bytes and revisions verified; official checkpoint conversion ancestry unverified'})
    print('PREPARED',phase,flush=True)

def readback(phase):
    manifest=read(PUB/(phase+'.json'));commit=head();branch=subprocess.check_output(['git','branch','--show-current'],cwd=REPO,text=True).strip()
    remote=gh_json('repos/leecdiang/HeteroSpec/git/ref/heads/'+branch);assert remote['object']['sha']==commit
    tree=gh_json('repos/leecdiang/HeteroSpec/git/trees/'+commit+'?recursive=1');assert not tree.get('truncated')
    wanted={}
    for directory in [PUB,Path(__file__).parent]:
        for p in directory.iterdir():
            if p.is_file():wanted[p.relative_to(REPO).as_posix()]=sha(p)
    checked={};items={r['path']:r for r in tree['tree']}
    for path,h in wanted.items():
        item=items[path];blob=gh_json('repos/leecdiang/HeteroSpec/git/blobs/'+item['sha']);assert blob['encoding']=='base64';b=base64.b64decode(blob['content']);actual=hashlib.sha256(b).hexdigest();assert actual==h
        checked[path]={'sha256':actual,'git_blob':item['sha'],'bytes':len(b)}
    receipt={'status':'PASS','utc':now(),'frozen_sha':commit,'remote_sha':remote['object']['sha'],'phase':phase,'manifest_sha256':sha(PUB/(phase+'.json')),'actual_authenticated_GitHub_blob_readback':checked,'remote_transport':'authenticated GitHub REST ref/tree/blob bytes, not local Git cache','new_forwards_before_boundary':len(list((LOCAL/'runs').rglob('REQUEST_STARTED.json')))}
    save(LOCAL/(phase+'_REMOTE_RECEIPT.json'),receipt);save(PUB/(phase+'_REMOTE_READBACK.json'),receipt)
    print('ACTUAL REMOTE READBACK PASS',phase,commit,'files',len(checked),flush=True)
if __name__=='__main__':
    import sys
    {'prepare':prepare,'readback':readback}[sys.argv[1]](sys.argv[2])
