"""Read-only historical/environment audit. Never imports a model runner."""
from pathlib import Path
import datetime, hashlib, json, os, shutil, sqlite3, struct, subprocess, time

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
OLD = WORK.parent

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(8 * 1024**2), b''):
            h.update(b)
    return h.hexdigest()

def read(path):
    return json.loads(Path(path).read_bytes())

def put(name, value):
    with (HERE / name).open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)

def ident(path, expected=None):
    p = Path(path)
    if not p.is_file():
        return dict(path=str(p), exists=False)
    actual = sha(p)
    return dict(path=str(p), exists=True, bytes=p.stat().st_size, sha256=actual,
                expected=expected, matches=None if expected is None else actual == expected)

def command(args):
    t = time.monotonic()
    try:
        r = subprocess.run(args, capture_output=True, timeout=30)
        return dict(argv=list(map(str,args)), code=r.returncode, seconds=time.monotonic()-t,
                    stdout=r.stdout.decode('utf8','replace'), stderr=r.stderr.decode('utf8','replace'))
    except Exception as exc:
        return dict(argv=list(map(str,args)), error=repr(exc), seconds=time.monotonic()-t)

class GGUF:
    """Metadata only; reads no tensors and never initializes an inference backend."""
    formats = {0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
    def __init__(self, stream): self.f=stream
    def unpack(self, fmt):
        n=struct.calcsize('<'+fmt); raw=self.f.read(n)
        if len(raw)!=n: raise ValueError('truncated GGUF metadata')
        return struct.unpack('<'+fmt,raw)[0]
    def string(self):
        n=self.unpack('Q')
        if n>64*1024**2: raise ValueError('oversized GGUF string')
        b=self.f.read(n)
        if len(b)!=n: raise ValueError('truncated GGUF string')
        return b
    def value(self, kind):
        if kind in self.formats: return self.unpack(self.formats[kind])
        if kind==8: return self.string().decode('utf8','replace')
        if kind==9:
            sub=self.unpack('I'); n=self.unpack('Q')
            if n>2_000_000: raise ValueError('oversized GGUF array')
            vals=[self.value(sub) for _ in range(n)]
            return vals
        raise ValueError('unknown GGUF type '+str(kind))
    def metadata(self):
        if self.f.read(4)!=b'GGUF': raise ValueError('not GGUF')
        ver=self.unpack('I'); nt=self.unpack('Q'); nk=self.unpack('Q')
        meta={}
        for _ in range(nk):
            k=self.string().decode('utf8'); meta[k]=self.value(self.unpack('I'))
        tokens=meta.get('tokenizer.ggml.tokens',[])
        # Canonical JSON fingerprint is explicit and is not a claim of raw GGUF-byte hash.
        toksha=hashlib.sha256(json.dumps(tokens,ensure_ascii=True,separators=(',',':')).encode()).hexdigest()
        scalar={k:v for k,v in meta.items() if not isinstance(v,list) and
                (k.startswith('general.') or k.startswith('qwen3.') or k.startswith('tokenizer.'))}
        return dict(version=ver,tensors=nt,metadata_pairs=nk,metadata_end_offset=self.f.tell(),
                    vocabulary_count=len(tokens),vocabulary_canonical_json_sha256=toksha,scalars=scalar,
                    note='metadata-only CPU parser, no model load, no forward')

def main():
    started=time.monotonic(); HERE.mkdir(exist_ok=True)
    records=[]
    cumulative=read(OLD/'q8rtx213-correction-draft/benchmarks/rtx_q8_correction_draft_20261109/results/CUMULATIVE_LEDGER.json')
    ledger_results=[]
    for i,entry in enumerate(cumulative['latest_RTX_ledger_chain']):
        p=Path(entry['path']); before=ident(p,entry['sha256'])
        folder=HERE/'ledger_copies'/str(i); folder.mkdir(parents=True,exist_ok=False)
        parts=[]
        for suffix in ('','-wal','-shm'):
            src=Path(str(p)+suffix)
            if src.is_file():
                parts.append(ident(src)); shutil.copyfile(src,folder/src.name)
        db=sqlite3.connect((folder/p.name).as_uri()+'?mode=ro',uri=True)
        db.row_factory=sqlite3.Row
        tables=[r[0] for r in db.execute("select name from sqlite_master where type='table'")]
        table='attempts' if 'attempts' in tables else tables[0]
        rows=[dict(r) for r in db.execute('select * from '+table)]
        db.close()
        numeric={k:sum(r.get(k,0) or 0 for r in rows) for k in
                 ('requests','token_rows','rows','operators') if any(k in r for r in rows)}
        after=ident(p,entry['sha256'])
        ledger_results.append(dict(before=before,after=after,sidecars=parts,tables=tables,
                                   attempts=rows,totals=numeric,old_main_byte_unchanged=before['sha256']==after['sha256']))
    put('LEGACY_LEDGER_AUDIT.json',dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        published_totals={k:cumulative[k] for k in ('cumulative_requests','cumulative_reserved_rows','qualification_requests')},
        ledgers=ledger_results,refunds=0,new_epoch_borrows_old_budget=False))
    inventory=[]
    for role,base in [('R','D:/rtx192-review-v2/R-Qwen'),('loop4','D:/rtx211-q8-20261109/loop4-v2'),('packed','D:/rtx211-q8-20261109/packed-v2')]:
        root=Path(base); build=read(root/'BUILD.json'); files=[ident(root/'bin/worker.exe',build['exe'])]
        for name,expected in build['modules'].items(): files.append(ident(root/'bin'/name,expected))
        inventory.append(dict(role=role,build=ident(root/'BUILD.json'),disk_files=files,
                              newly_loaded_modules=None,scope='read-only disk binding, historical binaries only'))
    for role,path,expected in [('target','D:/HeteroSpec-PC/models/gguf/Qwen3-8B-Q8_0.gguf','408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6'),('draft','D:/HeteroSpec-PC/models/gguf/Qwen3-0.6B-Q8_0.gguf','9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031')]:
        row=ident(path,expected)
        with Path(path).open('rb') as f: row['gguf']=GGUF(f).metadata()
        inventory.append(dict(role=role,model=row))
    tools=[Path('D:/rtx184-tools/cuda/bin')/x for x in ('nvcc.exe','ptxas.exe','nvlink.exe')]
    tools += [Path('D:/rtx184-tools/msvc/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/cl.exe'),
              Path('D:/rtx184-tools/msvc/setup_x64.bat'),Path('D:/HeteroSpec-PC/.venv-analysis/Lib/site-packages/ziglang/zig.exe')]
    for path in tools: inventory.append(dict(role='toolchain',file=ident(path)))
    put('DISK_IDENTITIES.json',dict(inventory=inventory,actual_loaded_modules_new_epoch=None,
                                   note='No new native worker has been launched; disk presence is not loaded-DLL evidence.'))
    source=[]
    for core in ('loop4','packed'):
        root=Path('D:/rtx192-review-v2/native-v2/cores')/core
        for rel in ('AGENTS.md','ggml/src/ggml-cuda/mmvq.cuh','ggml/src/ggml-cuda/mmvq.cu','ggml/src/hs_loop4_tensor.hpp','src/llama-graph.cpp','src/llama-context.cpp'):
            source.append(ident(root/rel))
    for path in Path('D:/rtx211-q8-20261109/frontend-v2').iterdir():
        if path.is_file():source.append(ident(path))
    put('SOURCE_IDENTITIES.json',dict(files=source,upstream221_head='af436df989570ad882db65bd8a4b265b9e8cfdae',
        upstream_head_verified_by_parent_connector=True,remote_AGENTS_md='404_NOT_FOUND',
        local_original_thread_status='UNVERIFIED',thread_connector_error='codex_app/list_threads MCP -32000 request failed'))
    observations=[command(['nvidia-smi','--query-gpu=index,uuid,name,memory.total,memory.used,memory.free,driver_version,temperature.gpu,power.draw,power.limit,utilization.gpu','--format=csv']),
                  command(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv']),
                  command(['D:/rtx184-tools/cuda/bin/nvcc.exe','--version']),
                  command(['D:/HeteroSpec-PC/.venv-analysis/Lib/site-packages/ziglang/zig.exe','version'])]
    lock=Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock')
    put('HOST_AUDIT.json',dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),observations=observations,
        old_shared_lock=dict(path=str(lock),exists=lock.exists(),modified=False),
        cuda_env={k:v for k,v in os.environ.items() if k in ('CUDA_VISIBLE_DEVICES','CUDA_DEVICE_ORDER','GGML_CUDA_DISABLE_GRAPHS')},
        disks={p:dict(zip(('total','used','free'),shutil.disk_usage(p))) for p in ('C:/','D:/')},
        audit_model_requests=0,audit_kernel_launches=0,new_native_loaded_modules=None,
        original_thread_unverified=True,exclusive_gpu_resource_not_established=True,
        physical_device_binding='GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd; observed physical index 0',
        elapsed_seconds=time.monotonic()-started))
    print(json.dumps(dict(status='AUDIT_COMPLETE_NO_MODEL_NO_KERNEL',seconds=time.monotonic()-started,
                           all_legacy_main_hashes_match=all(r['after']['matches'] for r in ledger_results))))

if __name__=='__main__': main()
