"""Package existing PR147 bytes. No model/native process is started."""
import argparse
import gzip
import json
import pathlib
import zipfile
from delivery import read, sha, save, check, require

P = pathlib.Path
BASE = '3429e2c49626c30e4a406a517a3e8a030aea9c7f'
SLOTS = ['qual-0187', 'qual-0192', 'qual-0193']


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('raw', 'source', 'history', 'dependencies', 'work', 'out'):
        ap.add_argument('--' + name, type=P, required=True)
    a = ap.parse_args()
    repo = P(__file__).resolve().parents[3]
    baseline = repo / 'benchmarks/rtx_native_bridge_20261026/results'
    with gzip.open(baseline / 'RAW_FILES.json.gz', 'rt') as f:
        raw_manifest = json.load(f)['files']
    a.work.mkdir(parents=True, exist_ok=False)
    a.out.mkdir(parents=True, exist_ok=True)
    files = {}

    def add(name, path, origin, expected=None):
        require(name not in files, 'duplicate logical member')
        if expected is not None:
            check(path, expected)
        files[name] = (path, dict(bytes=path.stat().st_size, sha256=sha(path), origin=origin))

    def raw(name, source=None):
        rel = source or name
        add(name, a.raw / rel, 'PR147 RAW_FILES.json.gz:' + rel, raw_manifest[rel])

    for name in ('PANEL.json', 'MODEL_CONTRACT.json', 'STAGE_ORIGIN.json', 'STAGE_RESULT.json',
                 'HISTORICAL_R_ENDPOINTS.json', 'qualification-v2-QUALIFICATION.json', 'RECOVERY.json',
                 'CLEAN_BUILD.json', 'bridge-build-v2-BUILD.json', 'RECORDING_AMENDMENT.json'):
        raw(name)
    for directory in ('stage-fixture', 'request-smoke'):
        for p in sorted((a.raw / directory).rglob('*')):
            if p.is_file(): raw(p.relative_to(a.raw).as_posix())
    for arm in ('MQ', 'PQ', 'QB'):
        rel = 'stage-replays/clean-build-' + arm + '-r0'
        for p in sorted((a.raw / rel).iterdir()):
            if p.is_file(): raw('stage-expected/' + arm + '-r0/' + p.name, rel + '/' + p.name)
    for slot in SLOTS:
        raw('qualification-v2/' + slot + '.json')
        for p in sorted((a.raw / 'qualification-v2' / slot).rglob('*')):
            if p.is_file(): raw(p.relative_to(a.raw).as_posix())
    hist = read(a.raw / 'HISTORICAL_R_ENDPOINTS.json')
    require(sha(a.history) == hist['source_sha256'], 'historical E2 source')
    add('history/E2_s0_Qwen_b00.json', a.history, 'historical E2 s0_Qwen_b00, bound by HISTORICAL_R_ENDPOINTS')
    deps = read(a.dependencies)
    add('sources/SOURCE_RUNTIME.zip', a.source, '3235d44c26edd92db33e574094c26af8e29d2452 historical original capsule', deps['source_archive'])
    add('DEPENDENCIES.json', a.dependencies, 'delivery dependency acquisition manifest')
    selection = a.work / 'selection.json'
    save(selection, dict(result_baseline=BASE, slots=SLOTS, input_id='GSM8K/test/443',
                         criterion='Existing PR147 stage/smoke input; R and captured k3/fresh PQ/QB. No timing selection.',
                         preserved_request_bytes=True, native_processes_started=0,
                         historical_bulk_scope='Other inputs, interrupted v1, full builds remain at original RAW_ACCESS; not delivered by this subset.'))
    add('selection.json', selection, 'new packaging selection')
    for name in ('NATIVE_RECORDS.zip', 'INDEPENDENT_AUDIT.json', 'FINAL_VALIDATION.json', 'ANALYSIS.json', 'ACCOUNTING.json'):
        add('recorded-results/' + name, baseline / name, BASE + ':' + name)
    for p in sorted(P(__file__).parent.glob('*.py')):
        add('tools/' + p.name, p, 'new CPU delivery / portable native wrapper source')
    p = P(__file__).parent / 'worker.cpp'
    require(p.read_bytes() == (P(__file__).parents[1] / 'rtx_bridge/worker.cpp').read_bytes(), 'frozen worker changed')
    add('tools/worker.cpp', p, BASE + ':scripts/native_reproduction/rtx_bridge/worker.cpp (unchanged bytes)')
    # Keep the exact legacy helper for native wrapper imports.
    p = P(__file__).parents[1] / 'rtx_recover.py'
    add('tools/rtx_recover.py', p, BASE + ':scripts/native_reproduction/rtx_recover.py')
    doc = P(__file__).parent / 'README.md'
    add('README.md', doc, 'new portable delivery guide')
    manifest = {name: meta for name, (_, meta) in sorted(files.items())}
    save(a.out / 'MEMBERS.json', manifest)
    archive = a.work / 'RTX_NATIVE_DELIVERY.zip'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, (p, meta) in sorted(files.items()):
            check(p, meta)
            z.write(p, name)
        z.write(a.out / 'MEMBERS.json', 'MEMBERS.json')
    parts = []
    with archive.open('rb') as f:
        while data := f.read(40 * 1024 * 1024):
            p = a.out / f'RTX_NATIVE_DELIVERY.part{len(parts)+1:03d}'
            with p.open('xb') as dst: dst.write(data)
            parts.append(dict(path=p.name, bytes=p.stat().st_size, sha256=sha(p)))
    save(a.out / 'PARTS.json', dict(archive=dict(bytes=archive.stat().st_size, sha256=sha(archive)),
                                  parts=parts, members=len(manifest),
                                  expanded_bytes=sum(x['bytes'] for x in manifest.values()),
                                  result_baseline=BASE, native_processes_started=0))
    print(json.dumps(read(a.out / 'PARTS.json'), indent=2))


if __name__ == '__main__':
    main()
