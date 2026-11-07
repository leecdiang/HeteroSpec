#!/usr/bin/env python3
"""Check the Phase-3 evidence labels against active source and built previews."""
from pathlib import Path
import re
import sys

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[3]
MS = ROOT / 'paper/mlsys2027/manuscript'
OUT = MS / 'output'


def read(rel):
    return (MS / rel).read_text()


def check(ok, label):
    if not ok:
        raise AssertionError(label)
    print('PASS:', label)


def pdftext(name):
    path = OUT / name
    check(path.is_file(), name + ' exists')
    return '\n'.join(page.extract_text() or '' for page in PdfReader(path).pages)


def main():
    headline = read('tables/02_headlines_v05.tex')
    rows = [line for line in headline.splitlines() if line.startswith(('M4 ', 'CPU to RTX', 'RTX 5070', 'B570 serialized', '358H '))]
    check(len(rows) == 7 and all('Text-path &' in x for x in rows[:5]) and
          all('Direct-ID &' in x for x in rows[5:]), 'Table 2 row-level historical/direct-ID endpoints')
    check('historical text-path agreement' in read('sections/02_framework.tex').lower() and
          'predictor-to-live' in read('sections/02_framework.tex').lower(), 'three-class framework key')
    a3 = read('tables/06_verification_lookup_v05.tex')
    a4 = read('tables/05_regimes_v083_rows.tex')
    check('Historical text-path status' in a3 and not re.search(r'\bExact\b', a3), 'historical A3 lookup')
    check('Evidence endpoint / gate' in a4 and len(re.findall(r'^.*Text-path.*\\\\$', a4, re.M)) == 6 and
          len(re.findall(r'^358H .*Direct-ID.*\\\\$', a4, re.M)) == 2 and
          not re.search(r'\bExact\b', a4), 'historical/direct-ID A4 inventory')
    fresh = read('tables/08_direct_id.tex')
    values = read('tables/direct_id_values.tex')
    check('Fresh direct-ID qualification' in fresh and fresh.count('Direct-ID sequences') == 4 and
          all(x in values for x in (r'\DIRTXBatchedPairs}{75}', r'\DIRTXSerializedPairs}{90}',
                                      r'\DIBFastPairs}{60}', r'\DIBSerializedPairs}{78}')),
          'fresh RTX/B570 direct-ID labels and frozen 75/90, 90/90, 60/90, 78/90')
    diagnoses = read('sections/05_diagnoses.tex')
    appendix = read('appendix.tex')
    check('Predictor-to-live complete-ID agreement is 72/72' in diagnoses and
          'Reference-to-live direct-ID qualification is 60/72' in diagnoses and
          'BLOCKED' in diagnoses and
          '72/72 predictor-to-live complete-ID agreement' in appendix and
          'Reference-to-live direct-ID qualification is 60/72 and BLOCKED' in appendix,
          'B570 prediction 72/72 distinct from blocked reference qualification 60/72')
    check(all(x in diagnoses + appendix for x in ('24/24', '12/12', 'four prompts')),
          'B570 mechanism ancillary values unchanged')
    check('direct-ID sequence equality' in read('sections/04_outcomes.tex') and
          'Direct-ID' in a4 and '90/90' in a4, '358H direct-ID 90/90 retained')
    runtime = read('sections/07_runtime_codesign.tex') + read('tables/07_runtime.tex')
    check('prospective m4' in runtime.lower() and 'direct-ID sequence equality' in runtime,
          'prospective M4 direct-ID output endpoint')
    figure = read('figures/03_verification.tex')
    plot = read('figures/presentation_v07/plot.py')
    for label in ('Historical target-forward proxy', 'Different runs / contexts',
                  'Fresh direct-ID qualification', 'No matching fresh latency endpoint'):
        check(label in plot, 'Figure 3 source label: ' + label)
    check('not a matched cost--qualification experiment' in figure and
          'does not retrospectively authorize historical timing' in figure,
          'Figure 3 caption comparator boundary')
    mainpdf = pdftext('manuscript-v0.8.3-phase3-preview.pdf')
    apppdf = pdftext('appendix-v0.8.3-phase3-preview.pdf')
    for label in ('Historical target-forward proxy', 'Different runs / contexts',
                  'Fresh direct-ID qualification', 'No matching fresh latency endpoint'):
        check(label in mainpdf, 'Figure 3 rendered label: ' + label)
    check(all(x in mainpdf + apppdf for x in ('75/90', '90/90', '60/90', '78/90', '72/72', '60/72')),
          'known direct-ID and prediction counts appear in PDFs')
    check('Text-path' in mainpdf and 'Direct-ID' in mainpdf and
          'Text-path' in apppdf and 'Direct-ID' in apppdf,
          'rendered row-level endpoint labels')
    for pattern in (r'historical[^.]{0,80}\bexact pairs\b', r'72/72\s+qualification',
                    r'serialized\s+exact\b'):
        check(not re.search(pattern, mainpdf + '\n' + apppdf, re.I | re.S),
              'no ambiguous PDF pattern: ' + pattern)
    check(len(PdfReader(OUT / 'manuscript-v0.8.3-phase3-preview.pdf').pages) == 12,
          'main 10 body plus 2 references')
    print('PASS: evidence-class validator')


if __name__ == '__main__':
    try:
        main()
    except (AssertionError, ImportError) as error:
        print('FAIL:', error, file=sys.stderr)
        sys.exit(1)
