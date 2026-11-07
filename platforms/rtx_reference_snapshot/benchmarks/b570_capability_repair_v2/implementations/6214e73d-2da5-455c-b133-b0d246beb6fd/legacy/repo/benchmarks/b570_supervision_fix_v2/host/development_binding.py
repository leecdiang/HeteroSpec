"""Bind actual development captures and compiler evidence to reviewed source."""
import hashlib
import subprocess


def source_hashes(freeze):
    return {k:v for k,v in freeze['bound_files'].items()
            if k.startswith('host/') or k in ('ACCEPTANCE.json','BUDGET.json','check_receipts.py')}


def validate(cfg, freeze, freeze_sha, build, build_sha, ledger):
    if freeze.get('scope')!='source_review_only' or freeze.get('review_status')!='scoped-clean':
        raise ValueError('development source review missing')
    expected=source_hashes(freeze)
    if 'host/LauncherCapture.dll' in expected:raise ValueError('source-only freeze contains DLL')
    if cfg.get('source_review_sha256')!=freeze_sha or build.get('source_review_sha256')!=freeze_sha:
        raise ValueError('development review identity mismatch')
    if cfg.get('build_record_sha256')!=build_sha or build['source_hashes']!=expected:
        raise ValueError('build source identity mismatch')
    if cfg['code_hashes']!={**expected,'host/LauncherCapture.dll':build['dll_sha256']}:
        raise ValueError('runtime source capture differs from reviewed build')
    if build['exit_code']!=0 or not build.get('compiler_sha256'):
        raise ValueError('compiler failed or identity missing')
    starts=[r for r in ledger if r['kind']=='PROCESS_CREATE' and r['pid']==build['pid']
            and build['begin_ns']<=r['at_ns']<=build['end_ns']]
    if len(starts)!=1:raise ValueError('compiler process observation missing')
    start=starts[0];command=subprocess.list2cmdline(build['argv'])
    if start['command_sha256']!=hashlib.sha256(command.encode()).hexdigest():
        raise ValueError('observed compiler command mismatch')
    closes=[r for r in ledger if r['kind']=='PROCESS_CLOSED' and r['pid']==start['pid']
            and r['created_filetime']==start['created_filetime']]
    if len(closes)!=1 or closes[0]['exit_code']!=0:raise ValueError('compiler OS closure missing')
    return True
