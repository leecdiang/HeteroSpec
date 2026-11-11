"""Resume unstarted phases after archive-path repair; no prior model run repeated."""
import sys,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];STUDY=ROOT/'benchmarks/rtx_trajectory_cost_v4'
sys.path.insert(0,str(STUDY));import FAN_AMENDMENT_EXECUTE as operator
import FAN_AMENDMENT_VERIFY_V2 as independent
from prepare import save,now
import guards,package,study,freeze,closeout,verify_joint,paper_evidence

def reconstruct(index,output):
    result=operator.ORIGINAL_RECONSTRUCT(index,output);out=package.longpath(Path(output).resolve());root=out/'evidence'
    proc=subprocess.run([sys.executable,'-B',str(root/'metadata/FAN_AMENDMENT_VERIFY_V2.py'),str(root)],capture_output=True)
    (out/'fan-amendment.stdout.log').write_bytes(proc.stdout);(out/'fan-amendment.stderr.log').write_bytes(proc.stderr)
    if proc.returncode:raise RuntimeError('Independent supplemental verifier failed: '+proc.stderr.decode(errors='replace'))
    result['independent_fan_amendment']=json.loads(proc.stdout);save(out/'RECONSTRUCTION.json',result);return result
package.reconstruct=reconstruct

def seal_existing_predictions():
    guards.check_manifest('F0_MANIFEST.json');guards.check_manifest('FAN_AMENDMENT_MANIFEST.json');independent.check(ROOT)
    sealed=json.loads((STUDY/'A_trajectory/RESERVED_PREDICTIONS.json').read_text(encoding='utf-8'))
    assert len(sealed['rows'])==57 and sealed['pre_live_runs']==228
    assert not (STUDY/'F2_MANIFEST.json').exists()
    package.make('pre-live','A');freeze.manifest('F2');study.commit('RTX V4 F2: preserve complete predictions and explicitly authorized fan continuation');freeze.receipt('F2')

def run():
    out=ROOT/'work/fan-amendment/recovery1';out.mkdir(parents=True,exist_ok=False)
    record={'status':'STARTED','started_utc':now(),'scope':'Archive path correction; original frozen control/verification source and predictor records unchanged. Only unstarted live and B model conditions follow.','model_retries':0,'stages':[]};save(out/'records.json',record)
    try:
        for name,fn in [('seal-existing-predictions',seal_existing_predictions),('A-native-live',operator.live),('B-matched-cost',lambda:study.B_formal(type('Args',(),{'authorization':'EXECUTE_FROZEN','reviewed_sha':operator.AUTH['original_F0']})())),('independent-verification',lambda:verify_joint.all_reached(ROOT)),('closeout-and-paper',lambda:(closeout.reached(),paper_evidence.main(),operator.final_scope())),('complete-A-capsules',lambda:package.make('complete','A')),('complete-B-capsules',lambda:package.make('complete','B')),('complete-index',closeout.index)]:
            row={'stage':name,'status':'STARTED','started_utc':now()};record['stages'].append(row);save(out/'records.json',record);print('START',name,flush=True)
            fn();row.update(status='PASS',ended_utc=now());save(out/'records.json',record);print('PASS',name,flush=True)
        record['status']='COMPLETE'
    except Exception as e:record.update(status='STOPPED_PRESERVED_FOR_REVIEW',error=repr(e));raise
    finally:record['ended_utc']=now();save(out/'records.json',record)
if __name__=='__main__':run()
