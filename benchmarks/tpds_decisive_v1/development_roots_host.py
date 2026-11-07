"""Four-root finite qualification; preserve every native failure."""
from native_adapter import *
import qualify_host,dedup_host,traceback
def main():
    os.environ['TPDS_EVIDENCE_CAS']='D:/rtx184-cas'
    for ix in (1,2,3):
        suffix='-root'+str(ix)
        for kind,exe in [('old',OLD/'bin/rtx-scope-transfer.exe'),('observer',ROOT/'draft/reference-observer/bin/rtx-scope-transfer.exe')]:
            label=kind+'-r'+suffix+('-v3' if kind=='old' and ix==1 else '')
            job=draft_job(label,'M',('r0','r1'),ix);job['exe']=str(exe);job['binding']['families']['Qwen']['executable_sha256']=sha(exe)
            template=next(x for x in json.loads((OLD.parent/'admission-Qwen-v4/SLOTS.json').read_bytes()) if x['arm']=='R' and x['source_index']==ix)
            job['slots']=[dict(template,slot_id=r,observer='heavy') for r in ('r0','r1')]
            execute(job)
        paths=[RUNS/(kind+'-r'+suffix+('-v3' if kind=='old' and ix==1 else ''))/'native'/r for kind in ('old','observer') for r in ('r0','r1')]
        vectors=[{p.name:sha(p) for p in (x/'target').glob('*.f32')} for x in paths]
        endpoints=[json.loads(x.with_suffix('.json').read_bytes())['endpoint'] for x in paths]
        assert all(v==vectors[0] for v in vectors) and len(vectors[0])>0
        assert all(v==endpoints[0] for v in endpoints)
        put(ROOT/('BRIDGE'+suffix+'.json'),dict(full_vectors_equal=True,endpoints_equal=True,paths=list(map(str,paths)),vectors=vectors[0]))
        dedup_host.main()
        for arm in ('D1','D2','D4','M'):
            try:
                execute(draft_job('development-v3-'+arm+suffix,arm,('heavy','warmup','off'),ix));qualify_host.main(arm,ix)
            except Exception as e:
                put(ROOT/('DEVELOPMENT_FAILURE-'+arm+suffix+'.json'),dict(error=repr(e),traceback=traceback.format_exc(),no_main_claim=True));raise
            dedup_host.main()
if __name__=='__main__':main()
