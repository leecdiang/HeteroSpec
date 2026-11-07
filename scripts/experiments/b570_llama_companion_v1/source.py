"""Prepare separate stock-oracle and experimental Vulkan sources, without altering history."""
from __future__ import annotations
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
from common import BASE, UPSTREAM, blob, git_bytes, need, read, sha, write

PREFIX = 'benchmarks/b570_native_reproduction_v1/'
PINS = {'native/ggml-vulkan.cpp': 'ebc9821bf50d76fa376b400a015aaf873a42d7f3',
        'native/llama-graph.cpp': 'ee8c9d321603760607a7d526c836c2c0b1a23cf7',
        'native/query_head.h': '26eaf778a64946cbac916e6c71df00b193e831c9',
        'run_native.py': 'dd0e0439631d84bd59effa180a135d67c39cd5bc'}


def once(text, old, new):
    need(text.count(old) == 1, 'nonunique/missing source anchor: ' + old[:100])
    return text.replace(old, new, 1)


def graph_port(text):
    begin = '    // Private request bridge: immutable layout per fresh context, single-threaded host.'
    end = '    const bool use_flash_attn = cparams.flash_attn && kq_b == nullptr;'
    need(text.count(begin) == text.count(end) == 1, 'graph bridge source drift')
    start, stop = text.index(begin), text.index(end)
    old = text[start:stop]
    new = '''    // Companion port. This expanded domain requires new native qualification.
    // Layout is immutable per Context; setter is active only during target decode.
    if (hs_b570::mode != 0 && q->ne[1] > 1) {
        GGML_ASSERT(q->ne[0] == 128 && q->ne[2] == 32 && k->ne[2] == 8);
        GGML_ASSERT(q->ne[1] >= 2 && q->ne[1] <= 4);
        GGML_ASSERT(k->ne[1] >= 256 && k->ne[1] <= 1024 && k->ne[1] % 256 == 0);
        GGML_ASSERT(q->ne[3] == 1 && k->ne[3] == 1 && v->ne[3] == 1);
        GGML_ASSERT(!cparams.flash_attn && !kq_b && !sinks && !v_mla && v_trans);
        GGML_ASSERT(!hparams.attn_soft_cap && hparams.f_max_alibi_bias == 0 && cparams.offload_kqv);
        const bool qb = hs_b570::mode == 2;
        auto b = hs_qh::build(ctx0, qb ? hs_qh::Mode::QB4 : hs_qh::Mode::PQ, q, k, v, kq_mask, kq_scale);
        GGML_ASSERT(!b.common_original && !b.copied_kv);
        for (auto * t : b.scores) cb(t, qb ? "hs_qb_qk" : "hs_pq_qk", il);
        for (auto * t : b.probs) cb(t, qb ? "hs_qb_prob" : "hs_pq_prob", il);
        for (auto * t : b.values) cb(t, qb ? "hs_qb_av" : "hs_pq_av", il);
        cb(b.out, qb ? "hs_qb_final" : "hs_pq_final", il);
        ggml_build_forward_expand(gf, b.out);
        return b.out;
    }

'''
    text = text[:start] + new + text[stop:]
    return once(text, '#include "query_head.h"', '#include "query_head.h"\n#include "companion_scope.hpp"')


def vulkan_port(text):
    # Preserve the qualified shader body and broadcast stride mechanism. Only the
    # named experimental admission domains are enlarged; no generic search/replace.
    first = text.index('// Exact E2 AV domain only.')
    end = text.index('static void ggml_vk_mul_mat_vec_nc_f16_f32', first)
    region = text[first:end]
    region = once(region, '(a->ne[0] == 256 || a->ne[0] == 512)', '(a->ne[0] >= 256 && a->ne[0] <= 1024 && a->ne[0] % 256 == 0)')
    region = once(region, '(b->ne[3] == 2 || b->ne[3] == 4)', '(b->ne[3] >= 2 && b->ne[3] <= 4)')
    text = text[:first] + region + text[end:]
    first = text.index('const bool qb_batch_broadcast =')
    end = text.index('if (!(ggml_vk_dim01_contiguous', first)
    region = text[first:end]
    for old, new, count in [
        ('(b->ne[3] == 2 || b->ne[3] == 4)', '(b->ne[3] >= 2 && b->ne[3] <= 4)', 2),
        ('(a->ne[1] == 256 || a->ne[1] == 512)', '(a->ne[1] >= 256 && a->ne[1] <= 1024 && a->ne[1] % 256 == 0)', 1),
        ('(a->ne[0] == 256 || a->ne[0] == 512)', '(a->ne[0] >= 256 && a->ne[0] <= 1024 && a->ne[0] % 256 == 0)', 1)]:
        need(region.count(old) == count, 'Vulkan admission source drift')
        region = region.replace(old, new)
    return text[:first] + region + text[end:]


