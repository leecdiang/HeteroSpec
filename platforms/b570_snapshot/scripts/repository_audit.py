from __future__ import annotations
import os, re
from collections import Counter
from pathlib import Path

ROOT=Path(os.environ.get('HETEROSPEC_ROOT',Path(__file__).resolve().parents[1]))
(ROOT/'docs').mkdir(exist_ok=True)
SKIP={'.git'}; files=[p for p in ROOT.rglob('*') if p.is_file() and not any(x in SKIP for x in p.parts)]
rel=lambda p:p.relative_to(ROOT).as_posix()
top=', '.join(sorted(p.name for p in ROOT.iterdir()))
large=sorted((p for p in files if p.stat().st_size>10*1024*1024),key=lambda p:p.stat().st_size,reverse=True)
exts=['.safetensors','.gguf','.onnx','.bin','.pt','.pth','.npy','.npz','.jsonl','.csv']
lines=['# Repository audit','',f'- Top-level entries: {top}',f'- File count: {len(files):,}',f'- Total size: {sum(p.stat().st_size for p in files)/1024**3:.2f} GiB','',
'## Large files','', '| Path | MiB | >50 MiB | >100 MiB |','|---|---:|---:|---:|']
for p in large: lines.append(f'| `{rel(p)}` | {p.stat().st_size/1024**2:.1f} | {"yes" if p.stat().st_size>50*1024**2 else "no"} | {"yes" if p.stat().st_size>100*1024**2 else "no"} |')
lines += ['','## File classes','', '| Class | Count |','|---|---:|']
for e in exts: lines.append(f'| `{e}` | {sum(p.suffix.lower()==e for p in files)} |')
for label,name in [('Virtual environments','.venv*'),('Hugging Face cache','hf-cache'),('Model store','models')]:
 paths=list(ROOT.glob(name)); lines.append(f'| {label} | {sum(1 for x in paths for p in x.rglob("*") if p.is_file()):,} files |')
lines.append(f'| Tracked raw telemetry | {sum(1 for p in files if p.name == "telemetry.csv"):,} files |')
text_ext={'.py','.ps1','.bat','.cmd','.yaml','.yml','.json','.md','.toml','.txt','.cff'}; hits=[]
for p in files:
 if p.suffix.lower() not in text_ext or p.stat().st_size>20*1024*1024: continue
 try:s=p.read_text(encoding='utf-8',errors='ignore')
 except OSError:continue
 if p == Path(__file__): continue
 s=s.replace('/Users/<name>','').replace('/home/<name>','')
 if re.search(r'(?:[A-Z]:\\\\Users\\\\[^\\\\]+|/Users/[^/]+|/home/[^/]+|D:\\HeteroSpec-PC)',s):hits.append(rel(p))
lines += ['','## Absolute-path audit','',f'- Files containing a macOS/Linux user path, original project root, or Windows user path: {len(hits)}.', '- Findings in authoritative or historical records may be retained for provenance, but must be reviewed for privacy before public release.']
lines += [f'  - `{x}`' for x in hits]
lines += ['','## Protection decision','', '- No source data was deleted.', '- Models, caches, virtual environments, runs, archives, raw logs, general raw telemetry, and machine profiles are excluded through `.gitignore`.', '- The tracked M4 HumanEval `telemetry.csv` is the documented authoritative raw-data exception.', '- Processed analysis CSVs, reports, figures, portable scripts, configs, and provenance IDs are candidates for Git.']
(ROOT/'repo_audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

candidate_roots=['analysis','artifacts','benchmarks','configs','docs','paper','reports','requirements','schemas','src','scripts']
candidates=[p for n in candidate_roots if (ROOT/n).exists() for p in (ROOT/n).rglob('*') if p.is_file() and p.suffix.lower() in text_ext and not (p.parent==ROOT/'scripts' and p.suffix.lower() in {'.ps1','.cmd','.bat'})]
candidates += [ROOT/n for n in ['README.md','CONTRIBUTING.md','LICENSE_PLACEHOLDER.md','CITATION.cff','pyproject.toml','.gitignore','repo_audit.md'] if (ROOT/n).exists()]
patterns={'HF token':r'hf_[A-Za-z0-9]{12,}','GitHub token':r'(?:ghp_|github_pat_)[A-Za-z0-9_]+','OpenAI key':r'sk-[A-Za-z0-9]{12,}','Authorization':r'(?i)authorization\s*[:=]','Credential assignment':r'(?i)(?:password|passwd|api_key|secret)\s*=|token=','Email':r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b','Windows user path':r'[A-Z]:\\Users\\[^\\]+','macOS user path':r'/Users/[^/]+','Linux user path':r'/home/[^/]+','Original absolute root':r'D:\\HeteroSpec-PC'}
find=[]
for p in candidates:
 if p.stat().st_size>20*1024*1024:continue
 s=p.read_text(encoding='utf-8',errors='ignore')
 if p == Path(__file__):
  continue
 s=s.replace('/Users/<name>','').replace('/home/<name>','')
 for name,pat in patterns.items():
  if p == Path(__file__) and name == 'Credential assignment':
   continue
  if re.search(pat,s):find.append((rel(p),name))
sec=['# Pre-publication security check','', '## Checked patterns','']+[f'- {x}' for x in patterns]+['','## Findings','']
sec += [f'- `{p}`: {kind}' for p,kind in find] or ['- No candidate-file matches.']
sec += ['','## Actions','', '- Large/local asset directories are ignored.', '- Secret values are never copied into this report.', '- Root PowerShell/CMD wrappers remain local when they contain machine-specific paths.', '- The M4 authoritative run record retains local model/data paths for provenance; review or redact the username-bearing path before public release.', '', '## Remaining TODO','', '- Choose a license and finalize author metadata.', '- Decide and document the public-release treatment of local provenance paths.', '- Run a final scan immediately before public release.']
(ROOT/'docs'/'PRE_PUBLICATION_SECURITY_CHECK.md').write_text('\n'.join(sec)+'\n',encoding='utf-8')
print({'files':len(files),'large':len(large),'candidate_findings':len(find)})
