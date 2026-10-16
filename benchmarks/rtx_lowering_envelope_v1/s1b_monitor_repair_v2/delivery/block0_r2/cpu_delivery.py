"""Post-stop CPU-only closure using unchanged frozen inspectors and archive tools."""
import argparse,datetime,json,os,re,shutil,subprocess,sys,time,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from common import V,load,save,sha,env
from bounded import State,Deadline,durable
from lifecycle import Child,process_commit
from transport_lifecycle import TransportChild
from admission import owned_conflicts
import publication as P

OUT=Path(__file__).resolve().parent
REL='benchmarks/rtx_lowering_envelope_v1/s1b_monitor_repair_v2'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',required=True,choices=['forensic','package','push-data','readback','restore','recompute','push-closure','verify-closure','remote-head','publish-api','report','multipart']);ap.add_argument('--commit');a=ap.parse_args()
    f=load(V/'F0.json');root=Path(f['execution_root']);budget=f['budget']['offline_CPU_delivery'];assert load(root/'CLEAN0_ENDED.json')['status']=='INCOMPLETE_STOPPED';owned_conflicts(f)
    ledger=OUT/'cpu_ledger';ledger.mkdir(exist_ok=True)
    prior=list(ledger.iterdir())+list((V/'delivery/cpu_ledger').iterdir())
    assert all((p/'CPU_ENDED.json').exists() for p in prior),'unresolved CPU action;no overwrite'
    wall=sum(load(p/'CPU_ENDED.json')['seconds'] for p in prior);spent=sum(load(p/'CPU_ENDED.json')['conservative_owned_seconds'] for p in prior)
    factor=17 if a.phase.startswith('push-') or a.phase in ['multipart','publish-api'] else 3
    remaining=min(budget['wall_seconds']-wall,(budget['conservative_owned_seconds']-spent)/factor);assert remaining>15
    d=ledger/f'{len(list(ledger.iterdir())):02d}-{a.phase}';d.mkdir();begin=time.perf_counter()
    class CPUState(State):
        def snapshot(self,status):
            r=super().snapshot(status);r.update(run_id=f['run_id'],execution_id=f['execution_id'],conservative_owned_seconds=factor*r['seconds'],process_bound_multiplier=factor);return r
    state=CPUState(d,'CPU');state.start=begin;w=TransportChild(f['console_helper'],f['CPU_transport_executables']) if factor==17 else Child(f['console_helper']);error=None
    def monitor():state.peak_commit=max(state.peak_commit,process_commit());assert state.peak_commit<=budget['controller_commit']
    deadline=Deadline(state,remaining,w.terminate,grace=5,monitor=monitor).start()
    def run(cmd,name,cap=32768):
        prefix=d/name;durable(prefix.with_suffix('.COMMAND.json'),dict(command=cmd,CPU_only=True,run_id=f['run_id'],execution_id=f['execution_id']))
        e=env('');e['GODEBUG']='http2client=0';e.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='http.version',GIT_CONFIG_VALUE_0='HTTP/1.1')
        w.run(cmd,prefix,min(300,deadline.remaining()-5),e,budget['job_commit'],deadline.guard,log_cap=cap);return prefix.with_suffix('.stdout')
    def fetch(name,prefix,cap=40*1024**2):
        assert a.commit and re.fullmatch('[0-9a-f]{40}',a.commit)
        p=run([f['gh']['path'],'api','repos/leecdiang/HeteroSpec/contents/'+REL+'/'+name+'?ref='+a.commit,'-H','Accept: application/vnd.github.raw','-H','Accept-Encoding: identity'],prefix,cap)
        assert p.read_bytes()==(V/name).read_bytes(),'remote exact bytes mismatch';return p
    layout=load(OUT/'TRANSPORT_LAYOUT.json') if (OUT/'TRANSPORT_LAYOUT.json').exists() else dict(active_archive_directory='raw',manifest='RAW_MANIFEST.json')
    try:
        if a.phase=='forensic':
            run([f['python']['path'],'-B',str(OUT/'forensic_block0.py'),'--root',str(root),'--frozen',str(V),'--out',str(OUT/'FORENSIC.json')],'forensic')
            run([f['python']['path'],'-B',str(V/'run_s1b.py'),'--dry-check'],'post-stop-freeze-check')
            shutil.copyfile(V/'delivery/ANALYSIS.json',OUT/'ANALYSIS.json')
            save(OUT/'POST_STOP_IDENTITY.json',dict(F0_sha256=sha(V/'F0.json'),all_frozen_files_unchanged=True,owned_native_conflicts=False,new_GPU_queries=0))
        elif a.phase=='package':
            original={p.relative_to(root).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in root.rglob('*') if p.is_file()}
            save(OUT/'ORIGINAL_RAW_INVENTORY.json',original)
            context=root/'CPU_SEAL_CONTEXT';context.mkdir(exist_ok=False)
            for p in (V/'authorizations/clean0_r2').iterdir():
                if p.is_file():shutil.copyfile(p,context/p.name)
            for name in ['forensic_block0.py','FORENSIC.json','ANALYSIS.json','ORIGINAL_RAW_INVENTORY.json','POST_STOP_IDENTITY.json']:shutil.copyfile(OUT/name,context/name)
            save(context/'CPU_ONLY_SEAL.json',dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),GPU_stage_already_ended=True,original_files_not_modified=True,no_after_input_or_module_record_fabricated=True))
            for name,row in original.items():assert sha(root/name)==row['sha256']
            run([f['python']['path'],'-B',str(V/'evidence_s1b.py'),'--action','package','--root',str(root),'--out',str(OUT/'raw')],'package')
            import archive
            desc=load(OUT/'raw/ARCHIVE.json');reader=archive.PartsReader(OUT/'raw',desc['parts'])
            with zipfile.ZipFile(reader) as z:members=json.loads(z.read('MANIFEST.json'));assert set(z.namelist())==set(members)|{'MANIFEST.json'}
            save(OUT/'RAW_MANIFEST.json',dict(run_id=f['run_id'],execution_id=f['execution_id'],F0_sha256=sha(V/'F0.json'),archive=desc,members=members,member_count=len(members),member_bytes=sum(r['bytes'] for r in members.values()),all_original_raw_members_included=all('raw/'+n in members for n in original)))
        elif a.phase.startswith('push-'):
            repo=Path(f['repository']);paths=[]
            for folder in [OUT,V/'authorizations/clean0_r2',V/'execution_ledger',V/'delivery/cpu_ledger']:
                for p in folder.rglob('*'):
                    if p.is_file() and d not in p.parents and '__pycache__' not in p.parts:
                        if p==OUT/'raw/raw-000.zip.part' and layout['active_archive_directory']!='raw':continue
                        if OUT/'cpu_ledger' in p.parents:continue
                        paths.append(p)
            rows=P.stage_exact(repo,sorted(set(paths)));cached=subprocess.check_output([f['git']['path'],'-C',str(repo),'diff','--cached','--name-only']).decode().splitlines();assert cached and all(n.startswith(REL+'/') for n in cached)
            run([f['git']['path'],'-C',str(repo),'commit','-m','PR118: seal r2 Block0 ordinary-output stop;no retry'],'commit')
            commit=subprocess.check_output([f['git']['path'],'-C',str(repo),'rev-parse','HEAD']).decode().strip();P.tree_exact(repo,commit,rows)
            save(d/'COMMITTED_TREE_EXACT.json',dict(commit=commit,all_staged_files_exact=True,files=rows))
            run([f['git']['path'],'-C',str(repo),'push','origin',f['branch']],'push');print('PUSHED',commit)
        elif a.phase=='readback':
            download=OUT/'download';download.mkdir(exist_ok=False);descriptor=fetch('delivery/block0_r2/'+layout['active_archive_directory']+'/ARCHIVE.json','descriptor');shutil.copyfile(descriptor,download/'ARCHIVE.json');desc=load(descriptor);remote=[]
            for i,part in enumerate(desc['parts']):
                assert re.fullmatch(r'raw-\d{3}\.zip\.part',part['name'])
                p=fetch('delivery/block0_r2/'+layout['active_archive_directory']+'/'+part['name'],'part'+str(i));target=download/part['name'];p.rename(target);assert sha(target)==part['sha256'];remote.append(part)
                if layout['active_archive_directory']=='raw_api':
                    source=OUT/'raw_api'/part['name'];assert source.parent==OUT/'raw_api' and sha(source)==part['sha256'];source.unlink();os.link(target,source)
            for i,name in enumerate([layout['manifest'],'FORENSIC.json','ANALYSIS.json']):fetch('delivery/block0_r2/'+name,'metadata'+str(i))
            save(OUT/'RAW_REMOTE_AUTHENTICATED.json',dict(authenticated_remote_bytes=True,commit=a.commit,run_id=f['run_id'],execution_id=f['execution_id'],F0_sha256=sha(V/'F0.json'),archive_sha256=desc['sha256'],remote_parts=remote,manifest_sha256=sha(OUT/layout['manifest']),successful_remote_fragment_copies_hardlinked_for_physical_dedup=layout['active_archive_directory']=='raw_api'))
        elif a.phase=='restore':
            fresh=Path(f['fresh_restore_root']);assert not fresh.exists()
            run([f['python']['path'],'-B',str(V/'evidence_s1b.py'),'--action','restore','--archive',str(OUT/'download'),'--out',str(fresh)],'restore')
            manifest=load(OUT/layout['manifest'])['members'];actual={p.relative_to(fresh).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in fresh.rglob('*') if p.is_file() and p.name!='MANIFEST.json'};assert actual==manifest
            save(OUT/'FRESH_ENUMERATION.json',dict(status='PASS',fresh_root=str(fresh),members=len(actual),bytes=sum(x['bytes'] for x in actual.values()),all_members_exact=True))
        elif a.phase=='recompute':
            fresh=Path(f['fresh_restore_root']);run([f['python']['path'],'-B',str(fresh/'frozen/evidence_s1b.py'),'--action','analyze','--root',str(fresh/'raw'),'--out',str(OUT/'FRESH_ANALYSIS.json')],'frozen-analysis')
            run([f['python']['path'],'-B',str(fresh/'raw/CPU_SEAL_CONTEXT/forensic_block0.py'),'--root',str(fresh/'raw'),'--frozen',str(fresh/'frozen'),'--out',str(OUT/'FRESH_FORENSIC.json')],'forensic-replay')
            assert (OUT/'FRESH_ANALYSIS.json').read_bytes()==(OUT/'ANALYSIS.json').read_bytes();assert (OUT/'FRESH_FORENSIC.json').read_bytes()==(OUT/'FORENSIC.json').read_bytes()
            save(OUT/'FRESH_RECOMPUTE_VERIFIED.json',dict(status='VERIFIED',fresh_interpreter=True,all_frozen_analysis_bytes_equal=True,all_forensic_description_bytes_equal=True,archive_SHA256=load(OUT/'RAW_REMOTE_AUTHENTICATED.json')['archive_sha256'],remote_commit=load(OUT/'RAW_REMOTE_AUTHENTICATED.json')['commit'],GPU_queries=0,graph_calls=0))
        elif a.phase=='remote-head':
            p=run([f['gh']['path'],'pr','view','118','--repo','leecdiang/HeteroSpec','--json','headRefOid,isDraft,headRefName'],'PR');save(d/'REMOTE_HEAD.json',load(p));print(p.read_text())
        elif a.phase=='publish-api':
            import publish_git_api
            publish_git_api.publish(f,d,run)
        elif a.phase=='report':
            run([f['python']['path'],'-B',str(OUT/'build_result.py')],'report')
        elif a.phase=='multipart':
            import prepare_multipart
            prepare_multipart.prepare(f,OUT,d)
        else:
            for i,name in enumerate(['RESULT.md','RESULT.json','FRESH_RECOMPUTE_VERIFIED.json','RAW_MANIFEST.json']):fetch('delivery/block0_r2/'+name,'result'+str(i))
            p=run([f['gh']['path'],'pr','view','118','--repo','leecdiang/HeteroSpec','--json','headRefOid,isDraft,headRefName'],'PR');pr=load(p);assert pr['headRefOid']==a.commit and pr['isDraft']
            save(OUT/'RESULT_REMOTE_VERIFIED.json',dict(status='VERIFIED',commit=a.commit,PR=pr,result_sha256=sha(OUT/'RESULT.json'),F0_sha256=sha(V/'F0.json'),archive_sha256=load(OUT/'raw/ARCHIVE.json')['sha256'],new_GPU_activity=False))
    except BaseException as exc:error=repr(exc);state.minimum_stop(error);w.terminate();raise
    finally:w.terminate();state.reason=error;state.finish('COMPLETE' if error is None else 'CPU_DELIVERY_FAILED');deadline.close()
if __name__=='__main__':main()
