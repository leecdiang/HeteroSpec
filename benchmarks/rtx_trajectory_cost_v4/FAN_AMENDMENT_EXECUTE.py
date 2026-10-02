"""Explicit fan-only authorization/host overlay; frozen numerical source untouched."""
import sys,os,json,hashlib,subprocess,time,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SRC=ROOT/'scripts/platform/rtx_trajectory_cost_v4';sys.path.insert(0,str(SRC))
from prepare import STUDY,save,sha,now
import guards,study,native_runner,configuration,identity,freeze,package,verify_A,analysis,closeout
sys.path.insert(0,str(STUDY));import FAN_AMENDMENT_VERIFY as independent
os.environ.update(PYTHONDONTWRITEBYTECODE='1',GODEBUG='http2client=0')
AUTH=json.loads((STUDY/'FAN_AMENDMENT.json').read_text(encoding='utf-8'))
BASELINE=json.loads((STUDY/'FAN_AMENDMENT_HOST_BASELINE.json').read_text(encoding='utf-8'))
PROTOCOL=json.loads((STUDY/'JOINT_PROTOCOL.json').read_text(encoding='utf-8'))
ORIGINAL_TELEMETRY=native_runner.telemetry

def observed_telemetry():
    observation=ORIGINAL_TELEMETRY();p=Path(os.environ['APPDATA'])/'GHelper/config.json';raw=p.read_bytes();cfg=json.loads(raw.decode('utf-8-sig'))
    fields={k:v for k,v in cfg.items() if any(w in k.lower() for w in ['mode','power','fan','cpu','gpu','limit','clock','profile','eco','performance'])}
    observation['ghelper_amendment_observation']={'utc':now(),'file_sha256':hashlib.sha256(raw).hexdigest(),'fields':fields}
    return observation

def assets(phase):
    original=json.loads((STUDY/'ASSET_IDENTITY.json').read_text(encoding='utf-8'));out=ROOT/'work'/('ASSET_OBSERVATION_FAN_'+phase+'.json');identity.main(out);actual=json.loads(out.read_text(encoding='utf-8'))
    for group in ['assets','runtime','frontends','driver_modules','timer_binaries']:
        for k,v in original[group].items():
            if actual[group][k]['sha256']!=v['sha256'] or actual[group][k]['bytes']!=v['bytes']:raise RuntimeError('MATERIAL_ASSET_CHANGED '+group+'/'+k)
    host=configuration.host(ROOT/'work'/('HOST_OBSERVATION_FAN_'+phase+'.json'))
    if host['os']!=BASELINE['os'] or host['gpu']['values'][:3]!=BASELINE['gpu']['values'][:3] or independent.material(host['GHelper_config_fields'])!=independent.material(BASELINE['GHelper_config_fields']):raise RuntimeError('NON_FAN_MATERIAL_HOST_CHANGED')
    if phase=='B_START':save(STUDY/'FAN_AMENDMENT_B_HOST_BASELINE.json',host)
    save(ROOT/'work'/('FAN_HOST_POLICY_'+phase+'.json'),{'utc':now(),'status':'PASS','fan_only_adjustment_authorized':True,'full_config_file_hash_used_as_material_gate':False,'non_fan_material_settings_equal':True,'asset_bytes_equal':True,'actual_host':host})
    return out

def authorize(task,condition,phase=None,**unused):
    phase=phase or os.environ.get('HS_PHASE')
    if phase not in ['A_LIVE','B_FORMAL']:raise RuntimeError('Fan continuation permits only the unstarted native live/B phases')
    if task not in PROTOCOL['A']['task_ids']:raise RuntimeError('Outside unchanged 19-task cohort')
    if phase=='A_LIVE' and condition!='RTX_BATCHED_K2' or phase=='B_FORMAL' and condition not in PROTOCOL['B']['wire_conditions']:raise RuntimeError('Condition outside unchanged schedule')
    if AUTH['user_authorization_verbatim']!='我调了下风扇转速而已，不影响实验，继续完成吧':raise RuntimeError('Direct fan-only authority missing')
    for name,v in AUTH['preserved_original_files'].items():
        if sha(ROOT/name)!=v['sha256']:raise RuntimeError('Original stop/prefix record changed '+name)
    for checkpoint in ['F0','FAN_AMENDMENT','F2']:
        guards.receipt(checkpoint);guards.check_manifest(checkpoint+'_MANIFEST.json')
    if phase=='B_FORMAL':guards.receipt('B_START');guards.check_manifest('B_START_MANIFEST.json')

