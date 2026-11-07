"""Future CPU-only census sealing/readback, never launches the next GPU stage.

Use --seal after the separately approved census ends. Commit/push its payload,
then --readback COMMIT authenticates those exact bytes and records the handoff.
Numerics still requires a new human approval bound to the census/decision SHA.
"""
import argparse,hashlib,subprocess,urllib.request,zipfile
from pathlib import Path
from common import V,load,save,sha
import analyzer
def main():
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group(required=True);g.add_argument('--seal',action='store_true');g.add_argument('--readback');a=ap.parse_args()
    f0=load(V/'F0.json');root=Path(f0['execution_root']);d=V/'census_delivery'
    if a.seal:
        assert (root/'CENSUS_ENDED.json').exists() and load(root/'CENSUS_ENDED.json')['error'] is None
        assert (root/'CENSUS_SUCCESS.json').exists();d.mkdir(exist_ok=False);members=[]
        paths=list((root/'census').rglob('*'))+[p for p in root.glob('CENSUS_*.json')]
        with zipfile.ZipFile(d/'CENSUS_RAW.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
            for p in sorted(set(paths)):
                if p.is_file():
                    name=p.relative_to(root).as_posix();z.write(p,name);members.append(dict(path=name,bytes=p.stat().st_size,sha256=sha(p)))
        assert (d/'CENSUS_RAW.zip').stat().st_size<=16*1024**2
        save(d/'MANIFEST.json',dict(sha256=sha(d/'CENSUS_RAW.zip'),bytes=(d/'CENSUS_RAW.zip').stat().st_size,members=members,F0_sha256=sha(V/'F0.json'),GPU_graph_calls=0))
        print('Census sealed; push payload, authenticate readback, then wait for numerical approval');return
    token=subprocess.check_output(['gh','auth','token']).decode().strip();received={}
    target=V/'census_readback';target.mkdir(exist_ok=False)
    for name in ('CENSUS_RAW.zip','MANIFEST.json'):
        url='https://api.github.com/repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_lowering_envelope_v1/formal_numerical_v2/census_delivery/'+name+'?ref='+a.readback
        req=urllib.request.Request(url,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github.raw+json','Accept-Encoding':'identity','User-Agent':'HeteroSpec-census-handoff'})
        with urllib.request.urlopen(req,timeout=45) as r:assert r.status==200;data=r.read()
        with (target/name).open('xb') as out:out.write(data)
        assert sha(target/name)==sha(d/name);received[name]=data
    manifest=load(target/'MANIFEST.json');assert sha(target/'CENSUS_RAW.zip')==manifest['sha256']
    with zipfile.ZipFile(target/'CENSUS_RAW.zip') as z:
        assert set(z.namelist())=={m['path'] for m in manifest['members']}
        for m in manifest['members']:assert hashlib.sha256(z.read(m['path'])).hexdigest()==m['sha256']
        import json
        census=json.loads(z.read('census/native/CENSUS.json'));decision=json.loads(z.read('CENSUS_DECISION.json'))
    expected={(r['descriptor_id'],r['layout']):r for r in load(V/'CPU_GRAPH_EXPECTED.json')}
    assert analyzer.census_decision(census,expected,load(V/'PLAN.json'))==decision
    save(root/'CENSUS_AUTHENTICATED.json',dict(authenticated_remote_bytes=True,data_commit=a.readback,F0_sha256=sha(V/'F0.json'),
        census_sha256=sha(root/'census/native/CENSUS.json'),decision_sha256=sha(root/'CENSUS_DECISION.json'),primary_QH='QH_C',numerical_admitted=decision['numerical_admitted'],numerical_authorization='NOT_GRANTED'))
    print('Census bytes and decision reconstructed; numerical stage still awaits separate human confirmation')
if __name__=='__main__':main()