def stage(repo, archive, out, mode):
    out = Path(out)
    need(mode in ('oracle', 'candidate') and not out.exists(), 'fresh source stage/mode')
    inventory = json.loads(git_bytes(repo, BASE, PREFIX + 'SOURCE_INPUTS.json'))
    need(sha(archive) == inventory['upstream_archive_sha256'], 'upstream archive identity')
    out.mkdir(parents=True)
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            destination = (out / member.name).resolve()
            need(destination.is_relative_to(out.resolve()), 'unsafe archive member')
            need(member.isdir() or member.isfile(), 'archive links are not accepted')
        tar.extractall(out, filter='data')
    src = out / ('llama.cpp-' + UPSTREAM)
    for item in inventory['upstream']:
        p = src / item['path']
        need(p.is_file() and p.stat().st_size == item['bytes'] and sha(p) == item['sha256'], 'upstream source mismatch: ' + item['path'])
    changes = []
    if mode == 'candidate':
        for old, dest, transform in [
            ('native/ggml-vulkan.cpp', 'ggml/src/ggml-vulkan/ggml-vulkan.cpp', vulkan_port),
            ('native/llama-graph.cpp', 'src/llama-graph.cpp', graph_port),
            ('native/query_head.h', 'src/query_head.h', lambda x: x)]:
            data = git_bytes(repo, BASE, PREFIX + old, PINS[old])
            text = data.decode('utf-8'); changed = transform(text)
            target = src / dest; before = target.read_bytes() if target.exists() else b''
            target.write_text(changed, encoding='utf-8', newline='\n')
            diff = ''.join(difflib.unified_diff(text.splitlines(True), changed.splitlines(True), fromfile=old, tofile=dest))
            (out / (Path(dest).name + '.patch')).write_text(diff, encoding='utf-8')
            changes.append({'path': dest, 'upstream_sha256': hashlib.sha256(before).hexdigest(),
                            'parent_blob': PINS[old], 'after_sha256': sha(target)})
    for n in ('companion_scope.hpp',):
        shutil.copyfile(Path(__file__).parent / n, src / 'src' / n)
    write(out / 'SOURCE.json', {'mode': mode, 'upstream': UPSTREAM, 'archive_sha256': sha(archive),
          'upstream_files_checked': len(inventory['upstream']), 'changes': changes,
          'new_domain': 'q2/3/4; keys256/512/768/1024; d128; 32/8 heads; F16 KV/F32 Q',
          'native_qualified': False, 'root': str(src.resolve())})
    return src


def supervisor(repo, out):
    data = git_bytes(repo, BASE, PREFIX + 'run_native.py', PINS['run_native.py']).decode()
    data = once(data, "check(0<a.limit<=240,'Native time bound')", "check(a.limit>0,'Finite positive native time bound')")
    data = once(data, "if key.startswith('HS_') or key.startswith('GGML_VK_PERF_LOGGER'):del env[key]", "if key.startswith(('HS_', 'HSC_', 'JSA_', 'GGML_')):del env[key]")
    data = once(data, "p.add_argument('--limit',type=int,default=240);", "p.add_argument('--limit',type=int,default=240);p.add_argument('--minimum-free-bytes',type=int,default=10*1024**3);")
    data = once(data, "check(shutil.disk_usage(a.receipt.parent).free>10*1024**3,'Less than 10 GiB free')", "check(a.minimum_free_bytes>0 and shutil.disk_usage(a.receipt.parent).free>a.minimum_free_bytes,'Disk reserve')")
    data = once(data, "seen.update(modules(handle));check(time.monotonic()-start<a.limit,'Native timeout');time.sleep(.1)", "seen.update(modules(handle));check(time.monotonic()-start<a.limit,'Native timeout');check(shutil.disk_usage(a.receipt.parent).free>a.minimum_free_bytes,'Runtime disk reserve');time.sleep(.1)")
    p = Path(out)
    need(not p.exists(), 'fresh supervisor path')
    p.write_text(data, encoding='utf-8', newline='\n')
    return p


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', required=True);ap.add_argument('--archive', required=True);ap.add_argument('--out', required=True)
    ap.add_argument('--mode', choices=['oracle', 'candidate'], required=True)
    args = ap.parse_args(); print(stage(args.repo, args.archive, args.out, args.mode))
