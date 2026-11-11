#!/usr/bin/env python3
"""Persisted-PDF validation, metadata/anonymity/font checks and all-page raster review."""
import hashlib,json,re,subprocess
from pathlib import Path
import fitz
from PIL import Image,ImageOps,ImageDraw
HERE=Path(__file__).resolve().parents[1];REV=HERE.parent/'reviews/reconstruction_v010';QA=HERE.parents[2]/'tmp/qa-v010/render'
def main():
 QA.mkdir(parents=True,exist_ok=True);report={'documents':{},'visual_review':'PENDING'}
 for stem in ['manuscript','appendix']:
  p=HERE/'output'/(stem+'-v0.10.0.pdf');raw=p.read_bytes();assert raw.startswith(b'%PDF') and b'%%EOF' in raw[-1024:]
  doc=fitz.open(p);texts=[];pngs=[];fontrows=[]
  for i,page in enumerate(doc):
   text=page.get_text();texts.append(text)
   pix=page.get_pixmap(matrix=fitz.Matrix(1.35,1.35),alpha=False);png=QA/f'{stem}-{i+1:02}.png';pix.save(png);pngs.append(png)
   for f in page.get_fonts():fontrows.append(f)
  joined='\n'.join(texts)
  assert not re.search(r'leecdiang|YinnHuu|yinhu360|/workspace/|C:\\\\Users|github\.com/leecdiang',joined,re.I)
  assert 'Anonymous' in str(doc.metadata)
  fonts=subprocess.check_output(['pdffonts',str(p)],text=True)
  assert ' no ' not in '\n'.join(fonts.splitlines()[2:]),fonts
  report['documents'][stem]={'pages':len(doc),'sha256':hashlib.sha256(raw).hexdigest(),'text_sha256':hashlib.sha256(joined.encode()).hexdigest(),'metadata':doc.metadata,'identifying_pattern_scan':'PASS','fonts':fonts,'all_pages_rendered':len(pngs)}
  for start in range(0,len(pngs),6):
   canvas=Image.new('RGB',(1260,990),'#eeeeee');draw=ImageDraw.Draw(canvas)
   for j,png in enumerate(pngs[start:start+6]):
    im=Image.open(png);im.thumbnail((390,440));x=(j%3)*420+(420-im.width)//2;y=(j//3)*490+25;canvas.paste(im,(x,y));draw.text((x,y-18),f'{stem} page{start+j+1}',fill='black')
   canvas.save(QA/f'{stem}-overview-{start//6+1}.png')
 (REV/'PDF_QA.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'AUTOMATED_PASS_VISUAL_PENDING','documents':{k:{'pages':v['pages'],'sha256':v['sha256']} for k,v in report['documents'].items()},'render_dir':str(QA)}))
if __name__=='__main__':main()
