#!/usr/bin/env python3
"""Render authoritative vector outputs with Poppler at their exact insertion size."""
from pathlib import Path
import subprocess
from PIL import Image
import fitz

HERE=Path(__file__).resolve().parents[1]
def main():
    for i in range(1,6):
        src=HERE/f'pdf/figure{i}.pdf'
        for dpi in (96,180):
            out=HERE/f'qa/figure{i}_{dpi}dpi'
            subprocess.run(['pdftoppm','-r',str(dpi),'-singlefile','-png',str(src),str(out)],check=True)
            im=Image.open(str(out)+'.png')
            im.convert('L').save(HERE/f'qa/figure{i}_{dpi}dpi_gray.png')
    # Letter-size proof sheets preserve native physical dimensions; not a manuscript mock-up.
    proof=fitz.open()
    layouts=[[(1,63,46),(2,63,336)],[(3,63,45),(4,63,293)],[(5,63,70)]]
    for layout in layouts:
        page=proof.new_page(width=612,height=792)
        for i,x,y in layout:
            src=fitz.open(HERE/f'pdf/figure{i}.pdf');w,h=src[0].rect.width,src[0].rect.height
            page.show_pdf_page(fitz.Rect(x,y,x+w,y+h),src,0)
        page.insert_text((63,777),'Native MLSys width proof: single 3.25 in / double 6.75 in. Print at 100%.',fontsize=8)
    proof.save(HERE/'qa/insertion_proof.pdf',garbage=4,deflate=True,no_new_id=True)
    for p in range(len(proof)):
        pix=proof[p].get_pixmap(matrix=fitz.Matrix(96/72,96/72),colorspace=fitz.csGRAY)
        pix.save(HERE/f'qa/insertion_proof_page{p+1}_gray.png')
    print('Rendered all five candidates in color and grayscale at 96/180 dpi; three native-size proof pages.')

if __name__=='__main__':main()
