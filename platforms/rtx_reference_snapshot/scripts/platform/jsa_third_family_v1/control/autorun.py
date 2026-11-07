"""Detached local orchestration; never invokes Codex or an OpenAI API."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *
import argparse, ctypes, traceback

CONTROL = LOCAL / 'autorun'
OUTPUT = REPO.parent.parent / 'outputs'
STATUS = OUTPUT / 'HeteroSpec_RTX_三家族实验_运行状态.md'
LOG = CONTROL / 'run.log'
SCRIPTS = Path(__file__).resolve().parents[1]
BRANCH = 'experiment/jsa-third-family-rtx-20261011'
PR = 'https://github.com/leecdiang/HeteroSpec/pull/84'

def state(phase, detail=''):
    CONTROL.mkdir(exist_ok=True); OUTPUT.mkdir(exist_ok=True)
    n = len(list((CONTROL / 'events').glob('*.json')))
    save(CONTROL / 'events' / f'{n:04d}-{phase}.json',
         {'utc': now(), 'phase': phase, 'detail': detail, 'pid': os.getpid()})
    # This display is not a paid request ledger. Scientific records stay immutable.
    content = ('# HeteroSpec RTX 实验运行状态\n\n'
               f'状态：**{phase}**\n\n{detail}\n\n'
               f'更新时间（UTC）：{now()}\n\n后台进程：{os.getpid()}\n\n'
               f'详细日志：[run.log]({LOG.as_posix()})\n\n'
               f'实验 PR：[#84]({PR})\n\n'
               '本流程不调用 Codex 或 OpenAI API；无需保持对话运行。\n'
               '请保持电脑开机、接电和网络可用。脚本会临时阻止系统自动睡眠，结束后解除。\n')
    for _ in range(5):
        try: STATUS.write_text(content, encoding='utf-8'); break
        except PermissionError: time.sleep(.2)

def step(name, cmd, timeout, retries=1):
    state(name, '运行中；所有后续步骤由本地脚本自动执行。')
    for attempt in range(retries):
        with LOG.open('ab', buffering=0) as log:
            log.write(f'\n[{now()}] {name} attempt {attempt+1}\n'.encode())
            run = subprocess.run(cmd, cwd=REPO, stdout=log, stderr=subprocess.STDOUT,
                                 timeout=timeout, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if run.returncode == 0: return
        if attempt + 1 < retries: time.sleep(10 * (attempt + 1))
    raise RuntimeError(f'{name}: exit {run.returncode}; see {LOG}')

def python_step(name, file, *args, timeout=600, retries=1):
    step(name, [sys.executable, '-u', str(SCRIPTS / file), *args], timeout, retries)

def commit(message):
    subprocess.run(['git', 'add', 'benchmarks/jsa_third_family_v1'], cwd=REPO, check=True)
    subprocess.run(['git', 'diff', '--cached', '--check'], cwd=REPO, check=True)
    changed = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=REPO)
    assert changed.returncode in [0, 1]
    if changed.returncode:
        step('COMMIT_RESULTS', ['git', 'commit', '-m', message], 300)
    step('PUSH_RESULTS', ['git', 'push', 'origin', BRANCH], 1200, retries=5)

def validate(initial=True):
    f = read(PUB / 'F0B.json'); r = read(LOCAL / 'F0B_REMOTE_RECEIPT.json')
    assert r['status'] == 'PASS' and r['manifest_sha256'] == sha(PUB / 'F0B.json')
    for name, h in f['code_sha256'].items(): assert sha(SCRIPTS / name) == h
    for name, h in f['payload_sha256'].items(): assert sha(PUB / name) == h
    boundary = read(PUB / 'AUTORUN_BOUNDARY.json')
    for name, h in boundary['control_sha256'].items(): assert sha(SCRIPTS / 'control' / name) == h
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=REPO, text=True).strip() == BRANCH
    if initial: assert not (LOCAL / 'runs/formal').exists(), 'Formal run already exists; never replay it.'

def body():
    a = read(PUB / 'RESULTS.json'); p = read(PUB / 'POSTCHECKS.json')
    def ratio(v): return 'null (unqualified)' if v is None else f'{v:.6f}x'
    lines = ['Execute design PR #83 on RTX 5070 Ti Laptop using Qwen, SmolLM2 and Llama with the same newly audited 24-task panel and all six fixed conditions.', '',
             f'Completed {a["completed"]}/3456 formal requests. Engineering completed 624/624 requests including its warmups; formal warmups completed {p["accounting"]["formal"]["warmups_started"]}/144. No formal retry, overwrite, condition selection or endpoint truncation.', '',
             '| Family | Stable complete paid R | Qualified M3/C3_K3 | Qualified R/C3_K3 | Qualified R/M3 |',
             '|---|---|---:|---:|---:|']
    for family, f in a['families'].items():
        c = {r['comparison']: r for r in f['comparisons']}
        lines.append('| '+family+' | '+str(f['stable_complete_R'])+' | '+' | '.join(ratio(c[k]['qualified_ratio']) for k in ['M3/C3_K3', 'R/C3_K3', 'R/M3'])+' |')
    lines += ['', 'The prospective fast-session amendment uses two consecutive independent sessions per family, four rounds each. These are descriptive effects; all six-date confidence intervals and cross-date positive decisions remain untested/null. Qualification requires every planned native-array slot and all stable paid ordinary references. Unqualified cost ratios remain explicitly diagnostic; k1/k2 and all failures/missing slots remain reported.', '',
              'The primary timer is complete resident nonstreaming HTTP submission through response receipt and JSON parsing. Loading/warmups are separately accounted. Requested logical batch2048 is clamped by the unchanged runtime to effective1024 under ctx1024; targetUB1/4 and draftUB1, F16 KV, full GPU, FA off and threads24 are fixed.', '',
              'All 18 implementation gates passed, all 36 capture-on/off comparisons and all cap-boundary arrays agreed. Numerical DLLs and private source hashes are preserved. Publisher model bytes/revisions are verified; official checkpoint conversion ancestry remains unverified. Native per-phase GPU timers are not claimed.', '',
              'Validation: unchanged F0B code/payload/runtime/model hashes and request budgets passed; independent local author-archive restoration and actual authenticated GitHub scientific-archive restoration reproduced RESULTS.json byte-for-byte. See RESULTS.md, RESULTS.json, ENGINEERING_RESULTS.json, POSTCHECKS.json, ARCHIVE_MANIFEST.json and RESTORE_LOCAL/REMOTE.json.', '',
              'The workflow ran locally without Codex/OpenAI API polling. Prior PR #80/#82, manuscript and release remain unchanged. This PR remains draft; nothing is merged.', '']
    target = CONTROL / 'PR_BODY_FINAL.md'; target.write_text('\n'.join(lines), encoding='utf-8')
    return target

def main(resume=False):
    validate(initial=not resume)
    CONTROL.mkdir(exist_ok=True)
    # OS releases this lock after crashes, but formal STARTED slots are never replayed.
    import msvcrt
    lock = (CONTROL / 'LOCK').open('a+b'); lock.seek(0); lock.write(b'1'); lock.flush(); lock.seek(0)
    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    started = False
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
        if not resume:
            receipt = read(PUB / 'AUTORUN_REMOTE_READBACK.json'); assert receipt['status'] == 'PASS'
            save(CONTROL / 'START.json', {'utc': now(), 'pid': os.getpid(), 'F0B_remote_commit': read(LOCAL / 'F0B_REMOTE_RECEIPT.json')['frozen_sha'], 'controller_sha256': sha(__file__), 'Codex_or_OpenAI_API_calls': 0, 'formal_retries': 0})
            started = True
            python_step('FORMAL_RUNNING', 'formal.py', timeout=60*3600)
        assert (LOCAL / 'runs/formal/COMPLETE.json').exists(), 'Interrupted formal run is retained; do not restart it.'
        if not (PUB / 'RESULTS.json').exists(): python_step('ANALYSING', 'analyse.py')
        if not (PUB / 'POSTCHECKS.json').exists(): python_step('VERIFYING_IDENTITIES', 'postchecks.py', timeout=1800)
        if not (PUB / 'RESULTS.md').exists(): python_step('WRITING_REPORT', 'report.py')
        if not (PUB / 'ARCHIVE_MANIFEST.json').exists(): python_step('ARCHIVING', 'pack.py', timeout=3600)
        assert (PUB / 'RAW_EVIDENCE.zip').stat().st_size < 100*1024*1024, 'Git scientific bundle exceeds ordinary blob limit; local evidence retained.'
        if not (PUB / 'RESTORE_LOCAL.json').exists(): python_step('LOCAL_REPRODUCTION', 'restore_check.py', 'local', timeout=1800)
        commit('Complete consecutive-session RTX three-family results and local reproduction')
        if not (PUB / 'RESTORE_REMOTE.json').exists(): python_step('REMOTE_REPRODUCTION', 'restore_check.py', 'remote', timeout=1800, retries=3)
        for mode in ['LOCAL', 'REMOTE']: assert read(PUB / f'RESTORE_{mode}.json')['status'] == 'PASS'
        if not (PUB / 'AUTORUN_COMPLETE.json').exists():
            save(PUB / 'AUTORUN_COMPLETE.json', {'status': 'SCIENTIFIC_PIPELINE_COMPLETE', 'utc': now(), 'formal_completed': read(PUB / 'RESULTS.json')['completed'], 'results_sha256': sha(PUB / 'RESULTS.json'), 'local_and_remote_independent_CPU_reproduction': 'PASS', 'Codex_or_OpenAI_API_calls': 0, 'formal_retries': 0})
        commit('Record independent authenticated remote restoration and unattended completion')
        target = body()
        step('UPDATE_PR', ['gh', 'pr', 'edit', '84', '--repo', 'leecdiang/HeteroSpec', '--title', 'Complete RTX three-family validation with consecutive sessions', '--body-file', str(target)], 300, retries=3)
        state('COMPLETE', f'实验、报告、归档、本地及远端独立复算和 PR 更新已完成。结果：{OUTPUT / "HeteroSpec_RTX_三家族同日实验_报告.md"}')
    except BaseException:
        with LOG.open('a', encoding='utf-8') as log: traceback.print_exc(file=log)
        state('FAILED_NEEDS_ATTENTION', '失败证据和已有输出全部保留；不会自动重跑正式请求。详情见日志。网络发布步骤可用 --resume-post 继续，不重复模型实验。')
        raise
    finally:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
        lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1); lock.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--check-only', action='store_true'); parser.add_argument('--resume-post', action='store_true'); args = parser.parse_args()
    if args.check_only:
        validate(); print('AUTORUN CHECK PASS: F0B unchanged; no formal run; controller hashes verified; no forwards.')
    else: main(args.resume_post)
