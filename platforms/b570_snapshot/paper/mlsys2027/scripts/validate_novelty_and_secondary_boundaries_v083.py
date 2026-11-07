#!/usr/bin/env python3
"""Check Phase-5 novelty, M4-control, and 358H-interface boundaries."""
from pathlib import Path
import json
import re
import subprocess
import sys

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[3]
MS = ROOT / 'paper/mlsys2027/manuscript'
BASE = 'd3ae7067fc5ff285d87238f8c48a7104ebfb349d'


def read(rel):
    return (MS / rel).read_text()


def original(rel):
    return subprocess.check_output(['git', 'show', f'{BASE}:paper/mlsys2027/manuscript/{rel}'], cwd=ROOT)


def check(condition, label):
    if not condition:
        raise AssertionError(label)
    print('PASS:', label)


def citations(text):
    return {key.strip() for group in re.findall(r'\\cite(?:p|t)?\{([^}]+)\}', text)
            for key in group.split(',')}


def main():
    related = read('sections/08_related_work.tex')
    old_related = original('sections/08_related_work.tex').decode()
    check(citations(related) == citations(old_related) and
          (MS / 'references.bib').read_bytes() == original('references.bib'),
          'Related Work uses exactly the existing citation keys and bibliography')
    check(not re.search(r'\b(first|first-ever|novelty)\b', related, re.I),
          'no firstness novelty claim')
    for key in ('lossless', 'compilerassisted', 'lever', 'aclheterospec'):
        check(key in citations(related), 'closest work retained: ' + key)
    check('prospectively qualifies specific RTX/B570 execution paths' in related and
          'freezes a B570 target-partition predictor before comparing complete reserved serialized trajectories' in related and
          'realized state-interface accounting' in related,
          'distinct qualification, prediction, and state-interface boundary')
    check('Slowdown and correctness gating are therefore established background' in related and
          'Numerical path dependence is not new here' in related and
          'Adaptive control is established prior work' in related,
          'adjacent prior-work territory acknowledged')
    main_tex = read('main.tex')
    abstract = main_tex.split(r'\begin{abstract}', 1)[1].split(r'\end{abstract}', 1)[0]
    intro = read('sections/01_introduction.tex')
    runtime = read('sections/07_runtime_codesign.tex')
    table = read('tables/07_runtime.tex')
    conclusion = read('sections/10_conclusion.tex')
    check('Guard reaches \\RTGuard$\\times$ post-prefill speedup over target-only' in abstract and
          'slower than fixed speculation' in abstract and 'no incremental control benefit is shown' in abstract,
          'abstract does not imply Guard beats fixed speculation')
    check('Guard is profitable against target-only' in runtime and
          'Guard had higher latency on this comparison' in runtime and
          'post-study paired secondary analysis' in runtime and
          'no incremental benefit over Always-Spec' in runtime,
          'runtime interpretation and post-study secondary status')
    check('Post-study paired secondary latency ratio' in table and
          table.index('Target / Guard') < table.index('Target / Always-Spec') < table.index('Guard / Always-Spec'),
          'Table 3 target-relative rows adjacent and adverse comparison visible')
    check('post-study paired secondary comparison favors fixed speculation' in conclusion and
          'no incremental control benefit is shown' in conclusion,
          'conclusion keeps M4 as supporting negative control')
    for rel in ('tables/runtime_values.tex', 'tables/values.tex', 'tables/direct_id_values.tex',
                'tables/07_runtime.tex', 'figures/04_358h.tex', 'figures/03_verification.tex'):
        check((MS / rel).read_bytes() == original(rel), 'frozen numeric/figure source: ' + rel)
    qa = json.loads((ROOT / 'paper/mlsys2027/evidence/RUNTIME_QA_V07.json').read_text())
    serialized = json.dumps(qa, sort_keys=True)
    for value in ('1.0270760219826773', '1.0129560055428655', '1.0435592653980876'):
        check(value in serialized, 'raw M4 paired value: ' + value)
    for value in (r'\RTGuard}{1.3114}', r'\RTGuardLo}{1.2487}', r'\RTGuardHi}{1.3787}',
                  r'\RTAlways}{1.3469}', r'\RTAlwaysLo}{1.2867}', r'\RTAlwaysHi}{1.4088}',
                  r'\RTGuardFaster}{24}', r'\RTAlwaysFaster}{36}', r'\RTTies}{0}'):
        check(value in read('tables/runtime_values.tex'), 'M4 headline value: ' + value)
    diagnoses = read('sections/05_diagnoses.tex')
    figure4 = read('figures/04_358h.tex')
    check('full committed-prefix replay/reconstruction and proposal' in diagnoses and
          'inseparable in the recorded timing' in diagnoses and
          '58.35' in figure4 and 'replay-plus-proposal call' in figure4 and
          'replay-only time is not measured' in figure4,
          '358H combined timed region, no replay-only percentage')
    check('No formal R2 performance run occurred' in runtime and
          'invalid for performance claims' in runtime and
          'later intervention stops at qualification' in conclusion,
          '358H later intervention has no formal performance endpoint')
    check(not re.search(r'(?:replay-only|replay alone|replay penalty)[^.]{0,50}58\.35|58\.35[^.]{0,50}(?:replay-only|replay alone|replay penalty)',
                        diagnoses + runtime + figure4, re.I),
          'no unsupported replay-only 58.35% assignment')
    contribution = re.search(r'Our three contributions are (.+?)\n\n', intro, re.S)
    check(bool(contribution) and all(f'({n})' in contribution.group(1) for n in (1, 2, 3)) and
          '(4)' not in contribution.group(1), 'exactly three headline contributions')
    check(abstract.index('fresh direct-ID studies') < abstract.index('target-only micro-batch-one predictor') <
          abstract.index('On 358H') and
          intro.index('Two prospectively frozen direct-ID studies') < intro.index('M4, RTX 5070 Ti Laptop') and
          '72/72 complete generated-token-ID sequences' in intro,
          'first-page qualification → frozen prediction → realized-cost story')
    check('72/72 predictor-to-live complete-ID agreement' in conclusion and
          'without a unique numerical cause' in conclusion,
          'Phase-4 B570 sufficiency claim retained')
    for name,count in [('manuscript',12),('appendix',8)]:
        path = MS / f'output/{name}-v0.8.3-phase5-preview.pdf'
        check(path.is_file() and len(PdfReader(path).pages) == count,
              f'{name} Phase-5 preview page count {count}')
    print('PASS: novelty and secondary-boundary validator')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('FAIL:', error, file=sys.stderr)
        sys.exit(1)
