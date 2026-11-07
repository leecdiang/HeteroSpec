"""Exact CPU capsule publication / authenticated remote restore, no GPU commands."""
import argparse,datetime,hashlib,json,subprocess,time,zipfile
from pathlib import Path
from common import V,load,save,sha,pin,env
from lifecycle import Child
from transport_lifecycle import TransportChild
import publication as P

REL='benchmarks/rtx_lowering_envelope_v1/s1b_monitor_repair_v2'

def settled_files():
    rows=[p for p in V.iterdir() if p.is_file() and p.name!='CPU_JOB.lock']
    for folder in ['cpu_raw','preparation_candidates','ledger']:
        for p in (V/folder).rglob('*'):
            if not p.is_file() or '__pycache__' in p.parts:continue
            if folder=='cpu_raw' and any(x in p.relative_to(V/folder).parts for x in ['publication','publication_final']):continue
            if folder=='ledger' and not any(q.name.startswith(p.name[:3]+'-') for q in (V/folder).glob('*-EXIT.json')):continue
            rows.append(p)
    return sorted(set(rows))

def package(f):
    d=V/'delivery/cpu-final';d.mkdir(parents=True,exist_ok=False)
    members={};sources=[(p,'frozen/'+p.relative_to(V).as_posix()) for p in settled_files()]
    sources += [(Path(f['execution_bound_census']['path']),'evidence/CENSUS.json'),(Path(f['execution_bound_decision']['path']),'evidence/DECISION.json'),(V.parent/'s1b_cost_v1/CPU_GRAPHS_FINAL2.json','evidence/ORIGINAL_CPU_GRAPHS.json')]
    part=d/'raw-000.zip.part'
    with zipfile.ZipFile(part,'x',zipfile.ZIP_DEFLATED) as z:
        for p,n in sources:
            assert not p.is_symlink() and n not in members
            members[n]=dict(bytes=p.stat().st_size,sha256=sha(p));z.write(p,n)
        z.writestr('MANIFEST.json',json.dumps(members,separators=(',',':'))+'\n')
    assert part.stat().st_size<40*1024**2
    m=dict(schema=2,run_id=f['run_id'],execution_id=f['execution_id'],F0_sha256=sha(V/'F0.json'),members=members,member_count=len(members),member_bytes=sum(r['bytes'] for r in members.values()),archive_bytes=part.stat().st_size,archive_sha256=sha(part),parts=[dict(name=part.name,bytes=part.stat().st_size,sha256=sha(part))],GPU_queries=0,CUDA_loads=0,graph_calls=0)
    save(d/'ARCHIVE_MANIFEST.json',m);P.validate_archive(d,m)
    save(V/'CPU_CAPSULE_PACKAGED.json',dict(run_id=f['run_id'],execution_id=f['execution_id'],archive_manifest=pin(d/'ARCHIVE_MANIFEST.json'),archive=pin(part),member_count=len(members),member_bytes=m['member_bytes'],authenticated_remote_bytes=False))
    print('CPU capsule',len(members),'members',part.stat().st_size,'bytes;manifest',sha(d/'ARCHIVE_MANIFEST.json'))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--action',required=True,choices=['package','stage-push','readback','closure-push']);ap.add_argument('--commit');a=ap.parse_args()
    f=load(V/'F0.json');root=V/'cpu_raw/publication_final'/a.action;root.mkdir(parents=True,exist_ok=False);begin=time.monotonic_ns();commands=[];error=None
    save(root/'START.json',dict(run_id=f['run_id'],execution_id=f['execution_id'],action=a.action,monotonic_ns=begin,CPU_only=True))
    w=TransportChild(f['console_helper'],f['CPU_transport_executables']) if a.action.endswith('push') else Child(f['console_helper'])
    def run(cmd,name,cap=32768):
        prefix=root/name;save(prefix.with_suffix('.COMMAND.json'),dict(command=cmd,run_id=f['run_id'],execution_id=f['execution_id'],CPU_only=True));e=env('');e['GODEBUG']='http2client=0'
        w.run(cmd,prefix,120,e,512*1024**2,log_cap=cap);commands.append(dict(prefix=str(prefix),command=cmd));return prefix.with_suffix('.stdout')
    try:
        if a.action=='package':package(f)
        elif a.action.endswith('push'):
            repo=Path(f['repository']);assert subprocess.check_output([f['git']['path'],'branch','--show-current'],cwd=repo).decode().strip()==f['branch']
            # All large CPU fixtures are carried losslessly in the exact capsule.
            selected=[p for p in V.iterdir() if p.is_file() and p.name!='CPU_JOB.lock']
            selected += [p for sub in ['delivery/cpu-final','preparation_candidates','ledger'] for p in (V/sub).rglob('*') if p.is_file()]
            rows=P.stage_exact(repo,selected)
            staged=subprocess.check_output([f['git']['path'],'diff','--cached','--name-only'],cwd=repo).decode().splitlines();assert staged and all(n.startswith(REL+'/') for n in staged)
            run([f['git']['path'],'-C',str(repo),'commit','-m','PR118: '+('freeze canonical identity and actual interval CPU repair r2' if a.action=='stage-push' else 'authenticate r2 CPU capsule and fresh replay;GPU remains unstarted')],'commit')
            commit=subprocess.check_output([f['git']['path'],'-C',str(repo),'rev-parse','HEAD']).decode().strip();P.tree_exact(repo,commit,rows)
            save(root/'COMMIT_TREE_EXACT.json',dict(commit=commit,files=rows,all_exact=True))
            run([f['git']['path'],'-C',str(repo),'push','origin',f['branch']],'push')
            print('PUSHED',commit)
        else:
            assert a.commit and len(a.commit)==40 and all(c in '0123456789abcdef' for c in a.commit)
            download=root/'download';download.mkdir();files=['delivery/cpu-final/ARCHIVE_MANIFEST.json','delivery/cpu-final/raw-000.zip.part','F0.json','run_s1b.py','monitor_contract.py','strict_lifecycle.py','monitor_worker.py','monitor_audit.py']
            remote=[]
            for i,name in enumerate(files):
                cmd=[f['gh']['path'],'api','repos/leecdiang/HeteroSpec/contents/'+REL+'/'+name+'?ref='+a.commit,'-H','Accept: application/vnd.github.raw','-H','Accept-Encoding: identity']
                output=run(cmd,str(i),40*1024**2);assert output.read_bytes()==(V/name).read_bytes(),name
                dst=download/Path(name).name;dst.write_bytes(output.read_bytes());remote.append(dict(path=name,bytes=dst.stat().st_size,sha256=sha(dst)))
            manifest=load(download/'ARCHIVE_MANIFEST.json');fresh=Path('D:/hs116-s1b-exact-r2-cpu-final-fresh');assert not fresh.exists()
            proof=P.validate_archive(download,manifest,fresh)
            run([f['python']['path'],'-B',str(fresh/'frozen/fresh_check.py'),'--out',str(V/'FRESH_CPU_AUDIT.json'),'--F0-sha256',sha(V/'F0.json')],'fresh-replay')
            audit=load(V/'FRESH_CPU_AUDIT.json');assert audit['status']=='PASS'
            save(V/'REMOTE_F0_BYTES.json',load(download/'F0.json')) if False else (V/'REMOTE_F0_BYTES.json').open('xb').write((download/'F0.json').read_bytes())
            save(V/'AUTHENTICATED_F0.json',dict(authenticated_remote_bytes=True,run_id=f['run_id'],execution_id=f['execution_id'],commit=a.commit,sha256=sha(V/'F0.json'),author_GPU_approval=False))
            save(V/'CENSUS_EXACT_AUTHENTICATED.json',dict(authenticated_remote_bytes=True,run_id=f['run_id'],execution_id=f['execution_id'],commit=a.commit,execution_bound_path=f['execution_bound_census']['path'],execution_bound_sha256=sha(fresh/'evidence/CENSUS.json'),execution_bound_bytes=(fresh/'evidence/CENSUS.json').stat().st_size,remote_archive_sha256=manifest['archive_sha256'],manifest_sha256=sha(download/'ARCHIVE_MANIFEST.json'),JSON_normalization_used_for_binding=False))
            save(V/'REMOTE_ARCHIVE_VERIFIED.json',dict(status='VERIFIED',run_id=f['run_id'],execution_id=f['execution_id'],authenticated_remote_bytes=True,commit=a.commit,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),remote_files=remote,manifest_sha256=sha(download/'ARCHIVE_MANIFEST.json'),fresh_root=str(fresh),enumeration=proof,fresh_CPU_audit=pin(V/'FRESH_CPU_AUDIT.json'),not_a_local_only_restore=True,new_GPU_queries=0,CUDA_loads=0,graph_calls=0))
            print('VERIFIED remote bytes,all members,fresh interpreter audit;GPU0')
    except BaseException as e:
        error=repr(e);save(root/'FAILED.json',dict(error=error,CPU_only=True,scientific_retry=False));raise
    finally:
        w.terminate();seconds=(time.monotonic_ns()-begin)/1e9
        save(root/'ENDED.json',dict(run_id=f['run_id'],execution_id=f['execution_id'],seconds=seconds,conservative_owned_seconds=seconds*(17 if a.action.endswith('push') else 3),error=error,commands=commands,CPU_only=True,GPU_queries=0,CUDA_loads=0,graph_calls=0))
if __name__=='__main__':main()
