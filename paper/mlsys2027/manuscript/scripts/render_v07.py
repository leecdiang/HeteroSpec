"""Render every delivered page plus actual PDF Figure 3 at native scale."""
from pathlib import Path
import hashlib,json
import fitz
from PIL import Image,ImageOps,ImageDraw
HERE=Path(__file__).resolve().parents[1];E=HERE.parent/'evidence';QA=HERE/'build/qa_v07'
def main():
    QA.mkdir(parents=True,exist_ok=True);rendered={}
    for name,filename in [('main','manuscript-v0.7.pdf'),('appendix','appendix-v0.7.pdf'),('hardware','hardware-only-v0.7.pdf')]:
        source=HERE/'output'/filename;doc=fitz.open(source);images=[]
        # Remove only surplus renders from earlier drafts of this same artifact.
        for stale in QA.glob(f'{name}-[0-9][0-9].png'):
            if int(stale.stem.rsplit('-',1)[1]) > len(doc): stale.unlink()
        for stale in QA.glob(f'{name}-contact-*.png'):
            if int(stale.stem.rsplit('-',1)[1]) > (len(doc)+5)//6: stale.unlink()
        for index,page in enumerate(doc,1):
            path=QA/f'{name}-{index:02}.png';page.get_pixmap(dpi=150,alpha=False).save(path);images.append(path)
        sheets=[]
        for offset in range(0,len(images),6):
            subset=images[offset:offset+6];canvas=Image.new('RGB',(1100,3*740),'#dddddd');draw=ImageDraw.Draw(canvas)
            for pos,path in enumerate(subset):
                im=Image.open(path);im.thumbnail((535,700));x=(pos%2)*550+7;y=(pos//2)*740+25
                canvas.paste(im,(x,y));draw.text((x,y-18),f'{name} page {offset+pos+1}',fill='black')
            sheet=QA/f'{name}-contact-{offset//6+1}.png';canvas.save(sheet);sheets.append(str(sheet.relative_to(HERE)))
        rendered[name]={'pdf_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'pages':len(images),
                        'individual_page_images':[str(p.relative_to(HERE)) for p in images],'contact_sheets':sheets,'dpi':150}
    figure=HERE/'figures/presentation_v07';doc=fitz.open(figure/'pdf/verification.pdf')
    for dpi in (96,200):
        path=figure/f'qa/verification_pdf_color_{dpi}.png';doc[0].get_pixmap(dpi=dpi,alpha=False).save(path)
        Image.open(path).convert('L').save(figure/f'qa/verification_pdf_grayscale_{dpi}.png')
    (E/'DIRECT_ID_RENDERED_PAGES_V07.json').write_text(json.dumps({'status':'RENDERED_AWAITING_VISUAL_INSPECTION','artifacts':rendered},indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Rendered every delivered page and actual vector Figure 3; visual inspection required.')
if __name__=='__main__':main()