def reconstruct(index,output):
    result=ORIGINAL_RECONSTRUCT(index,output);root=package.longpath(Path(output).resolve())/'evidence'
    proc=subprocess.run([sys.executable,'-B',str(root/'metadata/FAN_AMENDMENT_VERIFY.py'),str(root)],capture_output=True)
    out=package.longpath(Path(output).resolve());(out/'fan-amendment.stdout.log').write_bytes(proc.stdout);(out/'fan-amendment.stderr.log').write_bytes(proc.stderr)
    if proc.returncode:raise RuntimeError('Independent fan-amendment archive verification failed: '+proc.stderr.decode(errors='replace'))
    result['independent_fan_amendment']=json.loads(proc.stdout);save(out/'RECONSTRUCTION.json',result);return result

ORIGINAL_RECONSTRUCT=package.reconstruct
package.reconstruct=reconstruct
native_runner.telemetry=observed_telemetry
native_runner.authorize=authorize
guards.authorize=authorize
study.assets=assets

def freeze_amendment():
    independent.check(ROOT);guards.check_manifest('F0_MANIFEST.json')
    files=list(json.loads((STUDY/'F1_MANIFEST.json').read_text(encoding='utf-8'))['files'])
    files+=['benchmarks/rtx_trajectory_cost_v4/'+name for name in ['A_TERMINAL.json','JOINT_BLOCKED.json','F1_MANIFEST.json','F1_REMOTE_RECEIPT.json','F1_GIT_PROOF.json','FAN_AMENDMENT.json','FAN_AMENDMENT_HOST_BASELINE.json','FAN_AMENDMENT_ASSET_OBSERVATION.json','FAN_AMENDMENT_NUMERICAL_PRELIVE.json','FAN_AMENDMENT_EXECUTE.py','FAN_AMENDMENT_VERIFY.py']]
    files+=['work/A-pre-live/records.json']
    # Work records are intentionally ignored by Git. The unchanged manifest is
    # additionally embedded as an explicit additive metadata snapshot.
    files.remove('work/A-pre-live/records.json');shutil.copy2(ROOT/'work/A-pre-live/records.json',STUDY/'FAN_AMENDMENT_ORIGINAL_PRELIVE_RECORDS.json');files+=['benchmarks/rtx_trajectory_cost_v4/FAN_AMENDMENT_ORIGINAL_PRELIVE_RECORDS.json']
    freeze.manifest('FAN_AMENDMENT',files);study.commit('RTX V4: preserve fan-drift stop and freeze explicitly authorized continuation');freeze.receipt('FAN_AMENDMENT')

def live():
    authorize(PROTOCOL['A']['task_ids'][0],'RTX_BATCHED_K2','A_LIVE');assets('A_LIVE')
    rows=study.phase('A-live','A_LIVE',[(t,r,configuration.A[4],'RTX_BATCHED_K2') for t in PROTOCOL['A']['task_ids'] for r in [1,2,3]])
    old=json.loads((ROOT/'work/A-pre-live/records.json').read_text(encoding='utf-8'))['runs'];report=analysis.A_report(old+rows['runs'],PROTOCOL['A']);save(STUDY/'A_trajectory/REPORT.json',report)
    checked=verify_A.full(ROOT)
    for key in ['status','comparisons','reference_divergent_prompts','repeat_stability','candidates']:
        if checked[key]!=report[key]:raise RuntimeError('Independent A result mismatch '+key)
    save(STUDY/'A_trajectory/INDEPENDENT_VALIDATION.json',{'status':'PASS','result':checked,'fan_amendment_authorized':True,'original_pre_live_phase_classification_preserved':True})

