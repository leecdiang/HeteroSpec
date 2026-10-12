"""Generate a separate independent auditor, keeping the original frozen audit untouched."""
from common95 import *
CODE=Path(__file__).parent
source=(CODE/'audit95.py').read_text(encoding='utf-8')
def replace(old,new):
    global source
    assert source.count(old)==1,(old,source.count(old));source=source.replace(old,new)
replace('import argparse,collections,hashlib,itertools,json,math,statistics,struct','import argparse,collections,hashlib,itertools,json,math,statistics,struct,zipfile')
replace("for phase in ['F0A','F0B']:","for phase in ['F0A','F0B','F0A_V02','F0B_V02']:")
replace("formal_plan=read(pub/'FORMAL_PLAN.json') if (pub/'FORMAL_PLAN.json').exists() else None","formal_plan=read(pub/'FORMAL_PLAN_V02.json') if (pub/'FORMAL_PLAN_V02.json').exists() else (read(pub/'FORMAL_PLAN.json') if (pub/'FORMAL_PLAN.json').exists() else None)")
replace("family=start['family'];assert start['utc']>read(local/('F0B_REMOTE_RECEIPT.json' if events[slot]['phase']=='formal' else 'F0A_REMOTE_RECEIPT.json'))['utc']", "family=start['family'];receipts={read(local/(phase+'_REMOTE_RECEIPT.json'))['commit']:read(local/(phase+'_REMOTE_RECEIPT.json')) for phase in frozen};assert start['freeze_commit'] in receipts and start['utc']>receipts[start['freeze_commit']]['utc']")
replace("build=read(pub/'NATIVE_BUILD.json');model=read(pub/'MODEL_CONTRACT.json')['families'][family]['models']", "build=read(pub/('NATIVE_BUILD_V02.json' if family in ['SmolLM2','Llama'] and r['actual_condition']['layout']=='PQ' else 'NATIVE_BUILD.json'));model=read(pub/'MODEL_CONTRACT.json')['families'][family]['models']")
replace("assert 'F0A' in frozen", """assert 'F0A' in frozen
    old_inventory=read(pub/'NATIVE_SOURCE_HASHES.json');new_inventory=read(pub/'NATIVE_SOURCE_HASHES_V02.json')
    assert set(old_inventory)==set(new_inventory) and [n for n in new_inventory if old_inventory[n]!=new_inventory[n]]==['src/llama-context.cpp']
    with zipfile.ZipFile(local/'SOURCE_RUNTIME.zip') as oz,zipfile.ZipFile(local/'SOURCE_RUNTIME_V02.zip') as nz:
        old_cpp=oz.read('native/source/src/llama-context.cpp').decode();new_cpp=nz.read('native/source/src/llama-context.cpp').decode()
        a=old_cpp.index('uint32_t llama_context::graph_max_nodes(');b=old_cpp.index('\\nllm_graph_result *',a)
        expected=old_cpp[:a]+old_cpp[a:b].replace('    return res;','    // PQ materializes up to four attention subgraphs; reserve metadata capacity only.\\n    return hs_scope::layout95() == 1 ? 4 * res : res;')+old_cpp[b:]
        assert new_cpp==expected,'numerical or undeclared source change'
        assert hashlib.sha256(new_cpp.encode()).hexdigest()==new_inventory['src/llama-context.cpp']
    assert read(pub/'NATIVE_BUILD_V02.json')['numerical_DLL_sha256']==read(pub/'NATIVE_BUILD.json')['numerical_DLL_sha256']
    assert all(a['slots']==b['slots'] and a['condition']==b['condition'] for a,b in zip(read(pub/'FORMAL_PLAN.json')['blocks'],read(pub/'FORMAL_PLAN_V02.json')['blocks']))""")
path=CODE/'audit95_v02.py'
with path.open('x',encoding='utf-8',newline='\n') as f:f.write(source)
save(PUB/'INDEPENDENT_AUDIT_V02_BINDING.json',dict(original_audit_sha256=sha(CODE/'audit95.py'),corrected_audit_sha256=sha(path),derivation_scope=['Validate original and prospective correction seals separately','Resolve receipt by actual recorded freeze commit','Retain all formal coordinates; use amended admissions','Verify PQ-only host graph capacity source delta and unchanged numerical DLLs','Select per-arm compiled source identity, original otherwise'],independent_stdlib_only=True,no_gpu_execution=True))
text=(CODE/'test_audit95.py').read_text(encoding='utf-8').replace('import audit95 as a','import audit95_v02 as a')
tests=CODE/'test_audit95_v02.py'
with tests.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
p=subprocess.run([str(PYTHON),'-m','unittest','discover','-s',str(CODE),'-p','test_audit95_v02.py','-v'],capture_output=True)
(LOCAL/'synthetic-v02.stdout.log').write_bytes(p.stdout);(LOCAL/'synthetic-v02.stderr.log').write_bytes(p.stderr);assert p.returncode==0
save(PUB/'SYNTHETIC_CHECKS_V02.json',dict(utc=now(),status='PASS',tests=14,original_synthetic_checks_unchanged=True,auditor_sha256=sha(path),stdout_sha256=sha(LOCAL/'synthetic-v02.stdout.log'),stderr_sha256=sha(LOCAL/'synthetic-v02.stderr.log')))
