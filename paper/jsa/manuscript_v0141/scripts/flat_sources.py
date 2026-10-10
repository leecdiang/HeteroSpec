"""Create and verify separate flat Elsevier source archives, without uploading."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dependencies(entry):
    """Only the editable TeX/bibliography/class and referenced PDF artwork."""
    found = set()

    def visit(relative):
        path = ROOT / relative
        assert path.is_file(), relative
        if relative in found:
            return
        found.add(relative)
        if path.suffix != '.tex':
            return
        text = path.read_text()
        for target in re.findall(r'\\input\{([^}]+)\}', text):
            visit(target if target.endswith('.tex') else target + '.tex')
        for target in re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}', text):
            visit(target)

    visit(entry + '.tex')
    found.update(['references.bib', 'elsarticle.cls', 'elsarticle-num.bst'])
    return sorted(found)


def flat_name(relative):
    if '/' not in relative:
        return relative
    path = Path(relative)
    return '-'.join(path.with_suffix('').parts).replace('_', '-') + path.suffix


def rewrite(text, mapping):
    for old, new in sorted(mapping.items(), key=lambda x: -len(x[0])):
        text = text.replace('{' + old + '}', '{' + new + '}')
        if old.endswith('.tex'):
            text = text.replace('{' + old[:-4] + '}', '{' + new[:-4] + '}')
    return text


def run(args, directory):
    env = os.environ.copy()
    env.update(SOURCE_DATE_EPOCH='1791504000', FORCE_SOURCE_DATE='1', TZ='UTC')
    return subprocess.run(args, cwd=directory, env=env, text=True,
                          capture_output=True, check=True)


def main():
    expected = json.loads((OUT / 'BUILD_QA.json').read_text())
    record = dict(version='v0.14.1', method='separate flat ZIPs extracted to empty directories and compiled',
                  uploaded_to_editorial_manager=False, editorial_manager_acceptance=False,
                  packages={})
    for entry in ['main', 'supplement']:
        sources = dependencies(entry)
        mapping = {name: flat_name(name) for name in sources}
        assert len(set(mapping.values())) == len(mapping)
        assert all('/' not in name and name.count('.') == 1 for name in mapping.values())
        assert len({Path(name).stem for name in mapping.values()}) == len(mapping)
        filename = f'editorial-manager-{entry}-flat-source-v0.14.1.zip'
        archive_path = OUT / filename
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for old, new in mapping.items():
                data = (ROOT / old).read_bytes()
                if old.endswith('.tex'):
                    data = rewrite(data.decode(), mapping).encode()
                info = zipfile.ZipInfo(new, date_time=(2026, 10, 9, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, data)
        with tempfile.TemporaryDirectory(prefix=f'jsa-v0141-flat-{entry}-') as temporary:
            fresh = Path(temporary)
            with zipfile.ZipFile(archive_path) as archive:
                assert all('/' not in name for name in archive.namelist())
                archive.extractall(fresh)
            result = run(['latexmk', '-pdf', '-interaction=nonstopmode', '-halt-on-error',
                          '-file-line-error', '-outdir=build', entry + '.tex'], fresh)
            (OUT / f'flat-{entry}-console.log').write_text(result.stdout + result.stderr)
            log = (fresh / 'build' / (entry + '.log')).read_text(errors='replace')
            problems = re.findall(r'Overfull.*|.*undefined.*|.*multiply defined.*|.*Float too large.*|.*Missing character.*|.*destination with the same identifier.*|.*duplicate ignored.*', log, re.I)
            assert not problems, problems
            pdf = fresh / 'build' / (entry + '.pdf')
            extracted = fresh / (entry + '-extracted.txt')
            run(['pdftotext', '-layout', str(pdf), str(extracted)], fresh)
            info = run(['pdfinfo', str(pdf)], fresh).stdout
            fonts = run(['pdffonts', str(pdf)], fresh).stdout
            assert 'Type 3' not in fonts
            for row in fonts.splitlines()[2:]:
                assert re.search(r'\s+yes\s+(?:yes|no)\s+(?:yes|no)\s+', row), row
            pages = int(re.search(r'Pages:\s+(\d+)', info).group(1))
            wanted = expected['documents'][entry]
            assert pages == wanted['pages']
            assert digest(extracted) == wanted['text_sha256']
            same_bytes = digest(pdf) == wanted['sha256']
            # Record differences as differences; do not infer a metadata-only cause.
            if not same_bytes:
                (OUT / f'flat-{entry}-rebuilt.pdf').write_bytes(pdf.read_bytes())
            record['packages'][entry] = dict(filename=filename, files=len(mapping),
                sha256=digest(archive_path), flattened_paths=mapping, pages=pages,
                pdf_sha256=digest(pdf), reference_pdf_sha256=wanted['sha256'],
                pdf_bytes_equal=same_bytes, text_equal=True,
                overfull=0, undefined_references=0, duplicate_labels_or_targets=0,
                missing_glyphs=0, all_fonts_embedded=True, type3_fonts=0)
    (OUT / 'FLAT_SOURCE_REBUILD_QA.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