def final_scope():
    result=independent.check(ROOT);save(STUDY/'FAN_AMENDMENT_INDEPENDENT_VALIDATION.json',result)
    paper=STUDY/'PAPER_EVIDENCE_DRAFT.md'
    note='\n## Explicit fan-policy amendment\n\nThe 228 predictor observations were captured under the original source/asset freeze but the original strict host-hash policy stopped the stage after an acknowledged fan-curve adjustment. The author explicitly authorized continuation before any native batched live outcome was observed. We preserved the original PROVENANCE_INVALID phase manifest and stop records, independently verified repeated predictor arrays and 57/57 replay pairs, and reused those observations without rerunning or relabeling them. The amended control policy leaves numerical source, assets, schedules, timer boundaries and full-array gates unchanged, permits fan/lighting configuration differences, and retains non-fan material settings as strict identity checks. The complete predictor arrays/tapes and amended authority were frozen and fully retrieved before live execution. This is a disclosed protocol amendment, not completion of the original no-deviation host policy or a fresh independent/unexposed cohort.\n\n'
    note+='Fan controls stayed fixed across the fresh B measurements: '+str(result['B_fan_control_stability'])+'. Fan profiles and device/clock/temperature observations are retained before and after each fresh run. Cost results apply to these recorded settings; fan speed can affect thermal conditions and latency even when numerical outputs remain unchanged.\n'
    if paper.exists():paper.write_text(paper.read_text(encoding='utf-8')+note,encoding='utf-8',newline='\n')
    save(STUDY/'FAN_AMENDMENT_RESULT_SCOPE.json',{'utc':now(),'status':'COMPLETE_UNDER_EXPLICIT_FAN_AMENDMENT','original_no_deviation_protocol_completed':False,'original_stop_reclassified':False,'original_pre_live_model_conditions_reused':228,'fresh_native_A_live_conditions':57,'fresh_B_conditions':171,'fresh_unexposed_cohort_claimed':False,'model_conditions_total':456,'distinct_prompts':19,'B_fan_control_stability':result['B_fan_control_stability'],'paper_scope_disclosed':True,'timing_materiality_note':'Fans can affect thermals/clocks and cost; the observed fan setting is part of the timing scope, never assumed irrelevant to latency.'})

def run():
    out=ROOT/'work/fan-amendment/continuation';out.mkdir(parents=True,exist_ok=False);record={'status':'STARTED','started_utc':now(),'stages':[],'original_pre_live_reused':228,'fresh_unstarted_native_conditions':228};save(out/'records.json',record)
    try:
        for name,fn in [('freeze-amendment',freeze_amendment),('seal-predictions',study.seal_predictions),('A-native-live',live),('B-matched-cost',lambda:study.B_formal(type('Args',(),{'authorization':'EXECUTE_FROZEN','reviewed_sha':AUTH['original_F0']})())),('independent-verification',lambda:__import__('verify_joint').all_reached(ROOT)),('closeout-and-paper',lambda:(closeout.reached(),__import__('paper_evidence').main(),final_scope())),('complete-A-capsules',lambda:package.make('complete','A')),('complete-B-capsules',lambda:package.make('complete','B')),('complete-index',closeout.index)]:
            row={'stage':name,'status':'STARTED','started_utc':now()};record['stages'].append(row);save(out/'records.json',record);print('START',name,flush=True)
            fn();row.update(status='PASS',ended_utc=now());save(out/'records.json',record);print('PASS',name,flush=True)
        record['status']='COMPLETE'
    except Exception as e:record.update(status='STOPPED_PRESERVED_FOR_REVIEW',error=repr(e));raise
    finally:record['ended_utc']=now();save(out/'records.json',record)
if __name__=='__main__':run()
