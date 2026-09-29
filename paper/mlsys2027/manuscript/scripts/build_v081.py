#!/usr/bin/env python3
"""Build the v0.8.1 author-review artifacts and independently compile the source ZIP.

Document-only operations: no evidence regeneration, inference or timing tools.
Run with a Python environment containing pypdf and with latexmk/pdflatex/bibtex.
"""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys, tempfile, zipfile
from pypdf import PdfReader

HERE = Path(__file__).resolve().parents[1]
EVIDENCE = HERE.parent / 'evidence'
OUT = HERE / 'output'

def run(args, cwd, console, env=None):
    with open(console, 'ab') as log:
        subprocess.run(args, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
                       env=env, check=True)

def extract(label):
    root = Path(tempfile.mkdtemp(prefix=f'heterospec-v081-{label}-'))
    with zipfile.ZipFile(OUT/'overleaf-submission-readiness-v0.8.1.zip') as z:
        z.extractall(root)
    manifest = json.loads((root/'SHA256SUMS.json').read_text())
    for name, digest in manifest.items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest() == digest, name
    return root, manifest

run([sys.executable, str(HERE/'scripts/package_overleaf_v081.py')], HERE,
    OUT/'build-v0.8.1.console')
fresh, manifest = extract('fresh')
clean, second_manifest = extract('cleanzip')
assert manifest == second_manifest
for root in (fresh, clean):
    for name in ('main', 'appendix'):
        # Explicit plain latexmk command tests the ZIP's portable root dependencies.
        run(['latexmk', '-pdf', name+'.tex'], root, root/(name+'-build.console'))
(fresh/'hardware-only').mkdir()
args = ['pdflatex','-interaction=nonstopmode','-halt-on-error',
        '-output-directory=hardware-only','-jobname=hardware-only',
        r'\def\HardwareOnly{1}\input{main.tex}']
run(args, fresh, fresh/'hardware-build.console')
env = os.environ.copy(); env['BIBINPUTS'] = str(fresh)+':'
run(['bibtex','hardware-only/hardware-only'], fresh, fresh/'hardware-build.console', env)
for _ in range(2):
    run(args, fresh, fresh/'hardware-build.console')
for source, target in [('main.pdf','manuscript-v0.8.1.pdf'),
                       ('appendix.pdf','appendix-v0.8.1.pdf'),
                       ('hardware-only/hardware-only.pdf','hardware-only-v0.8.1.pdf')]:
    shutil.copyfile(fresh/source, OUT/target)
env = os.environ.copy(); env['HETEROSPEC_V081_BUILD'] = str(fresh)
run([sys.executable,str(HERE/'scripts/qa_pdf_v081.py')], HERE,
    OUT/'build-v0.8.1.console', env)
comparison = {}
for name in ('main','appendix'):
    a,b = PdfReader(fresh/(name+'.pdf')), PdfReader(clean/(name+'.pdf'))
    at,bt = [p.extract_text() for p in a.pages], [p.extract_text() for p in b.pages]
    assert len(a.pages)==len(b.pages) and at==bt, name
    comparison[name] = {'pages':len(a.pages), 'extracted_text_equal':True,
                       'text_sha256':hashlib.sha256('\n'.join(at).encode()).hexdigest()}
report = {'status':'PASS', 'fresh_directory':str(fresh),'clean_zip_directory':str(clean),
          'manifest_files':len(manifest),'all_manifest_hashes_match':True,
          'comparison':comparison,'zip_sha256':hashlib.sha256((OUT/'overleaf-submission-readiness-v0.8.1.zip').read_bytes()).hexdigest(),
          'scope':'Document compilation only; no inference, measurement or evidence regeneration.'}
(EVIDENCE/'CLEAN_ZIP_QA_V081.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'PASS','fresh':str(fresh),'clean':str(clean),'comparison':comparison}))
