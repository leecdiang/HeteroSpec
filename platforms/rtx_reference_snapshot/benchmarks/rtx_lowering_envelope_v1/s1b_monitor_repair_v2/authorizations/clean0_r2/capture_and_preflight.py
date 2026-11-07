"""Read-only identity checks; no GPU/device APIs; no alternate execution entry."""
import datetime,hashlib,sys,subprocess,time,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from common import V,load,save,sha,env
from lifecycle import Child
from admission import owned_conflicts
import run_s1b as R,exact_binding,audit

def main():
    d=Path(__file__).resolve().parent;begin=time.perf_counter();f=load(V/'F0.json');p=load(V/'PLAN.json');error=None
    message=(d/'AUTHOR_MESSAGE.txt').read_bytes().decode('utf-8').removesuffix('\n')
    approval=dict(stage='S1B_CLEAN_BLOCK_0_EXACT',run_id='pr116-s1b-cost-v1',execution_id='pr116-s1b-exact-r2',F0_sha256='f2d6965646e1f53c5d8a8b974f0277efc2903ed022689374af3f178fbad8e587',census_sha256='d8c79ed1b4fc748ec8ce22a201137ef6fc201de79052fa7c6c4f7711806e8256',archive_manifest_sha256='3b84a2d8f000e2a8be7aceb46695d562696cb6912c8b875b90913e4b1db11c56',decision_sha256=f['execution_bound_decision']['sha256'],decision_binding_basis='exact author-approved F0 pins this unchanged Decision',clean_first_trace_deferred_amendment_accepted=True,author_message=message,author_message_sha256=hashlib.sha256(message.encode()).hexdigest(),received_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),received_time_basis='actual local capture of this message;server delivery timestamp unavailable',author_message_transport_final_LF_excluded=True,independent_authorization=True,scope=dict(block=0,clean_hosts=72,warmups=72,measurements=576,graph_calls=648,retry=False,Block1_2_trace_actor_decoder=False))
    save(d/'APPROVAL.json',approval)
    try:
        assert sha(V/'F0.json')==approval['F0_sha256']
        assert sha(V/'delivery/cpu-qpc/ARCHIVE_MANIFEST.json')==approval['archive_manifest_sha256']
        assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=V).decode().strip()=='3377459d651dbcc58bda8e492cd5d0d7e7ca7fea'
        assert subprocess.check_output(['git','branch','--show-current'],cwd=V).decode().strip()==f['branch']
        subprocess.run(['git','diff','--exit-code'],cwd=V,check=True,stdout=subprocess.DEVNULL)
        assert not Path(f['execution_root']).exists() and not (V/'execution_ledger').exists(),'already started;no retry'
        assert not Path(f['fresh_restore_root']).exists()
        R.authority('clean0',f,approval);R.check(f,p)
        c,dec=exact_binding.admit(f,approval,V/'F0.json')
        expected={(r['descriptor_id'],r['layout']):r for r in load(V/'CPU_EXPECTED.json')}
        import json
        assert audit.census(json.loads(c),p,expected)==json.loads(dec)
        assert len([s for s in p['clean_slots'] if s['block']==0])==72
        owned_conflicts(f)
        assert shutil.disk_usage(Path(f['execution_root']).anchor).free>=f['budget']['limits']['disk_free_before']
        prefix=d/'remote_PR';Child(f['console_helper']).run([f['gh']['path'],'pr','view','118','--repo','leecdiang/HeteroSpec','--json','headRefOid,isDraft,headRefName'],prefix,60,env(''),512*1024**2)
        pr=load(d/'remote_PR.stdout');assert pr['headRefOid']=='3377459d651dbcc58bda8e492cd5d0d7e7ca7fea' and pr['isDraft'] and pr['headRefName']==f['branch']
        save(d/'PREFLIGHT_PASS.json',dict(run_id=f['run_id'],execution_id=f['execution_id'],F0_sha256=sha(V/'F0.json'),Census_sha256=hashlib.sha256(c).hexdigest(),Decision_sha256=hashlib.sha256(dec).hexdigest(),archive_manifest_sha256=approval['archive_manifest_sha256'],all_frozen_files_pass=True,supported_Block0_coordinates=72,QPC=f['monitor_contract']['actual_clock'],new_execution_root_absent=True,old_stage_and_conflicts_absent=True,PR=pr,GPU_queries=0,CUDA_loads=0,graph_calls=0,seconds=time.perf_counter()-begin,next_only='one frozen run_s1b.py --stage clean0 --approval APPROVAL.json;readiness inside controller'))
        print('PASS read-only exact preflight;GPU0;one approved controller may now launch')
    except BaseException as e:
        error=repr(e);save(d/'PREFLIGHT_STOP.json',dict(reason=error,no_retry=True,GPU_queries=0,CUDA_loads=0,graph_calls=0,unstarted_coordinates=72,run_id=f['run_id'],execution_id=f['execution_id']));raise
if __name__=='__main__':main()
