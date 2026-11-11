"""Portable complete build with an existing Tectonic executable; no inference."""
from pathlib import Path
import argparse,json,shutil,subprocess,sys,tempfile,zipfile
from pypdf import PdfReader
HERE=Path(__file__).resolve().parents[1];E=HERE.parent/'evidence'
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--tectonic',required=True,type=Path)
    args=parser.parse_args();engine=args.tectonic.resolve()
    style=HERE/'vendor/official/mlsys2025style';build=HERE/'build';build.mkdir(exist_ok=True)
    def compile(root,source,out,paths):
        out.mkdir(parents=True,exist_ok=True)
        command=[str(engine),'--keep-logs','--keep-intermediates','-o',str(out)]
        for path in paths:command+=['-Z','search-path='+str(path)]
        subprocess.run(command+[str(source)],cwd=root,check=True)
    for source in ('main','appendix'):
        compile(HERE,HERE/(source+'.tex'),build,[style])
        shutil.copyfile(build/(source+'.pdf'),HERE/'output'/('manuscript-v0.7.pdf' if source=='main' else 'appendix-v0.7.pdf'))
    hardware=build/'hardware-only';hardware.mkdir(exist_ok=True)
    wrapper=hardware/'hardware-only.tex';wrapper.write_text(r'\def\HardwareOnly{1}\input{main.tex}'+'\n')
    compile(HERE,wrapper,hardware,[HERE,style])
    shutil.copyfile(hardware/'hardware-only.pdf',HERE/'output/hardware-only-v0.7.pdf')
    subprocess.run([sys.executable,'scripts/package_overleaf.py'],cwd=HERE,check=True)
    checks=[]
    with tempfile.TemporaryDirectory(prefix='heterospec-source-v07-') as temporary:
        root=Path(temporary)
        with zipfile.ZipFile(HERE/'output/overleaf-direct-id-integration-v0.7.zip') as package:package.extractall(root)
        for source in ('main','appendix'):
            compile(root,root/(source+'.tex'),root/'build',[])
            original=PdfReader(build/(source+'.pdf'));clean=PdfReader(root/'build'/(source+'.pdf'))
            assert len(original.pages)==len(clean.pages)
            assert [p.extract_text() for p in original.pages]==[p.extract_text() for p in clean.pages]
            checks.append(source+' clean source ZIP page count/text matches')
    (E/'DIRECT_ID_BUILD_QA_V07.json').write_text(json.dumps({'status':'PASS','engine':'Tectonic','checks':checks},indent=2)+'\n')
    print('Full, appendix, hardware-only and clean source ZIP builds PASS.')
if __name__=='__main__':main()
