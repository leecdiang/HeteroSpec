"""Read-only PR104 admission audit. Never starts a native process or request.

Writes a new, non-admitting FREEZE and complete evidence inventory. Existing
files are never replaced. This is not experiment.prepare's execution freeze.
"""
from __future__ import annotations
import argparse
import contextlib
import ctypes
import hashlib
import importlib
import io
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
import experiment

def command(args, cwd=None):
    p = subprocess.run(args, cwd=cwd, capture_output=True)
    return dict(command=args, returncode=p.returncode,
                stdout=p.stdout.decode('utf-8', errors='replace'),
                stderr=p.stderr.decode('utf-8', errors='replace'))

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('repo', 'baseline', 'legacy', 'runtime', 'out'):
        ap.add_argument('--'+k, type=Path, required=True)
    a = ap.parse_args()
    roots = {k: getattr(a, k).resolve() for k in ('repo','baseline','legacy','runtime','out')}
    out = roots['out']; out.mkdir(parents=True, exist_ok=False)
    evidence = out/'raw'; evidence.mkdir()
    checks = []; inventory = []
    def asset(path, expected=None, kind='sha256', label=None):
        row = dict(path=str(path), label=label or path.name, expected=expected, hash_kind=kind)
        try:
            item = experiment.pin(path); row.update(item)
            actual = experiment.blob(path.read_bytes()) if kind=='git_blob' else item['sha256']
            row.update(actual=actual, status='PASS' if expected is None or actual==expected else 'MISMATCH')
        except Exception as e:
            row.update(status='MISSING_OR_UNREADABLE', error=repr(e))
        checks.append(row); inventory.append(row)
        return row
    def preserve(name, body):
        (evidence/name).write_bytes(body)
    def git(*args, base=False):
        return command(['git', *args], str(roots['baseline'] if base else roots['repo']))
    git_records = {'pr104_head':git('rev-parse','HEAD'),
                   'pr104_branch':git('branch','--show-current'),
                   'pr104_status':git('status','--short'),
                   'baseline_head':git('rev-parse','HEAD',base=True)}
    expected_head='2511ade621d036c0d712c3d694483c79da2b4cf1'
    for label, key, expected in [('PR104_COMMIT','pr104_head',expected_head),
                                ('PR98_COMMIT','baseline_head',experiment.BASELINE_COMMIT)]:
        r=git_records[key]
        checks.append(dict(label=label, expected=expected, actual=r['stdout'].strip(),
                           status='PASS' if r['returncode']==0 and r['stdout'].strip()==expected else 'MISMATCH'))
    pub=roots['baseline']/'benchmarks/rtx_querylayout_mechanism_v1'
    for name, expected in experiment.RESULT_BLOBS.items():
        asset(pub/name, expected, 'git_blob')
    for name, expected in experiment.SOURCE_BLOBS.items():
        asset(roots['legacy']/name, expected, 'git_blob')
    deps=experiment.read(pub/'EXECUTION_DEPENDENCIES.json')['reused_authenticated_parent_code']
    for name, expected in deps.items():
        asset(roots['legacy']/name, expected, label='legacy helper: '+name)
    original=experiment.read(pub/'NATIVE_BUILD.json')
    corrected=experiment.read(pub/'NATIVE_BUILD_V02.json')
    asset(roots['runtime']/'llama-server.exe',original['server_sha256'])
    asset(roots['runtime']/'llama-server-pq-metadata4.exe',corrected['server_sha256'])
    asset(roots['runtime']/'querylayout-replay.exe',original['replay_sha256'])
    for name, expected in original['numerical_DLL_sha256'].items():
        asset(roots['runtime']/name, expected)
    contract=experiment.read(pub/'MODEL_CONTRACT.json')
    for family in experiment.FAMILIES:
        for role, item in contract['families'][family]['models'].items():
            r=asset(Path(item['path']),item['sha256'],label=family+'/'+role)
            r['expected_bytes']=item['bytes']
            if r.get('bytes')!=item['bytes']:r['status']='MISMATCH'
    for name in ('NATIVE_BUILD.json','NATIVE_BUILD_V02.json','RESOURCE_CORRECTION.json',
                 'MODEL_CONTRACT.json','EXECUTION_DEPENDENCIES.json','HOST_ADMISSION.json',
                 'LIVE_PREFLIGHT.json','P0_PLAN.json'):
        preserve(name,(pub/name).read_bytes())
    for name in ('correction95_v02.py','runner95.py'):
        preserve(name,(roots['baseline']/'scripts/platform/rtx_querylayout_mechanism_v1'/name).read_bytes())
    for name in experiment.SOURCE_BLOBS:
        preserve(name,(roots['legacy']/name).read_bytes())
    sys.path.insert(0,str(roots['legacy']))
    common=importlib.import_module('run_common'); native=importlib.import_module('resident')
    host=common.host()
    expected_host=experiment.read(pub/'LIVE_PREFLIGHT.json')['sample']
    identity_keys=('gpu','driver','total_MiB','power_scheme_guid')
    checks.append(dict(label='HOST_IDENTITY',expected={k:expected_host[k] for k in identity_keys},
                       actual={k:host[k] for k in identity_keys},
                       status='PASS' if all(host[k]==expected_host[k] for k in identity_keys) else 'MISMATCH'))
    host_commands=[command(['nvidia-smi','--query-gpu=name,uuid,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu,clocks.sm,clocks.mem,power.draw,power.limit','--format=csv']),
                   command(['nvidia-smi','-q']),command(['powercfg','/getactivescheme'])]
    preserve('HOST.json',experiment.encoded(dict(sample=host,commands=host_commands)))
    preserve('GIT.json',experiment.encoded(git_records))
    # Construct commands only. No subprocess for native binaries is invoked.
    native.LOCAL=out; common.PUB=pub; native.PUB=pub
    runtime_routes=[]
    for family in experiment.FAMILIES:
        for arm in ('R','M_PQ','M_QB','C_PQ','C_QB'):
            cmd=native.command(family,experiment.condition(arm))
            v02=family in ('SmolLM2','Llama') and arm.endswith('_PQ')
            runtime_routes.append(dict(family=family,arm=arm,generated_command=cmd,
                expected_binary='llama-server-pq-metadata4.exe' if v02 else 'llama-server.exe',
                actual_binary=Path(cmd[0]).name,status='MISMATCH' if v02 else 'PASS'))
    mismatched=[r for r in runtime_routes if r['status']=='MISMATCH']
    checks.append(dict(label='INHERITED_ARM_RUNTIME_ROUTING',status='MISMATCH' if mismatched else 'PASS',
                       affected=[r['family']+'/'+r['arm'] for r in mismatched],
                       reason='PR104 prepare copies only NATIVE_BUILD.json/original executable; run_session uses unmodified native.Resident. PR98 CorrectedWorker selects NATIVE_BUILD_V02 and metadata4 executable for SmolLM2/Llama PQ.'))
    preserve('RUNTIME_ROUTES.json',experiment.encoded(runtime_routes))
    old=experiment.read(pub/'P0_PLAN.json')
    blocks=experiment.schedule(old['P2_panel'])
    planned=dict(blocks=blocks,panel=old['P2_panel'],seed=20261014,
                 input_exposure='EXPOSED_PANEL_NEW_EXECUTION_BLOCKS',
                 blocks_count=len(blocks),comparison_requests=864,reference_requests=432,warmups=324,
                 total_requests=1620,registered=False,executed=False)
    experiment.save(out/'UNREGISTERED_PLAN.json',planned)
    frozen=[]
    for p in sorted(Path(__file__).parent.glob('*.py')):
        frozen.append(experiment.pin(p))
    frozen.extend(experiment.pin(p) for p in sorted(evidence.iterdir()))
    frozen.append(experiment.pin(out/'UNREGISTERED_PLAN.json'))
    mismatches=[c for c in checks if c['status']!='PASS']
    report=dict(schema=1,created_utc=datetime.now(timezone.utc).isoformat(),
                phase='PHASE0_READ_ONLY_ADMISSION',status='STOPPED_INCONSISTENCY' if mismatches else 'REVIEW_REQUIRED',
                execution_admitted=False,canonical_E2_execution_freeze=False,
                pr104_commit=expected_head,pr104_branch='experiment/rtx-qb-confirmation-20261014',
                baseline_commit=experiment.BASELINE_COMMIT,roots={k:str(v) for k,v in roots.items()},
                checks=checks,mismatches=mismatches,host=host,files=frozen,
                native_processes_started=0,scientific_requests_started=0,
                scientific_slots_started=[],scientific_retries=0,
                E2_status='NOT_STARTED_PHASE0_STOP',E1_status='NOT_STARTED_E2_GATE',
                inherited_history_untouched=True)
    experiment.save(out/'FREEZE.json',report)
    print(json.dumps(dict(status=report['status'],mismatches=mismatches,checks=len(checks),
                          native_processes_started=0,requests_started=0),indent=2))

if __name__=='__main__':main()
