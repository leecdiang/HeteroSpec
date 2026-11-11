import ast,hashlib,json
from pathlib import Path
from s0_budget import ROOT,save
def main():
    original=Path('D:/hs104-authenticated-final-restore/E1/data/native/source/CMakeLists.txt').read_bytes()
    tree=ast.parse((ROOT/'patch_native.py').read_text(encoding='utf-8'))
    suffix=next(n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.startswith('\nadd_executable(lowering113'))
    data=original+suffix.replace('\n','\r\n').encode();wanted=json.loads((ROOT/'SOURCE_DELTA.json').read_bytes())['files']['CMakeLists.txt']['current'];assert hashlib.sha256(data).hexdigest()==wanted
    p=ROOT/'engineering/FAILED_INITIAL_NATIVE_DELTA_UTF8/CMakeLists.txt';p.write_bytes(data)
    receipt=json.loads((ROOT/'FAILED_SOURCE_RETENTION.json').read_bytes())
    receipt['files'][0]=dict(path='CMakeLists.txt',sha256=wanted,status='EXACT_RECONSTRUCTED_RECORDED_SHA');assert all(r['status']=='EXACT_RECONSTRUCTED_RECORDED_SHA' for r in receipt['files'])
    receipt['status']='ALL_8_INITIAL_FAILED_NATIVE_FILES_EXACT';receipt['method']='original authenticated parent plus retained native delta, verified against each original recorded SHA; original mixed LF/CRLF CMake append preserved'
    save(ROOT/'FAILED_SOURCE_RETENTION_COMPLETE.json',receipt);print(receipt['status'])
if __name__=='__main__':main()
