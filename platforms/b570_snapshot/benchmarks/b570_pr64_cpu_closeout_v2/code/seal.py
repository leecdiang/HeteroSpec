"""Deterministic small CPU evidence archive; never embeds original raw/KV/model bulk."""
from evidence import *
import zipfile,io,shutil

def main():
    v=json.loads((OUT/'INDEPENDENT_VERIFICATION.json').read_text());assert v['status']=='PASS'
    event('CPU_SEAL_START')
    write('STATUS.json',dict(state='CPU_AUDIT_COMPLETE',remote_delivery='PENDING_NEW_DRAFT_AND_FRESH_READBACK',new_model_requests=0,new_forward=0,new_warmup=0))
    (OUT/'code').mkdir(exist_ok=True)
    for p in pathlib.Path(__file__).parent.glob('*.py'):shutil.copy2(p,OUT/'code'/p.name)
    (OUT/'dependencies').mkdir(exist_ok=True);shutil.copy2(ROOT/'dependencies/FIXED_SOURCE_READINGS.json',OUT/'dependencies/FIXED_SOURCE_READINGS.json')
    (OUT/'documents').mkdir(exist_ok=True)
    for n in ['README.md','REPORT.zh-CN.md','COST_EXPLANATION.md','PAPER_HANDOFF.md','RELATED_WORK.md','CROSS_PLATFORM_GAPS.md','NEXT_STAGE.md','FIGURE_VISUAL_QA.json','RTX_RAW_ACCESS.json','RUNTIME.json','PROTOCOL.json'] :shutil.copy2(OUT/n,OUT/'documents'/n)
    payload={p.relative_to(OUT).as_posix():p.read_bytes() for p in OUT.rglob('*') if p.is_file() and 'archive' not in p.relative_to(OUT).parts and p.name not in ['CPU_ARCHIVE.json','DELIVERY_RECEIPT.json']}
    ix={n:dict(sha256=digest(b),bytes=len(b)) for n,b in payload.items()};buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n,b in sorted({**payload,'INDEX.json':(json.dumps(ix,sort_keys=True,indent=2)+'\n').encode()}.items()):
            entry=zipfile.ZipInfo(n,date_time=(2026,10,8,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED;z.writestr(entry,b)
    data=buf.getvalue();h=digest(data);folder=OUT/'archive';folder.mkdir(exist_ok=True);(folder/(h+'.zip')).write_bytes(data)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        assert z.testzip() is None
        for n,x in ix.items():assert digest(z.read(n))==x['sha256']
    # This receipt intentionally sits outside the archive whose digest it declares.
    write('CPU_ARCHIVE.json',dict(status='VERIFIED',archive='archive/'+h+'.zip',sha256=h,bytes=len(data),payload_files=len(payload),input_CAS_referenced_not_embedded=CFG['archive_sha256'],models_or_bulk_KV_embedded=False,index=ix,scope='sealed CPU snapshot including code/tables/figures/docs/input hashes; archive receipt and later remote receipt outside snapshot'))
    print('CPU sealed',h,len(data),'bytes',len(payload),'files')
if __name__=='__main__':main()
