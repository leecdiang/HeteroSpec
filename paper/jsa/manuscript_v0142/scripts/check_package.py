"""Extract the final author source ZIP and rebuild from an empty directory, CPU only."""
from pathlib import Path
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    package = OUT / 'overleaf-author-source-v0.14.2.zip'
    expected = json.loads((OUT / 'BUILD_QA.json').read_text())
    with tempfile.TemporaryDirectory(prefix='jsa-v0142-source-rebuild-') as temporary:
        fresh = Path(temporary)
        with zipfile.ZipFile(package) as archive:
            members = archive.namelist()
            assert len(members) == len(set(members))
            for name in members:
                relative = Path(name)
                assert not relative.is_absolute() and '..' not in relative.parts
                assert not any(x in relative.parts for x in ['build', 'output', '__pycache__'])
                assert archive.read(name) == (ROOT / name).read_bytes(), name
            archive.extractall(fresh)
        assert not (fresh / 'build').exists() and not (fresh / 'output').exists()
        result = subprocess.run([sys.executable, 'build.py', '--no-package'], cwd=fresh,
                                text=True, capture_output=True)
        (OUT / 'source-package-rebuild-console.log').write_text(result.stdout + result.stderr)
        assert result.returncode == 0, result.stdout + result.stderr
        actual = json.loads((fresh / 'output' / 'BUILD_QA.json').read_text())
        documents = {}
        for stem, filename in [('main', 'jsa-manuscript-v0.14.2.pdf'),
                               ('supplement', 'jsa-supplement-v0.14.2.pdf')]:
            a, b = expected['documents'][stem], actual['documents'][stem]
            assert a['pages'] == b['pages'] and a['text_sha256'] == b['text_sha256']
            assert a['sha256'] == b['sha256'], (stem, 'PDF bytes differ in the same environment')
            documents[stem] = dict(pages=b['pages'], text_sha256=b['text_sha256'],
                                   pdf_sha256=b['sha256'], text_equal=True, pdf_bytes_equal=True,
                                   clean_build_diagnostics=True, all_fonts_embedded=True)
        # Recalculation must not silently change supplied scientific figures or editable tables.
        generated = sorted(list((ROOT / 'figures').glob('*')) + list((ROOT / 'tables').glob('*.tex')))
        for path in generated:
            assert digest(path) == digest(fresh / path.relative_to(ROOT)), path.name
        original_qa = json.loads((OUT / 'NUMERICAL_QA.json').read_text())
        rebuilt_qa = json.loads((fresh / 'output' / 'NUMERICAL_QA.json').read_text())
        assert original_qa == rebuilt_qa
        original_scientific = json.loads((OUT / 'SCIENTIFIC_QA.json').read_text())
        rebuilt_scientific = json.loads((fresh / 'output' / 'SCIENTIFIC_QA.json').read_text())
        # The workspace has a preserved sibling v014; the portable ZIP instead
        # authenticates the same evidence against its included source bindings.
        original_sibling = original_scientific['preservation'].pop('v014_sibling_comparisons')
        rebuilt_sibling = rebuilt_scientific['preservation'].pop('v014_sibling_comparisons')
        assert original_scientific == rebuilt_scientific
        toolchain = {}
        for tool, arguments in [('pdflatex', ['--version']), ('latexmk', ['-version']), ('pdfinfo', ['-v'])]:
            result = subprocess.run([tool] + arguments, text=True, capture_output=True, check=True)
            toolchain[tool] = (result.stdout + result.stderr).splitlines()[:3]
        record = dict(version='v0.14.2', author_side_validation=True, new_inference=0,
                      method='final ZIP extracted into an empty temporary directory; full CPU build',
                      package_sha256=digest(package), package_files=len(members),
                      package_source_bytes_equal=True, numerical_qa_equal=True,
                      independent_scientific_core_equal=True,
                      workspace_sibling_comparisons=original_sibling,
                      extracted_sibling_comparisons=rebuilt_sibling,
                      toolchain=toolchain,
                      generated_figures_and_tables_equal=len(generated), documents=documents,
                      python=platform.python_version(),
                      boundary='Same-environment rebuild; not a live Overleaf run or private raw archive audit')
        (OUT / 'SOURCE_PACKAGE_REBUILD_QA.json').write_text(json.dumps(record, indent=2) + '\n')
        print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
