"""CPU-only native tokenization, conservative accessible-history census and selection.

No model context or forward is created by the separately pinned vocabulary tool.
Exposure includes ambiguous task/text mentions. Exhaustive availability ledgers,
corpora and vocabulary-only inventories are explicitly classified separately.
"""
import argparse
import collections
import gzip
import json
import os
from pathlib import Path
import re
import subprocess
import unicodedata
import zipfile
import sys
from work_package import read, sha_file, digest, write_new

WRAPPER = '<|im_start|>user\n{raw}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
PREFIX = 'Complete the following Python programming task. Return only the completed Python code, without Markdown fences.\n\n'
MATH_PREFIX = 'Solve the following math problem. Give a concise solution and the final answer.\n\n'

def normalized(s):
    return ' '.join(unicodedata.normalize('NFKC', s).split())

def main():
    ap = argparse.ArgumentParser()
    for name in ('humaneval', 'mbpp', 'tokenizer', 'model', 'out'):
        ap.add_argument('--' + name, type=Path, required=True)
    ap.add_argument('--history', type=Path, action='append', required=True)
    ap.add_argument('--gsm8k', type=Path)
    ap.add_argument('--math500', type=Path)
    ap.add_argument('--cpu-packages', type=Path)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    if a.cpu_packages:sys.path.insert(0,str(a.cpu_packages))
    import ahocorasick
    rows = []
    corpus_hashes={sha_file(a.humaneval),sha_file(a.mbpp)}
    with gzip.open(a.humaneval, 'rt', encoding='utf8') as f:
        he = [json.loads(line) for line in f]
    mb = read(a.mbpp)
    for family, data, corpus in (('HumanEval', he, a.humaneval), ('MBPP', mb, a.mbpp)):
        for r in data:
            task = r['task_id'] if family == 'HumanEval' else 'MBPP/' + str(r['task_id'])
            raw = PREFIX + r['prompt']
            rows.append(dict(id=task, text=r['prompt'], raw_prompt=raw, prefix=PREFIX,
                             formatted_prompt=WRAPPER.format(raw=raw), domain='code',
                             source={'revision': 'sha256:' + sha_file(corpus), 'task_id': task}))
    if a.gsm8k:
        for split in ['train','test']:
            corpus=a.gsm8k/(split+'.jsonl');h=sha_file(corpus);corpus_hashes.add(h)
            for i,line in enumerate(corpus.read_text('utf8').splitlines()):
                question=json.loads(line)['question'];task=f'GSM8K/{split}/{i}';raw=MATH_PREFIX+question
                rows.append(dict(id=task,text=question,raw_prompt=raw,prefix=MATH_PREFIX,
                    formatted_prompt=WRAPPER.format(raw=raw),domain='math',
                    source={'revision':'3101c7d5072418e28b9008a6636bde82a006892c','task_id':task,'file_sha256':h,'split':split}))
    if a.math500:
        corpus=a.math500/'test.jsonl';h=sha_file(corpus);corpus_hashes.add(h)
        for line in corpus.read_text('utf8').splitlines():
            r=json.loads(line);question=r['problem'];task='MATH500/'+r['unique_id'];raw=MATH_PREFIX+question
            rows.append(dict(id=task,text=question,raw_prompt=raw,prefix=MATH_PREFIX,
                formatted_prompt=WRAPPER.format(raw=raw),domain='math',
                source={'revision':'6e4ed1a2a79af7d8630a6b768ec859cb5af4d3be','task_id':task,'file_sha256':h,'unique_id':r['unique_id']}))
    input_bytes = ''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in rows).encode('utf8')
    (a.out/'TOKENIZER_INPUT.jsonl').write_bytes(input_bytes)
    with (a.out/'TOKENIZER_STDOUT.jsonl').open('xb') as out, (a.out/'TOKENIZER_STDERR.log').open('xb') as err:
        subprocess.run([str(a.tokenizer), str(a.model)], input=input_bytes, stdout=out, stderr=err, check=True, timeout=120)
    native = [json.loads(line) for line in (a.out/'TOKENIZER_STDOUT.jsonl').read_text('utf8').splitlines()]
    assert len(native) == len(rows)+1 and all(r['forward_calls'] == 0 for r in native)
    tokens = {r['id']: r['prompt_ids'] for r in native[1:]}
    write_new(a.out/'TOKENIZATION.json', dict(vocabulary=native[0], tokenizer_sha256=sha_file(a.tokenizer),
        stdout_sha256=sha_file(a.out/'TOKENIZER_STDOUT.jsonl'), input_sha256=sha_file(a.out/'TOKENIZER_INPUT.jsonl'),
        model_sha256=sha_file(a.model), mode='vocab_only; no contexts or forwards'))
    # Do not count exhaustive availability inventories as exposure; retain each classification and hash.
    availability_names = {'prompt_tokens.json', 'input_candidates.json', 'tokenization.stdout.jsonl',
        'tokenizer_stdout.jsonl', 'tokenizer_input.jsonl', 'tokenization.json', 'exposure_inventory.json',
        'exposure_audit.json', 'exposure_catalog.json', 'exposure_summary.json', 'exposure_recheck.json',
        'e_exposure_audit.json', 'e_exposure_catalog.json', 'candidate_inventory.json',
        'humaneval.jsonl', 'sanitized-mbpp.json'}
    skip = {'.git', '__pycache__', 'models', 'vendor', 'third_party', 'node_modules', 'datasets',
        'build', 'candidate-build', 'tokenizer-bin', 'candidate-src', 'candidate-common', 'upstream',
        'clean-source', 'clean-source2', 'b570-direct-id-v1-src', 'b570-direct-id-v1-build', 'llama-b10839',
        'b570-prefill-build', 'b570-partition-intervention-v1-build', 'b570-mechanism-v08-build'}
    suffixes = {'.json', '.jsonl', '.md', '.txt', '.csv', '.log', '.yaml', '.yml', '.tex', '.py', '.cpp', '.h'}
    id_re = re.compile(r'\b(HumanEval|MBPP)[/_-](\d{1,4})\b', re.I)
    math_id_re=re.compile(r'\bGSM8K/(?:train|test)/\d+\b')
    competition_id_re=re.compile(r'MATH500/test/[a-z_]+/\d+\.json')
    text_map = collections.defaultdict(set)
    for row in rows:
        for text in [row['text'],json.dumps(row['text'],ensure_ascii=True)[1:-1].replace('\\n','\n').replace('\\t','\t').replace('\\"','"')]:
            text_map[normalized(text)].add(row['id'])
    matcher=ahocorasick.Automaton()
    for text,ids in text_map.items():matcher.add_word(text,tuple(ids))
    matcher.make_automaton()
    hits = collections.defaultdict(set)
    catalog, errors, unique, fragments = [], [], {}, []
    out_abs = a.out.resolve()
    def inspect(label, b, basename):
        import hashlib
        h = hashlib.sha256(b).hexdigest()
        if h in unique:
            return
        unique[h] = label
        availability = h in corpus_hashes or basename.lower() in availability_names or ('exposure' in basename.lower() and basename.lower().endswith('.json'))
        catalog.append(dict(path=label, bytes=len(b), sha256=h, classification='availability' if availability else 'history'))
        if availability:
            return
        s = b.decode('utf8', errors='replace')
        found = {('HumanEval' if m[1].lower()=='humaneval' else 'MBPP')+'/'+m[2] for m in id_re.finditer(s)}
        found.update(math_id_re.findall(s))
        found.update(competition_id_re.findall(s))
        # Match normalized literal and JSON-escaped prompt text, without inspecting numerical outcomes.
        s = s.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
        for end,ids in matcher.iter(normalized(s)):found.update(ids)
        for task in found:
            hits[task].add(label)
    for root in a.history:
        assert root.exists(), root
        for directory, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in skip and not d.startswith('.venv') and (Path(directory)/d).resolve()!=out_abs]
            for name in files:
                p = Path(directory)/name
                if p.suffix.lower() not in suffixes | {'.zip'}:
                    continue
                try:
                    if p.suffix.lower()=='.zip' and not zipfile.is_zipfile(p):
                        candidates=[p.parent/'FAILED.json',p.parent/'FAILURE.json']
                        proof=next((q for q in candidates if q.exists() and read(q).get('status')=='TRANSPORT_FAILED'
                            and read(q).get('received_bytes',read(q).get('partial_bytes'))==p.stat().st_size),None)
                        if proof is None:raise zipfile.BadZipFile('Unreadable archive without matching transport receipt')
                        fragments.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha_file(p),receipt=str(proof),receipt_sha256=sha_file(proof)))
                    elif p.suffix.lower()=='.zip':
                        with zipfile.ZipFile(p) as z:
                            for member in z.infolist():
                                if Path(member.filename).suffix.lower() in suffixes and member.file_size <= 128*1024**2:
                                    inspect(str(p)+'!'+member.filename, z.read(member), Path(member.filename).name)
                    elif p.stat().st_size <= 128*1024**2:
                        inspect(str(p), p.read_bytes(), name)
                except (OSError, zipfile.BadZipFile, RuntimeError) as e:
                    errors.append(dict(path=str(p), error=str(e)))
        print('scanned', root, 'unique files', len(catalog), 'excluded identities', len(hits), flush=True)
    inventory = []
    token_counts=collections.Counter(digest(tokens[r['id']]) for r in rows)
    for row in rows:
        ids = tokens[row['id']]
        band = 'short' if 64<=len(ids)<=192 else 'long' if 256<=len(ids)<=352 else None
        reasons = ([] if band else ['outside length bands']) + (['historical or ambiguous exposure'] if row['id'] in hits else [])
        if token_counts[digest(ids)]>1:reasons.append('duplicate token sequence in candidate pool')
        inventory.append(dict(**row, prompt_ids=ids, stratum=band, cap=128,
            normalized_text_sha256=digest(normalized(row['text'])),
            template_sha256=digest({'wrapper':WRAPPER,'prefix':row['prefix']}),
            selection_hash=digest({'study':'b570_producer_consumer_boundary_v1','id':row['id'],'source':row['source']}),
            exclusions=reasons, evidence=sorted(hits.get(row['id'], []))))
    write_new(a.out/'EXPOSURE_CATALOG.json', catalog)
    write_new(a.out/'CANDIDATE_INVENTORY.json', inventory)
    audit = dict(status='PASS' if not errors else 'FAIL', roots=[str(p) for p in a.history], errors=errors,
        unique_files=len(catalog), catalog_sha256=sha_file(a.out/'EXPOSURE_CATALOG.json'),
        classified_failed_transport_fragments=fragments,
        policy='Any task ID or normalized prompt mention excludes; exhaustive corpora/tokenization/exposure ledgers are availability only.',
        limitations=['Accessible retained history only; not a claim about deleted/private other-machine records or model training.'],
        eligible_counts={band:sum(not r['exclusions'] and r['stratum']==band for r in inventory) for band in ['short','long']},
        new_forward_calls=0)
    write_new(a.out/'EXPOSURE_AUDIT.json', audit)
    assert not errors, errors[:5]
    chosen=[]
    for band in ['short','long']:
        eligible=sorted((r for r in inventory if not r['exclusions'] and r['stratum']==band),key=lambda r:(r['selection_hash'],r['id']))
        if len(eligible)<4:
            write_new(a.out/'STOP.json',dict(status='INSUFFICIENT_STATIC_PANEL',band=band,eligible=len(eligible),new_forward_calls=0))
            print('STOP: insufficient', band, len(eligible));return
        for r in eligible[:4]:
            chosen.append(dict(r, exposure_status='UNSEEN_FOR_CURRENT_IMPLEMENTATION'))
    write_new(a.out/'INPUT_PANEL.json',dict(schema=1,status='FROZEN_BEFORE_FORWARD',new_model_outputs_used_for_selection=False,
        candidate_inventory_sha256=sha_file(a.out/'CANDIDATE_INVENTORY.json'),exposure_audit_sha256=sha_file(a.out/'EXPOSURE_AUDIT.json'),
        selection_rule='Exclude accessible historical IDs/normalized prompt text, then first4 per native length band by canonical SHA256(study,id,source).',inputs=chosen))
    print('selected',[(r['id'],len(r['prompt_ids'])) for r in chosen])

if __name__=='__main__':main()
