"""Read-only raw matrix/vector auditor and compact reproducible CPU archive."""
import collections, hashlib, json, pathlib, struct, sys, zipfile
from common import ROOT, load, save, sha, modules
sys.path.insert(0,str(ROOT))
import plan, evidence

def span(t):return 4+sum((n-1)*b for n,b in zip(t['ne'],t['nb']))

def main():
    before=modules();cells={x['id']:x for x in plan.cpu_cells()};allrows=[];relations=[];sources=[]
    for group,label in [('development','DEVELOPMENT'),('held_after_code_lock','HELD')]:
        root=ROOT/'host_outputs'/group;r=load(ROOT/f'host/S0_{label}_RECEIPT.json');assert r['returncode']==0 and r['completed_fixtures']==216
        assert sha(root/'raw.jsonl')==r['raw_jsonl_sha256'];inputs=load(root/'inputs.json')
        for i in inputs:assert sha(i['input'])==i['input_sha256']
        rows=[x for x in map(json.loads,(root/'raw.jsonl').read_text().splitlines()) if x['event']=='FIXTURE_COMPLETE']
        for row in rows:
            cell=cells[row['id']];g=cell['geometry'];q,h,n,hk=(g[k] for k in ('q','h','n','hk'))
            assert row['modules_unchanged'] and len(row['modes'])==6
            for m in row['modes']:
                name=m['mode'];packed=q>1 and name in ('QH_C','QH_D');wide=q>1 and name in ('QB4','REPEAT4')
                assert m['input_bytes_unchanged']
                for stage in ('QK','softmax','AV','output'):assert m[stage]['nonfinite']==0
                expected_chains=q if q>1 and name=='PQ' else 1;assert len(m['stages'])==expected_chains
                graph=m['graph'];soft=[t for t in graph if t['op']=='SOFT_MAX'];assert len(soft)==expected_chains
                for j in range(q):
                    sm=soft[j if name=='PQ' and q>1 else 0];scores=graph[sm['sources'][0]];mask=graph[sm['sources'][1]]
                    ki=graph[scores['sources'][0]];qi=graph[scores['sources'][1]]
                    assert scores['ne']==[n,q if name=='MQ' or q==1 else 1,h*q if packed else h,q if wide else 1]
                    for head in range(h):
                        rhead=head*q+j if packed else head
                        assert rhead//(scores['ne'][2]//ki['ne'][2])==head//(h//hk)
                        mihead=rhead%mask['ne'][2];mibatch=(j if wide else 0)%mask['ne'][3]
                        col=j if name=='MQ' or q==1 else 0
                        if name!='QH_D' or q==1:
                            actual=mask['view_offset']+col*mask['nb'][1]+mihead*mask['nb'][2]+mibatch*mask['nb'][3]
                            assert actual==4*j*n
                        else:
                            assert mask['op']=='REPEAT' and mask['ne']==[n,1,h*q,1]
                            source=graph[mask['sources'][0]];assert source['ne']==[n,1,q,1] and mihead%q==j
                    for key,part in m['stages'][j if name=='PQ' and q>1 else 0].items():
                        f=root/row['id']/name/part['file'];assert f.stat().st_size==part['tensor']['bytes']
                final=root/row['id']/name/'final.f32';assert final.stat().st_size==4*128*h*q
            base=root/row['id']
            for left,right in [('PQ','QH_C'),('PQ','QH_D'),('QH_C','QH_D'),('MQ','REPEAT4')]:
                rel=evidence.compare_f32(base/left/'final.f32',base/right/'final.f32')
                relations.append(dict(id=row['id'],q=q,left=left,right=right,**rel))
            if q==1:
                for name in ('PQ','QB4','QH_C','QH_D','REPEAT4'):assert (base/'MQ/final.f32').read_bytes()==(base/name/'final.f32').read_bytes()
            allrows.append(row)
    assert len(allrows)==432 and len({r['id'] for r in allrows})==432
    dev=load(ROOT/'host/S0_DEVELOPMENT_RECEIPT.json');held=load(ROOT/'host/S0_HELD_RECEIPT.json');lock=load(ROOT/'host/HOST_RULE_LOCK.json')
    assert dev['exe_sha256']==held['exe_sha256']==lock['executable_sha256']
    metrics=[]
    for name in ('MQ','PQ','QB4','QH_C','QH_D','REPEAT4'):
        for stage in ('QK','softmax','AV','output'):
            ms=[next(m for m in r['modes'] if m['mode']==name)[stage] for r in allrows]
            metrics.append(dict(mode=name,stage=stage,elements=sum(x['elements'] for x in ms),nonfinite=sum(x['nonfinite'] for x in ms),max_abs=max(x['max_abs'] for x in ms),max_ulp=max(x['max_f32_ulp'] for x in ms),witness=max(ms,key=lambda x:x['max_abs'])['max_abs_witness']))
    summary=[]
    for left,right in [('PQ','QH_C'),('PQ','QH_D'),('QH_C','QH_D'),('MQ','REPEAT4')]:
        rs=[r for r in relations if r['left']==left and r['right']==right]
        summary.append(dict(left=left,right=right,cells=len(rs),bitwise_equal=sum(x['bitwise_equal'] for x in rs),max_abs=max(x['max_abs_finite'] for x in rs),max_ulp=max(x['max_ulp_finite'] for x in rs)))
    save(ROOT/'host/S0_FULL_VECTOR_RELATIONS.json',relations)
    save(ROOT/'host/S0_RESULT.json',dict(fixtures=432,geometries=72,graph_computes=2592,development=216,held_fixture_outputs=216,
         independent_unseen_geometry_claim=False,strict_failures=0,nonfinite=0,implementation_revisions=0,metrics=metrics,
         full_vector_summary=summary,exact_address_value_copy_controls=sum(x['address_checks'] for x in allrows),
         CPU_worker_processes=2,owned_wall_s=dev['owned_wall_s']+held['owned_wall_s'],sampled_peak_RSS=max(dev['peak_sampled_RSS'],held['peak_sampled_RSS']),
         new_model_processes=0,new_model_requests=0,GPU_forwards=0,GPU_operators=0,device_queries=0,probes=0,warmups=0,
         cost_scope='CPU wall includes build/compute/scalar audits/raw writes; not Vulkan or paid request speedup',modules_before=before,modules_after=modules()))
    # Archive only the finite new CPU evidence, not old history or models.
    archive=ROOT/'host/S0_RAW.zip';assert not archive.exists();manifest=[]
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for group in ('development','held_after_code_lock'):
            for f in sorted((ROOT/'host_outputs'/group).rglob('*')):
                if not f.is_file():continue
                rel=f.relative_to(ROOT/'host_outputs').as_posix();z.write(f,rel);manifest.append(dict(path=rel,bytes=f.stat().st_size,sha256=sha(f)))
    save(ROOT/'host/S0_RAW_MANIFEST.json',dict(archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,files=manifest))
    with zipfile.ZipFile(archive) as z:
        for row in manifest:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
    save(ROOT/'host/S0_RESTORE_RECEIPT.json',dict(files=len(manifest),all_archived_bytes_rehashed=True,scope='new finite CPU evidence only; no old-history restore',archive_sha256=sha(archive),modules=modules()))
    print(dict(fixtures=432,graphs=2592,relations=summary,archive_bytes=archive.stat().st_size,raw_files=len(manifest)))

if __name__=='__main__':main()
