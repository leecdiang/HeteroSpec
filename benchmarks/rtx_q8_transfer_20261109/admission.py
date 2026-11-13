"""Read-only host/history inventory; never imports a model runner."""
from pathlib import Path
import collections, datetime, hashlib, json, os, sqlite3, subprocess, time

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'results_20261109'
REPO = HERE.parents[1]
PIN = 'ad9fb6846dd979c3a76d3c415c74fa9f86565f7d'

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def put(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def run(args):
    started = time.monotonic()
    r = subprocess.run(args, capture_output=True, timeout=120)
    return dict(argv=list(map(str, args)), code=r.returncode,
                seconds=time.monotonic()-started,
                stdout=r.stdout.decode('utf8', errors='replace'),
                stderr=r.stderr.decode('utf8', errors='replace'))

def main():
    ROOT.mkdir(exist_ok=False)
    started = time.monotonic()
    base = Path('D:/rtx192-review-v2')
    docs = ['benchmarks/rtx_closeout_bcd/REPORT.md',
            'benchmarks/rtx_closeout_bcd/SOURCE_BINDINGS.json']
    for parent in ['benchmarks/server_expansion_v1/M2',
                   'benchmarks/server_expansion_v1/M']:
        names = subprocess.check_output(['git','-C',str(REPO),'ls-tree','-r','--name-only',PIN,parent]).decode().splitlines()
        docs += [n for n in names if '/results_' not in n and '/post-terminal/' not in n]
    records = []
    for name in docs:
        p = ROOT / 'pinned_sources' / name
        p.parent.mkdir(parents=True, exist_ok=True)
        data = subprocess.check_output(['git','-C',str(REPO),'show',PIN+':'+name])
        with p.open('xb') as f: f.write(data)
        records.append(dict(path=name, sha256=sha(p), bytes=len(data)))
    put(ROOT/'PINNED_SOURCES.json', dict(commit=PIN,files=records))
    inventory = []
    for role in ['R-Qwen','runtime-v2-loop4','runtime-v2-packed']:
        b = json.loads((base/role/'BUILD.json').read_bytes())
        files = [base/role/'bin/worker.exe'] + list((base/role/'bin').glob('*.dll'))
        pins = []
        for p in files:
            expected = b['exe'] if p.suffix=='.exe' else b['modules'][p.name]
            actual = sha(p)
            pins.append(dict(path=str(p),sha256=actual,expected=expected,matches=actual==expected,bytes=p.stat().st_size))
        inventory.append(dict(role=role,build_sha256=sha(base/role/'BUILD.json'),files=pins))
    models = json.loads((HERE.parent/'tpds_phase1_v1/MODEL_ASSETS.json').read_bytes())['Qwen']
    for role, model in models.items():
        p=Path('D:/HeteroSpec-PC/models/gguf')/model['file']
        actual=sha(p)
        inventory.append(dict(role=role,path=str(p),sha256=actual,expected=model['sha256'],matches=actual==model['sha256'],bytes=p.stat().st_size))
    put(ROOT/'SOURCE_BINDINGS_INITIAL.json',dict(status='DISK_AND_HISTORICAL_BINDINGS_ONLY',
        newly_loaded_candidate_modules=None,original_R_immutable=True,bindings=inventory,
        runtime_policy='No new worker launched. Actual loaded modules must be bound in qualification; disk hashes are insufficient.'))
    ledger_path=base/'ledger.sqlite'
    db=sqlite3.connect(ledger_path.as_uri()+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    attempts=[dict(r) for r in db.execute('select * from attempts order by started')]
    db.close()
    totals={k:sum(r[k] for r in attempts) for k in ['requests','token_rows','operators']}
    put(ROOT/'CUMULATIVE_LEDGER_INITIAL.json',dict(as_of_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source=str(ledger_path),sha256=sha(ledger_path),attempts=attempts,totals=totals,
        statuses=dict(collections.Counter(r['status'] for r in attempts)),
        historical_limits=dict(requests=3072,token_rows=4000000),new_requests=0,new_rows=0,
        reconciliation_status='PENDING_LATER_RTX_WORK_AUDIT',refunds=0))
    commands=[['nvidia-smi','--query-gpu=name,uuid,memory.total,memory.used,memory.free,driver_version,temperature.gpu,power.draw,power.limit,utilization.gpu','--format=csv'],
              ['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv'],
              ['powercfg','/getactivescheme']]
    put(ROOT/'HOST_INITIAL.json',dict(as_of_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        observations=[run(c) for c in commands],authorized_end_time=None,
        reserve_floors=dict(output_disk_bytes=20*1024**3,system_disk_bytes=10*1024**3,ram_bytes=4*1024**3,gpu_bytes=128*1024**2),
        source_protocol=PIN,model_forward_requests=0))
    first=[0,1,7,2,6,3,5,4]
    schedule=[[(a+s)%8 for a in first] for s in range(8)]
    assert all(sorted(row)==list(range(8)) for row in schedule)
    assert all(sorted(row[p] for row in schedule)==list(range(8)) for p in range(8))
    neighbors=collections.Counter((a,b) for row in schedule for a,b in zip(row,row[1:]))
    assert len(neighbors)==56 and set(neighbors.values())=={1}
    put(ROOT/'SCHEDULE_ACCOUNTING_CHECK.json',dict(schedule=schedule,position_balance=True,directed_neighbor_balance=True,
        live_measurements=1024,live_primers=128,diagnostic_measurements=128,diagnostic_primers=32,
        ceilings=dict(qualification=512,diagnostic=160,profiling=32,live=1152,closure=192),
        new_request_ceiling=2048,live_row_bound_conditional=1152*(2*192+16*96),
        exact_job_manifest_frozen=False,all_slots_not_yet_admitted=True,model_forward_requests=0))
    put(ROOT/'ADMISSION_COSTS_INITIAL.json',dict(wall_seconds=time.monotonic()-started,model_forward_requests=0,
        profiling_requests=0,clean_timing_requests=0,qualifying_requests=0,scope='Host inventory, hash reads, source fetch, ledger reads and no-model arithmetic only'))
    print(json.dumps(dict(files=len(records),historical_attempts=len(attempts),historical_totals=totals,
                         all_disk_pins_match=all(p['matches'] for r in inventory for p in r.get('files',[r])),
                         no_model_forwards=True),ensure_ascii=False))

if __name__=='__main__':main()
