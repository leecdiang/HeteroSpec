#!/usr/bin/env python3
"""Independent OLD/NEW reconciliation; consumes TeX data, not rendered pixels."""
from pathlib import Path
import hashlib,json,re
import numpy as np
import pandas as pd
import fitz

HERE=Path(__file__).resolve().parents[1];ROOT=HERE.parents[2]
OLD=ROOT/'paper/mlsys2027/manuscript/figures'
def main():
    d=lambda p:pd.read_csv(p,sep=r'\s+',float_precision='round_trip')
    new=lambda f:pd.read_csv(HERE/'data'/f,float_precision='round_trip')
    m4=d(OLD/'02_m4_data.dat');m=new('figure3_workloads.csv')
    np.testing.assert_allclose(m4[['mean','low','high']],m[['speedup','ci_low','ci_high']],rtol=1e-14)
    iso=d(OLD/'04_isolated.dat');n=new('figure4_isolated.csv')
    for dev in ['CPU','NPU']:
        np.testing.assert_allclose(iso[dev],n[n.device==dev].sort_values('context').tokens_s,rtol=1e-14)
    old=d(OLD/'04_realized.dat');n=new('figure4_realized.csv')
    np.testing.assert_allclose(old[['draft','target','residual']],n[['draft_s','target_s','residual_s']],rtol=1e-14)
    coordinates=re.findall(r'coordinates\s*\{([^}]+)\}',(OLD/'03_coordinates.tex').read_text())
    micro=new('figure2_micro_cells.csv')
    paths=['M4 Metal','RTX batched','RTX serialized','B570 fast','B570 serialized']
    for path,group in zip(paths,coordinates):
        vals=[float(x) for x,_ in re.findall(r'\(([\d.]+),([\d.]+)\)',group)]
        np.testing.assert_allclose(sorted(vals),sorted(micro[micro.path==path].v2_micro),rtol=0,atol=5e-5)
    lock=json.loads((HERE/'comparison/comparison_lock.json').read_text())
    assert hashlib.sha256((ROOT/lock['figures'][0]['old_pdf']).read_bytes()).hexdigest()==lock['manuscript_pdf_sha256']
    pdf=fitz.open(HERE/'comparison/OLD_NEW_COMPARISON.pdf');assert len(pdf)==10
    for row in lock['figures']:
        i=row['figure'];p=HERE/f'pdf/figure{i}.pdf'
        assert hashlib.sha256(p.read_bytes()).hexdigest()==row['selected_pdf_sha256']
        for stage in [0,1]:
            page=pdf[2*(i-1)+stage]
            # Actual placed PDF form bounds are a geometrical check independent
            # of compare.py's recorded width. Nested source forms are ignored.
            placed=[fitz.Rect(x[3]) for x in page.get_xobjects() if x[2]==0]
            assert len(placed)==2
            np.testing.assert_allclose([x.width/72 for x in placed],row['comparison_width_in'],atol=1e-5)
    result=dict(status='PASS',old_figures=5,comparison_pages=10,
        findings=['OLD M4 estimates and CIs equal NEW at full precision.',
            'OLD six Phase-1 medians and six Phase-3 component means equal NEW at full precision.',
            'OLD 11 micro cells equal NEW to original printed precision (B570 fast rounded to four decimals).',
            'No scientific numerical discrepancy found; decisions concern narrative, status encoding and readability.',
            'All OLD/NEW panel placements independently verified to use equal physical widths.',
            'OLD crops are original vector objects, not screenshot reconstructions.'],
        limitation='No manuscript prose or page-layout integration claimed; native OLD proof documents scale changes.')
    (HERE/'qa/comparison_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: OLD/NEW source numbers, exact PDF hashes, and all 20 placed panel widths.')
if __name__=='__main__':main()
