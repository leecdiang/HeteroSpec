"""Run only the early no-backend/no-model host self-test of bound frontend EXEs."""
from pathlib import Path
import argparse,hashlib,json,subprocess,time

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main(build):
    build=Path(build).resolve();receipt=json.loads((build/'BUILD.json').read_bytes())
    text=(build/'source_snapshot/entry.cpp').read_text(encoding='utf8')
    first=text[text.index('int main(int argc,char**argv){'):]
    anchor='int main(int argc,char**argv){\n    if(argc==2&&std::string(argv[1])=="--selftest")return hs_round1::selftest();'
    if not first.startswith(anchor):
        raise RuntimeError('selftest is not the first branch before backend/model setup')
    if first.index('--selftest-json')>first.index('const auto phase1_main_started'):
        raise RuntimeError('JSON byte selftest is not before native setup')
    out=build/'HOST_SELFTEST.json'
    if out.exists():raise FileExistsError(out)
    records=[]
    for core in ('loop4','packed'):
        exe=Path(receipt['builds'][core]['exe'])
        if sha(exe)!=receipt['builds'][core]['exe_sha256']:raise RuntimeError('build EXE changed')
        fixture=build/core/'selftest-json-bytes.json'
        if fixture.exists():raise FileExistsError(fixture)
        args=[str(exe),'--selftest-json',str(fixture)];start=time.monotonic()
        r=subprocess.run(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=15,creationflags=0x08000000)
        log=build/(core+'-selftest.log');log.write_bytes(r.stdout)
        result=json.loads(r.stdout)
        raw=fixture.read_bytes()
        # Independent file-level checks: real LF formatting and UTF-8 payload,
        # with no Windows text-mode CRLF expansion.
        decoded=json.loads(raw.decode('utf8'))
        fixture_ok=(raw.count(b'\n')>1 and b'\r\n' not in raw and any(b>127 for b in raw)
                    and result.get('multiline_UTF8_JSON_file_checked') is True
                    and result.get('multiline_UTF8_JSON_bytes')==len(raw))
        passed=(r.returncode==0 and result.get('status')=='PASS_HOST_SELFTEST_ONLY' and result.get('models')==0 and result.get('CUDA_calls')==0 and result.get('backend_initializations')==0 and fixture_ok)
        records.append({'core':core,'argv':args,'returncode':r.returncode,'seconds':time.monotonic()-start,'result':result,'exe_sha256':sha(exe),'log_sha256':sha(log),'fixture':{'path':str(fixture),'bytes':len(raw),'sha256':sha(fixture),'LF_count':raw.count(b'\n'),'CRLF_count':raw.count(b'\r\n'),'contains_UTF8_nonASCII':any(b>127 for b in raw),'decoded':decoded},'passed':passed})
    result={'schema':'heterospec.early-frontend-host-selftest.v1','status':'PASS' if all(r['passed'] for r in records) else 'FAIL','build_receipt_sha256':sha(build/'BUILD.json'),'records':records,'native_model_requests':0,'native_rows':0,'GPU_launches':0,'native_numerical_qualification':'NOT_RUN','scope':'early host helper selftests only; no native job arguments passed'}
    out.write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
    if result['status']!='PASS':raise SystemExit(1)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('build');main(p.parse_args().build)
