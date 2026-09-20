#!/usr/bin/env python3
"""Compare exact checkpoint vector artwork, prior candidates and selected assets.

No plot is reconstructed from a screenshot. OLD is clipped from the committed
manuscript PDF; plotting data remain exclusively repository tables/samples.
"""
from pathlib import Path
import json, hashlib
import fitz

HERE=Path(__file__).resolve().parents[1]
ROOT=HERE.parents[2]
BASE='1a11361f8526ec361e20dd6878d6e67352fb7bbd'
# PDF coordinates in points, top-left origin. Full column/text-block widths:
# 234 pt = 3.25 in; 486 pt = 6.75 in. Captions are reviewed separately.
REGIONS={1:(1,[307.44,65,541.44,264],'01_framework.tex'),
         2:(3,[55.44,65,541.44,219],'03_verification.tex'),
         3:(4,[55.44,232,289.44,375],'02_m4.tex'),
         4:(6,[55.44,65,541.44,261],'04_358h.tex'),
         5:(6,[55.44,330,289.44,503],'05_regimes.tex')}

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out=HERE/'comparison';out.mkdir(exist_ok=True)
    manuscript=ROOT/'paper/mlsys2027/manuscript/output/manuscript-v0.1.pdf'
    source=fitz.open(manuscript);proof=fitz.open();native=fitz.open();records=[]
    for i,(pn,coords,filename) in REGIONS.items():
        crop=fitz.Rect(coords);old=fitz.open();p=old.new_page(width=crop.width,height=crop.height)
        p.show_pdf_page(p.rect,source,pn,clip=crop)
        old.save(out/f'old_figure{i}.pdf',garbage=4,deflate=True,no_new_id=True)
        n=native.new_page(width=612,height=792)
        n.insert_text((63,32),f'OLD Figure {i}: actual checkpoint insertion width {crop.width/72:.2f} in',fontsize=10)
        n.show_pdf_page(fitz.Rect(63,60,63+crop.width,60+crop.height),old,0)
        n.insert_text((63,770),f'Vector crop from manuscript-v0.1.pdf, page {pn+1}; caption omitted.',fontsize=9)
        current=fitz.open(HERE/f'pdf/figure{i}.pdf');width=current[0].rect.width
        for stage,path in [('PRIOR candidate v0.2',out/f'prior_v02/figure{i}.pdf'),
                           ('SELECTED v0.3'+(' (appendix A1)' if i==5 else ''),HERE/f'pdf/figure{i}.pdf')]:
            other=fitz.open(path);old_h=crop.height*width/crop.width
            new_h=other[0].rect.height*width/other[0].rect.width
            height=max(612,old_h+new_h+174);page=proof.new_page(width=612,height=height)
            x=(612-width)/2
            page.insert_text((45,25),f'Figure {i}: OLD / {stage}',fontsize=12)
            page.insert_text((45,43),f'Both panels {width/72:.2f} in wide. Print at 100%; do not fit to page.',fontsize=9)
            scale=width/crop.width
            page.insert_text((x,67),f'OLD manuscript v0.1 (native {crop.width/72:.2f} in; scale {scale:.3f}x)',fontsize=9)
            page.show_pdf_page(fitz.Rect(x,77,x+width,77+old_h),old,0)
            y=77+old_h+30
            page.insert_text((x,y),stage,fontsize=10)
            page.show_pdf_page(fitz.Rect(x,y+12,x+width,y+12+new_h),other,0)
            page.insert_text((45,height-17),'Exact checkpoint artwork; no reconstructed values. Captions assessed in FIGURE_REVIEW.md.',fontsize=8)
        records.append(dict(figure=i,old_pdf=str(manuscript.relative_to(ROOT)),old_page_1based=pn+1,
            old_source=f'paper/mlsys2027/manuscript/figures/{filename}',crop_points=coords,
            old_native_width_in=crop.width/72,comparison_width_in=width/72,
            old_scale_for_equal_width=width/crop.width,
            prior_pdf_sha256=digest(out/f'prior_v02/figure{i}.pdf'),selected_pdf_sha256=digest(HERE/f'pdf/figure{i}.pdf')))
    proof.save(out/'OLD_NEW_COMPARISON.pdf',garbage=4,deflate=True,no_new_id=True)
    native.save(out/'OLD_NATIVE_WIDTH.pdf',garbage=4,deflate=True,no_new_id=True)
    for doc,prefix in [(proof,'comparison'),(native,'old_native')]:
        for idx,page in enumerate(doc):
            for cs,suffix in [(fitz.csRGB,'color'),(fitz.csGRAY,'gray')]:
                page.get_pixmap(matrix=fitz.Matrix(96/72,96/72),colorspace=cs).save(out/f'{prefix}_{idx+1:02d}_{suffix}.png')
    (out/'comparison_lock.json').write_text(json.dumps(dict(base_commit=BASE,
        manuscript_pdf_sha256=digest(manuscript),method='exact vector crop; equal-width scaling, with native OLD proof',
        figures=records),indent=2)+'\n')
    print('10 equal-width OLD/PRIOR and OLD/SELECTED pages; 5 native OLD pages; color + grayscale.')

if __name__=='__main__':main()
