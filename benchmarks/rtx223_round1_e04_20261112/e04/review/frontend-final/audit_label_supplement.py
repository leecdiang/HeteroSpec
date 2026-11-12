"""Exact raw-line comparison of producer member/map label receipts; CPU files only."""
from pathlib import Path
import datetime
import json
import re
from independent_common import need, sha, identity, read_json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = ROOT / 'e04/frontend/run-v4'
RECOVERY = ROOT / 'e04/frontend/recovery-v1'


def main():
    out = HERE / 'RAW_LABEL_SUPPLEMENT.json'
    need(not out.exists(), 'fresh raw-label supplement required')
    recipe = read_json(RUN / 'RECIPE.json')
    results = []
    for core in ('loop4', 'packed'):
        logs = RECOVERY if core == 'packed' else RUN
        archives = [str(Path(p).resolve()) for p in recipe['cores'][core]['archives']]
        by_name, aliases = {}, {}
        for p in archives:
            by_name.setdefault(Path(p).name.casefold(), set()).add(p)
            stem = Path(p).stem
            for label in (Path(p).name, stem, stem.removeprefix('lib')):
                aliases.setdefault(label.casefold(), set()).add(p)
        def resolve(value):
            if Path(value).is_absolute():
                p = str(Path(value).resolve())
                need(p in archives, 'raw member archive not frozen')
                return p
            options = by_name.get(value.casefold(), set())
            need(len(options) == 1, 'ambiguous raw member archive')
            return next(iter(options))
        witness_path = RECOVERY / (core + '-WHOLE_ARCHIVE_WITNESS.json')
        witness = read_json(witness_path)
        text = (logs / (core + '-link.stdout.log')).read_text(encoding='utf8') + (logs / (core + '-link.stderr.log')).read_text(encoding='utf8')
        member_rows = []
        for n, line in enumerate(text.splitlines(), 1):
            match = re.fullmatch(r'lld-link: (Reading|Loaded) (.*?\.(?:a|lib))\((.+?)\)(?: for (?:symbol )?(.+))?', line, re.I)
            if match:
                row = {'line': n, 'archive': resolve(match[2]), 'member_label': match[3], 'kind': match[1]}
                if match[1] == 'Loaded':
                    row['symbol_label'] = match[4]
                member_rows.append(row)
        need(member_rows == witness['member_labels'], 'producer member receipt differs from exact raw Reading/Loaded lines')
        map_rows = []
        map_path = Path(recipe['cores'][core]['object']).with_suffix('.map')
        for n, line in enumerate(map_path.read_text(encoding='utf8').splitlines(), 1):
            match = re.fullmatch(r'\s*[0-9A-Fa-f]{4}:[0-9A-Fa-f]+\s+(\S+)\s+[0-9A-Fa-f]+\s+(.+?)\s*', line)
            if not match:
                continue
            reference = match[2].split()[-1]
            if ':' not in reference:
                continue
            label, member = reference.split(':', 1)
            choices = aliases.get(label.casefold(), set())
            need(len(choices) == 1, 'map alias not uniquely frozen')
            map_rows.append({'line': n, 'archive': next(iter(choices)), 'member_label': member, 'symbol_label': match[1]})
        need(map_rows == witness['map_labels'], 'producer map label receipt differs from exact raw map lines')
        results.append({'core': core, 'member_label_rows_exact': len(member_rows), 'map_label_rows_exact': len(map_rows),
                        'producer_witness': identity(witness_path), 'raw_map': identity(map_path),
                        'raw_link_logs': [identity(logs / (core + '-link.' + stream + '.log')) for stream in ('stdout', 'stderr')]})
    result = {'schema': 'heterospec.e04.independent-exact-raw-label-supplement.v1',
              'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'PASS_EXACT_RAW_LINE_LABEL_BINDING',
              'frontend_review': identity(HERE / 'FINAL_FRONTEND_REVIEW.json'), 'cores': results,
              'scope': 'Strengthens exact raw-line binding only; selected duplicate-member offsets and COFF symbol resolution remain NOT_ATTESTED.',
              'producer_verifier_imported': False, 'GPU_calls': 0, 'numeric_DLL_loads': 0, 'models': 0}
    out.write_text(json.dumps(result, indent=2), encoding='utf8')
    print(json.dumps({'status': result['status'], 'sha256': sha(out), 'cores': [{k:v for k,v in row.items() if k in ('core','member_label_rows_exact','map_label_rows_exact')} for row in results]}, indent=2))


if __name__ == '__main__':
    main()
