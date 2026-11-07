"""Restore authenticated historical material into a new directory; no inference."""
import argparse, hashlib, json, pathlib, shutil, subprocess, time, zipfile
P=pathlib.Path
def sha(p):
    with P(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(P(p).read_bytes())
def save(p,d):P(p).write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('out',type=P);a=ap.parse_args();root=a.out.resolve();root.mkdir(exist_ok=False)
    records=[]
    for label,name,expected in [('original','SOURCE_RUNTIME.zip','62086688fc095be2654ae25aad2c7780c94db8617db5a6a9f71504f49897bf7e'),('metadata4','SOURCE_RUNTIME_V02.zip','36be0d738ad5d29579b75825f68337003eb127405cc5418abc566cb07718a4d8')]:
        src=P('D:/hsc95')/name;assert sha(src)==expected
        dest=root/label;dest.mkdir()
        with zipfile.ZipFile(src) as z:
            index=json.loads(z.read('INDEX.json'))['files']
            for name,v in index.items():
                p=(dest/name).resolve();assert p.is_relative_to(dest)
                data=z.read(name);assert len(data)==v['bytes'] and hashlib.sha256(data).hexdigest()==v['sha256']
                p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);assert sha(p)==v['sha256']
            (dest/'INDEX.json').write_bytes(z.read('INDEX.json'))
        records.append(dict(label=label,archive=str(src),sha256=expected,verified_files=len(index)))
        print('RESTORED',label,len(index),flush=True)
    build=read('D:/hs-qb-confirmation-v02/NATIVE_BUILD.json');dllsource=P('D:/hs-qb-confirmation-v02/native/build/bin')
    for name,h in build['numerical_DLL_sha256'].items():
        assert sha(dllsource/name)==h
        for label in ('original','metadata4'):
            dest=root/label/'native/bin'/name;shutil.copyfile(dllsource/name,dest);assert sha(dest)==h
    contract=read('D:/hs-qb-confirmation-v02/MODEL_CONTRACT.json')
    for item in contract['families']['Qwen']['models'].values():assert P(item['path']).stat().st_size==item['bytes'] and sha(item['path'])==item['sha256']
    save(root/'MODEL_CONTRACT.json',contract)
    panel=read('D:/hs-qb-confirmation-v02/PLAN.json')['panel']['Qwen'];save(root/'PANEL.json',{'inputs':panel})
    e1=P('D:/hs104-authenticated-final-restore/E1/data');registry=read(e1/'snapshot_registry/002.json');snap=e1/P(registry['root']).relative_to(P('D:/hs104-e1-v1'))
    fixture=root/'stage-fixture';fixture.mkdir()
    for name,h in registry['registry'].items():
        assert sha(snap/name)==h;shutil.copyfile(snap/name,fixture/name);assert sha(fixture/name)==h
    save(root/'STAGE_ORIGIN.json',registry)
    save(root/'RECOVERY.json',dict(status='PASS_FILE_IDENTITY_ONLY',archives=records,numerical_dlls=build['numerical_DLL_sha256'],models=contract['families']['Qwen']['models'],stage_coordinate='Qwen_l00_prefill_q3',native_requests=0))
    print('RECOVERY_PASS',root,flush=True)
if __name__=='__main__':main()
