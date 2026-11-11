#!/usr/bin/env python3
"""Validate Phase-4 claim scope and first-page positioning against its starting commit."""
from pathlib import Path
import re
import subprocess
import sys

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[3]
MS = ROOT / 'paper/mlsys2027/manuscript'
BASE = '3b6d7eee8888f96c71835b0b15eb1c7cb074a038'
TITLE = 'Execution-Path Qualification and Realized Costs in Speculative Decoding on Consumer Systems'


def source(rel):
    return (MS / rel).read_text()


def verify(condition, message):
    if not condition:
        raise AssertionError(message)
    print('PASS:', message)


def unchanged(rel):
    current = (ROOT / rel).read_bytes()
    original = subprocess.check_output(['git', 'show', f'{BASE}:{rel}'], cwd=ROOT)
    return current == original


def main():
    main_tex = source('main.tex')
    abstract = main_tex.split(r'\begin{abstract}', 1)[1].split(r'\end{abstract}', 1)[0]
    intro = source('sections/01_introduction.tex')
    diagnoses = source('sections/05_diagnoses.tex')
    synthesis = source('sections/06_synthesis.tex')
    conclusion = source('sections/10_conclusion.tex')
    verify(r'\mlsystitle{' + TITLE + '}' in main_tex, 'formal title unchanged')
    for label in ('72/72', 'complete generated-token-ID sequences', '24 reserved prompts',
                  'tested B570 stack', 'frozen before reserved live outcomes',
                  'reference-divergent trajectories', 'target-partition sufficiency'):
        verify(label in abstract, 'abstract: ' + label)
    verify('without identifying a unique numerical cause' in abstract and
           not re.search(r'(?<!without identifying a )\b(?:root cause|universal rule|unique cause established)\b', abstract, re.I),
           'abstract distinguishes sufficient path from unique numerical cause')
    contribution = re.search(r'Our three contributions are (.+?)\n\n', intro, re.S)
    verify(bool(contribution) and all(f'({i})' in contribution.group(1) for i in (1, 2, 3)) and
           '(4)' not in contribution.group(1), 'exactly three headline contributions')
    verify('fresh direct-ID' in contribution.group(1) and
           'prospectively frozen B570 target-partition predictor' in contribution.group(1) and
           '72/72 held-out complete-sequence agreement' in contribution.group(1) and
           'realized 358H state-interface cost' in contribution.group(1),
           'qualification, frozen prediction, realized-cost contribution order')
    verify(intro.index('Two prospectively frozen direct-ID studies') <
           intro.index('M4, RTX 5070 Ti Laptop') < intro.index('Our three contributions'),
           'first-page story order')
    verify('separately frozen consumer-system case studies, not a matched hardware ranking' in intro,
           'case-study scope versus hardware ranking')
    verify(r'\subsection{Controlled B570 target-partition sufficiency}' in diagnoses and
           'mechanism isolation' not in diagnoses, 'Section 5 heading calibrated')
    for name, text in [('abstract', abstract), ('introduction', intro), ('Section 5', diagnoses),
                       ('synthesis', synthesis), ('conclusion', conclusion)]:
        verify(('B570' in text and any(word in text.lower() for word in ('sufficien', 'reproduc', 'predict'))),
               name + ' B570 headline uses predictive/sufficiency language')
    verify('on the tested B570 configuration' in diagnoses and
           'On the tested B570 stack' in synthesis and conclusion,
           'B570 headline scope remains tested configuration/stack')
    verify('without a unique numerical cause' in conclusion and
           '72/72 predictor-to-live complete-ID agreement' in conclusion,
           'conclusion calibrates the 72/72 mechanism endpoint')
    verify('one B570 platform, model pair, runtime/build, greedy $k=2$, HumanEval workload, and 24 reserved prompts' in
           source('sections/09_limitations.tex'), 'full B570 scope retained in limitations')
    protected = [
        'paper/mlsys2027/manuscript/sections/08_related_work.tex',
        'paper/mlsys2027/manuscript/references.bib',
        'paper/mlsys2027/manuscript/tables/values.tex',
        'paper/mlsys2027/manuscript/tables/runtime_values.tex',
        'paper/mlsys2027/manuscript/tables/direct_id_values.tex',
        'paper/mlsys2027/manuscript/figures/03_verification.tex',
        'paper/mlsys2027/manuscript/figures/presentation_v07/plot.py',
        'paper/mlsys2027/manuscript/figures/presentation_v07/pdf/verification.pdf',
        'paper/mlsys2027/manuscript/figures/presentation_v07/svg/verification.svg',
    ]
    for rel in protected:
        verify(unchanged(rel), 'unchanged: ' + rel)
    preview = MS / 'output/manuscript-v0.8.3-phase4-preview.pdf'
    verify(preview.is_file() and len(PdfReader(preview).pages) == 12,
           'phase-4 main preview: 10 body plus 2 reference pages')
    rendered = '\n'.join(page.extract_text() or '' for page in PdfReader(preview).pages)
    verify(all(value in rendered for value in
               ('75/90', '90/90', '60/90', '78/90', '36/36', '72/72', '60/72', '24/24', '12/12')) and
           'four prompts' in diagnoses,
           'RTX/B570 qualification and mechanism values retained')
    print('PASS: claim-calibration validator')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('FAIL:', error, file=sys.stderr)
        sys.exit(1)
