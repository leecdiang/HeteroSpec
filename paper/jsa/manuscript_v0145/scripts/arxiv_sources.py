"""Compile a single arXiv document: main, shared references, supplement.

Identity and assembly follow arXiv:2610.03228v1. Scientific include files and
figures are byte-identical to the JSA author sources. Public front matter and
factual declarations are recorded separately from unresolved journal paperwork.
"""
from pathlib import Path
import hashlib
import json
import re
import tempfile
import zipfile
import fitz
from flat_sources import dependencies, run

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    main_text = (ROOT / 'main.tex').read_text()
    supplement = (ROOT / 'supplement.tex').read_text()
    title = re.search(r'\\title\{([^}]+)\}', main_text).group(1)
    abstract = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', main_text, re.S).group(1).strip()
    (OUT / 'arxiv-title-v0.14.5.txt').write_text(title + '\n')
    (OUT / 'arxiv-abstract-v0.14.5.txt').write_text(abstract + '\n')
    sources = sorted(set(dependencies('main') + dependencies('supplement')) - {'main.tex', 'supplement.tex', 'declarations.tex'})
    payload = {name: (ROOT / name).read_bytes() for name in sources}
    # The supplement uses a subset of the main bibliography. Keep all 18 entries
    # in the main reference list, so citations have one numbering across the PDF.
    bibkeys = lambda text: re.findall(r'\\bibitem[^\n]*\{([^}]+)\}', text)
    main_bbl = (ROOT / 'build/main.bbl').read_text()
    assert set(bibkeys((ROOT / 'build/supplement.bbl').read_text())) <= set(bibkeys(main_bbl))
    payload['arxiv.bbl'] = main_bbl.encode()
    public_declarations = r'''\section*{Manuscript preparation and reproducibility}
OpenAI ChatGPT/Codex was used to assist with restructuring and drafting text, source and bibliography checks, CPU analysis and plotting code, and the execution-architecture illustration. Quantitative figures are generated from the identified experimental exports, without generative replacement of observations. The author is responsible for the final manuscript.

Supplement \S S7 documents the frozen exports, source bindings and CPU-only checks used to reconstruct the figures and arithmetic. These checks do not rerun model inference or re-audit the private raw archives. No public deposit of the complete author-review evidence package is asserted here.
'''
    payload['declarations.tex'] = public_declarations.encode()
    s7_name = 'supplement/07_reproducibility.tex'
    s7_before = payload[s7_name].decode()
    s7_edits = [
        ('The author source package contains', 'The complete author-review source package contains'),
        (r'Compile \texttt{main.tex} or \texttt{supplement.tex} with pdfLaTeX using the supplied assets.',
         r'In that archive, compile \texttt{main.tex} or \texttt{supplement.tex}; the separate public arXiv source package compiles \texttt{arxiv.tex}. All use pdfLaTeX and the supplied assets.'),
        ('Authorship, affiliations, CRediT, funding, competing interests, permissions, permanent data/software access and the final AI-assistance statement require author confirmation.',
         'The public arXiv source package contains the manuscript dependencies; it does not include the complete evidence exports or private archives. Permanent public data/software access is not established by these local checks.')]
    s7_after = s7_before
    for before, after in s7_edits:
        assert s7_after.count(before) == 1
        s7_after = s7_after.replace(before, after)
    for pattern in [r'\d+(?:[.,]\d+)*', r'\\cite\w*\{[^}]*\}', r'(?<!\\)\$[^$]*\$']:
        assert re.findall(pattern, s7_before) == re.findall(pattern, s7_after)
    payload[s7_name] = s7_after.encode()
    helpers = r'''
% Separate supplement navigation, with continuous page and PDF destination IDs.
\makeatletter
\newcommand{\supplementtableofcontents}{\section*{\contentsname}\@starttoc{stoc}}
\newcommand{\startsupplementcontents}{%
  \let\arxivaddcontentsline\addcontentsline
  \renewcommand{\addcontentsline}[3]{%
    \def\arxivstream{##1}\def\arxivtoc{toc}%
    \ifx\arxivstream\arxivtoc
      \arxivaddcontentsline{stoc}{##2}{##3}%
    \else
      \arxivaddcontentsline{##1}{##2}{##3}%
    \fi}}
\makeatother
'''
    main_text = main_text.replace('pdfauthor={Author-review draft}', 'pdfauthor={Chengzhan Li}')
    main_text = main_text.replace('pdfsubject={JSA v0.14.5 author-review manuscript; not submitted}',
                                  'pdfsubject={Update prepared for arXiv:2610.03228; manuscript v0.14.5}')
    main_text = main_text.replace(r'\author{Author information pending confirmation}',
        r'''\author{Chengzhan Li}
\ead{chengzhan.li@std.uestc.edu.cn}
\address{University of Electronic Science and Technology of China}''')
    main_text = main_text.replace(r'\begin{document}', helpers + '\n' + r'\begin{document}')
    main_text = main_text.split(r'\end{document}')[0]
    sup_abstract = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', supplement, re.S).group(1).strip()
    sup_body = supplement.split(r'\renewcommand{\thesection}', 1)[1]
    sup_body = r'\renewcommand{\thesection}' + sup_body.split(r'\FloatBarrier', 1)[0]
    sup_body = sup_body.replace(r'\tableofcontents', r'\supplementtableofcontents')
    transitions = r'''
\clearpage
\startsupplementcontents
\setcounter{section}{0}
\setcounter{table}{0}
\setcounter{figure}{0}
\setcounter{equation}{0}
\renewcommand{\topfraction}{0.9}
\renewcommand{\bottomfraction}{0.8}
\renewcommand{\textfraction}{0.08}
\renewcommand{\floatpagefraction}{0.55}
\pdfbookmark[0]{Supplementary Material}{supplement-start}
\section*{Supplementary Material}
'''
    payload['arxiv.tex'] = (main_text + transitions + sup_abstract + '\n\n' + sup_body +
                           '\n' + r'\FloatBarrier' + '\n' + r'\end{document}' + '\n').encode()
    original_inputs = re.findall(r'\\input\{([^}]+)\}', (ROOT / 'main.tex').read_text() + supplement)
    assert re.findall(r'\\input\{([^}]+)\}', payload['arxiv.tex'].decode()) == original_inputs
    config = dict(process=dict(compiler='pdflatex'), sources=[dict(filename='arxiv.tex', usage='toplevel')])
    payload['00README.json'] = (json.dumps(config, indent=2) + '\n').encode()
    assert sum(name.endswith('.pdf') for name in payload) == 7
    assert not any(name.startswith(('evidence/', 'source_records/', 'historical_sources/', 'provenance/', 'output/')) for name in payload)
    archive_path = OUT / 'arxiv-source-v0.14.5.zip'
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 9, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    record = dict(version='v0.14.5', status='PASS', files=len(payload),
        package_sha256=sha(archive_path.read_bytes()), entry='arxiv.tex',
        published_baseline='https://arxiv.org/abs/2610.03228v1',
        identity_source='https://arxiv.org/pdf/2610.03228v1',
        author='Chengzhan Li', affiliation='University of Electronic Science and Technology of China',
        email='chengzhan.li@std.uestc.edu.cn', seven_vector_figures=True,
        shared_bibliography_entries=len(bibkeys(main_bbl)), private_evidence_included=False,
        unchanged_dependency_sha256={name: sha(payload[name]) for name in sources if name != s7_name},
        supplement_delivery_edits=dict(path=s7_name, before_sha256=sha(s7_before.encode()),
            after_sha256=sha(s7_after.encode()), replacements=s7_edits,
            numbers_equations_citations_equal=True),
        generated_entry_sha256=sha(payload['arxiv.tex']),
        public_declarations=public_declarations,
        journal_only_pending_forms_omitted=['CRediT roles','funding/interests confirmation prompts','public-deposit decision prompts'],
        submitted=False, live_arxiv_acceptance=False)
    with tempfile.TemporaryDirectory(prefix='jsa-v0145-arxiv-') as temporary:
        fresh = Path(temporary)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(fresh)
        for _ in range(4):
            result = run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error', '-file-line-error', 'arxiv.tex'], fresh)
        (OUT / 'arxiv-console.log').write_text(result.stdout + result.stderr)
        log = (fresh / 'arxiv.log').read_text(errors='replace')
        problems = re.findall(r'Overfull.*|.*undefined.*|.*multiply defined.*|.*Float too large.*|.*Missing character.*|.*destination with the same identifier.*|.*duplicate ignored.*', log, re.I)
        assert not problems, problems
        assert bibkeys((fresh / 'arxiv.bbl').read_text()) == bibkeys(main_bbl)
        stoc = (fresh / 'arxiv.stoc').read_text()
        assert len(re.findall(r'\\contentsline', stoc)) == 30
        fonts = run(['pdffonts', str(fresh / 'arxiv.pdf')], fresh).stdout
        assert 'Type 3' not in fonts
        for row in fonts.splitlines()[2:]:
            assert re.search(r'\s+yes\s+(?:yes|no)\s+(?:yes|no)\s+', row), row
        target = OUT / 'arxiv-combined-v0.14.5.pdf'
        target.write_bytes((fresh / 'arxiv.pdf').read_bytes())
        run(['pdftotext', '-layout', str(target), str(OUT / 'arxiv-combined-v0.14.5.txt')], fresh)
        with fitz.open(target) as pdf:
            texts = [p.get_text() for p in pdf]
            text = '\n'.join(texts)
            assert 'Author information pending confirmation' not in text
            assert 'await author confirmation' not in text
            assert all(value in text for value in ['Chengzhan Li', '1.742', '1.683', '1.035'])
            starts = [i + 1 for i, text in enumerate(texts) if 'Supplementary Material' in text]
            assert len(starts) == 1
            for i, page_text in enumerate(texts):
                assert page_text.strip().endswith(str(i + 1)), ('continuous printed page number', i + 1)
            for page in pdf:
                for link in page.get_links():
                    if 'page' in link:
                        assert 0 <= link['page'] < len(pdf)
            record['combined_pdf'] = dict(filename=target.name, sha256=sha(target.read_bytes()),
                pages=len(pdf), supplement_starts_on_pdf_page=starts[0],
                continuous_printed_page_numbers=True, supplementary_navigation_entries=30,
                internal_and_external_links=sum(len(p.get_links()) for p in pdf),
                bookmarks=len(pdf.get_toc()), overfull=0, undefined_references=0,
                duplicate_labels_or_targets=0, all_fonts_embedded=True, type3_fonts=0)
            (OUT / 'arxiv-comments-v0.14.5.txt').write_text(f'{len(pdf)} pages, 7 figures; expanded diagnosis, phase-scoped qualification and cost comparisons; includes supplementary material\n')
        # Compile the extracted sources again and compare exact PDF bytes.
        result = run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error', 'arxiv.tex'], fresh)
        assert sha((fresh / 'arxiv.pdf').read_bytes()) == record['combined_pdf']['sha256']
        record['repeat_compilation_pdf_bytes_equal'] = True
    record['boundary'] = 'Single-entry clean local compile; all research includes and figures are retained, with S7 delivery wording changes recorded separately. No live arXiv submission or new experiment.'
    (OUT / 'ARXIV_SOURCE_QA.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
