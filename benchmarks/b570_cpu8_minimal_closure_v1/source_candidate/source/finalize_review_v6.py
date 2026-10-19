"""Data-only approval composition after the actual complete independent verdict."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'source'),str(ROOT/'src/rev2')]
from win import dump_new,sha
from evidence_contract import member
from identity_v6 import file_identity
from audit_identity_stream import check
report=ROOT/'review/FINAL_REVIEW.json';review=json.loads(report.read_bytes())
manifest=ROOT/'review/CANDIDATE_MANIFEST.json';m=json.loads(manifest.read_bytes())
assert review['status']=='scoped-clean' and review['findings']==[] and review['candidate_manifest_sha256']==sha(manifest),'no complete exact final clean'
check(ROOT/'processes/full-review')
for row in m['files']:assert sha(member(ROOT,row['path']))==row['sha256'],'post-review deployed drift'
dump_new(ROOT/'source/FINAL_REVIEW_BINDING.json',dict(status='scoped-clean',report_path='review/FINAL_REVIEW.json',report_sha256=sha(report),files=m['files'],scope='Actual completed independent full deployed review; generated data, not a source-code replacement'))
design=ROOT/'legacy/repo/benchmarks/b570_supervision_fix_v2'
from bridge import sources
hashes=sources(design)
old=(design/'SOURCE_REVIEW_FREEZE.json').read_bytes()
dump_new(ROOT/'compiled/HISTORICAL_SOURCE_REVIEW.json',json.loads(old))
approval=dict(scope='source_review_only',review_status='scoped-clean',bound_files=hashes,current_deployed_report_sha256=sha(report),candidate_manifest_sha256=sha(manifest))
# Only this new copy changes; old UUID remains immutable.
(design/'SOURCE_REVIEW_FREEZE.json').write_text(json.dumps(approval,sort_keys=True,indent=2)+'\n')
build=json.loads((ROOT/'compiled/BUILD_CURRENT.json').read_bytes());events=[json.loads(x) for x in (ROOT/'processes/compile-v6-2/OS_EVENTS.jsonl').read_bytes().splitlines()]
start=next(x for x in events if x['event']=='ROOT_CREATED_SUSPENDED');end=next(x for x in events if x['event']=='PROCESS_CLOSED' and x['pid']==build['compiler']['pid'] and x['created_filetime']==build['compiler']['created_filetime'])
(design/'results').mkdir(exist_ok=True)
argv=json.loads((ROOT/'tools/021-build-launcher-windows-path.operation.json').read_bytes())['argv'];i=argv.index('--');compiler_argv=argv[i+1:]
dump_new(design/'results/BUILD_RECORD.json',dict(source_review_sha256=sha(design/'SOURCE_REVIEW_FREEZE.json'),source_hashes=hashes,compiler_sha256=json.loads((ROOT/'preflight/TOOLS.json').read_bytes())['csharp']['sha256'],argv=compiler_argv,pid=build['compiler']['pid'],begin_ns=start['at_ns'],end_ns=end['at_ns'],exit_code=0,dll_sha256=build['dll_sha256'],compiled_file='compiled/candidate/LauncherCapture.dll',scope='Actual pre-review compile; unchanged reviewed source, observed compiler and retained native OS exit'))
files={p.relative_to(ROOT).as_posix():sha(p) for base in ('source','src/rev2') for p in sorted((ROOT/base).rglob('*')) if p.is_file()}
dump_new(ROOT/'ENTRY_SOURCE_MANIFEST.final.json',dict(files=files))
expected=ROOT/'D0_EVIDENCE_SNAPSHOT/EXPECTED.json';d0=json.loads(expected.read_bytes());man=ROOT/'D0_EVIDENCE_SNAPSHOT/legacy'/d0['manifest_relative']
dump_new(ROOT/'INTEGRATION_GATE_BINDING.json',dict(startup_manifest='ENTRY_SOURCE_MANIFEST.final.json',startup_receipt='preflight/STARTUP.final.json',startup_intent='tools/038-final-startup.intent.json',startup_operation='tools/038-final-startup.operation.json',churn='review-churn',full_review_report='review/FINAL_REVIEW.json',full_review_process='full-review',candidate_manifest_sha256=sha(manifest),d0_snapshot='D0_EVIDENCE_SNAPSHOT',d0_manifest=d0['manifest_relative'],d0_manifest_sha256=sha(man),d0_expected_sha256=sha(expected)))
identity=json.loads((ROOT/'FILESYSTEM_IDENTITY.json').read_bytes());identity['files']={row['path']:file_identity(ROOT/row['path']) for row in m['files']}
(ROOT/'FILESYSTEM_IDENTITY.json').write_text(json.dumps(identity,sort_keys=True,indent=2)+'\n')
print(json.dumps(dict(status='CURRENT_REVIEW_BINDINGS_CREATED',startup_manifest_sha256=sha(ROOT/'ENTRY_SOURCE_MANIFEST.final.json'),review_sha256=sha(report),files=len(m['files']))))
