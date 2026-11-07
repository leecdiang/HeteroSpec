"""Offline PE export-RVA checks against every retained process's actual core IAT."""
import argparse,os,struct
from pathlib import Path
from common import load,save,sha
from prepare_rtx import root
def exports(path):
    b=Path(path).read_bytes();u16=lambda x:struct.unpack_from('<H',b,x)[0];u32=lambda x:struct.unpack_from('<I',b,x)[0]
    assert b[:2]==b'MZ';nt=u32(0x3c);assert b[nt:nt+4]==b'PE\0\0';n=u16(nt+6);opt=nt+24;assert u16(opt)==0x20b;section=opt+u16(nt+20)
    rows=[(u32(section+i*40+12),u32(section+i*40+8),u32(section+i*40+20),u32(section+i*40+16)) for i in range(n)]
    def off(rva):
        for va,vs,ptr,size in rows:
            if va<=rva<va+max(vs,size):return ptr+rva-va
        raise ValueError('RVA absent')
    expRVA=u32(opt+112);e=off(expRVA);functions=off(u32(e+28));names=off(u32(e+32));ordinals=off(u32(e+36));out={}
    for i in range(u32(e+24)):
        start=off(u32(names+4*i));end=b.index(b'\0',start);name=b[start:end].decode('ascii');rva=u32(functions+4*u16(ordinals+2*i));out[name]=rva
    return dict(image_size=u32(opt+56),symbols=out,sha256=sha(path))
def verify_record(rec,expected_path,pe):
    same=lambda a,b:os.path.normcase(str(Path(a).resolve()))==os.path.normcase(str(Path(b).resolve()))
    core=rec['core'];assert same(core['path'],expected_path) and core['sha256']==pe['sha256'] and core['ready'];base=core['module_handle'];assert base>0
    for name,fn in core['functions'].items():
        assert name in pe['symbols'] and fn['address']==base+pe['symbols'][name] and fn['RVA']==pe['symbols'][name] and same(fn['owner_path'],expected_path),'core export address'
    host=rec['host_core_IAT'];assert host['symbol']=='ggml_init' and host['IAT_target']==base+pe['symbols']['ggml_init'] and same(host['owner_path'],expected_path) and host['module_handle']==base,'host shared IAT'
    imports=rec['plugin_core_IAT'];assert len(imports)==41 and len({x['symbol'] for x in imports})==41
    for fn in imports:assert same(fn['owner_path'],expected_path) and fn['symbol'] in pe['symbols'] and fn['target']==base+pe['symbols'][fn['symbol']],'actual plugin core IAT export RVA mismatch'
    assert core['events'].count('dll_initializer_returned')==1 and 'rejected_use_before_dll_init' not in core['events'],'process init'
def main(out):
    r=root();s=load(r/'RUN_SPEC.json');runtime=Path(s['runtime_directory']);actual={name:sha(runtime/name) for name in s['numerical_DLLs']};assert actual==s['numerical_DLLs'];pe=exports(runtime/'ggml-base.dll');count=0
    for p in (r/'attempts').glob('*/native/RECORD.json'):verify_record(load(p),runtime/'ggml-base.dll',pe);count+=1
    # Deterministic negatives mutate a copied record, not DLL memory or history.
    import copy
    sample=load(next((r/'attempts').glob('*/native/RECORD.json')));rejected=[]
    for kind in ['target','owner','host','initializer']:
        bad=copy.deepcopy(sample)
        if kind=='target':bad['plugin_core_IAT'][0]['target']+=1
        if kind=='owner':bad['plugin_core_IAT'][0]['owner_path']='D:/wrong/ggml-base.dll'
        if kind=='host':bad['host_core_IAT']['IAT_target']+=1
        if kind=='initializer':bad['core']['events'].append('dll_initializer_returned')
        try:verify_record(bad,runtime/'ggml-base.dll',pe)
        except AssertionError:rejected.append(kind)
        else:raise AssertionError('bad identity accepted')
    save(out,dict(status='PASS',process_records=count,plugin_IAT_exports_checked=count*41,core_PE_sha256=pe['sha256'],all21_numerical_DLLs=actual,negative_tests=rejected,GPU_loads=0,method='raw core base plus exact frozen PE export RVA equals every actual IAT target;exact owner path and process-once initialization',scope='offline audit of retained actual process receipts;no live process inspection or GPU re-execution'))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();main(a.out)
