"""Independent raw checks. Does not import any producer verification module."""
from pathlib import Path
import ctypes
from ctypes import wintypes
import hashlib
import json
import re
import struct


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def identity(path):
    p = Path(path)
    return {'path': str(p.resolve()), 'bytes': p.stat().st_size, 'sha256': sha(p)}


def read_json(path):
    return json.loads(Path(path).read_bytes())


def make_dependencies(path):
    """Deliberately narrow independent grammar for these space-free absolute paths."""
    raw = Path(path).read_text(encoding='utf8')
    need(raw.endswith('\n') and '\0' not in raw, 'incomplete Make dependency file')
    joined = re.sub(r'\\\n', '', raw)
    need(len(joined.splitlines()) == 1, 'not one logical dependency rule')
    m = re.fullmatch(r'(.+?):\s+(.+)\n', joined)
    need(m is not None, 'missing dependency delimiter')
    target = m[1]
    deps = m[2].split()
    need(len(deps) > 1, 'empty/header-free dependency witness')
    need(all(Path(x).is_absolute() and not any(c in x for c in '*?$#|;') for x in [target] + deps), 'unsupported path syntax')
    paths = [str(Path(x).resolve()) for x in deps]
    need(len({x.casefold() for x in paths}) == len(paths), 'duplicate dependency')
    return str(Path(target).resolve()), sorted(paths)


def windows_words(line):
    # Windows system parsing only; no numeric DLL or CUDA import is performed.
    shell = ctypes.WinDLL('shell32', use_last_error=True)
    shell.CommandLineToArgvW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    shell.CommandLineToArgvW.restype = ctypes.POINTER(wintypes.LPWSTR)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.LocalFree.argtypes = [wintypes.HLOCAL]
    kernel.LocalFree.restype = wintypes.HLOCAL
    count = ctypes.c_int()
    ptr = shell.CommandLineToArgvW(line.strip(), ctypes.byref(count))
    need(bool(ptr), 'CommandLineToArgvW failed')
    try:
        return [ptr[i] for i in range(count.value)]
    finally:
        kernel.LocalFree(ptr)


def effective_cpu(path):
    invocations = []
    diagnostics = 0
    for line in Path(path).read_text(encoding='utf8').splitlines():
        if '-cc1' not in line:
            continue
        words = windows_words(line)
        if words[:3] == ['clang', '-cc1', 'version']:
            diagnostics += 1
            continue
        need(len(words) > 2 and words[1] == '-cc1', 'unrecognized cc1 line')
        invocations.append(words)
    need(len(invocations) == 1, 'not one actual cc1 invocation')
    words = invocations[0]
    cpus, features = [], []
    for i, word in enumerate(words):
        if word == '-target-cpu':
            need(i + 1 < len(words), 'CPU value absent')
            cpus.append(words[i + 1])
        elif word == '-target-feature':
            need(i + 1 < len(words), 'feature value absent')
            features.append(words[i + 1])
    need(len(cpus) == 1 and re.fullmatch('[A-Za-z0-9_.-]+', cpus[0]) and features, 'CPU/features absent')
    need(all(re.fullmatch('[+-][A-Za-z0-9_.-]+', x) for x in features), 'bad feature syntax')
    return [['cpu', cpus[0]]] + [['feature', f] for f in features], diagnostics


def archive_members(path):
    data = Path(path).read_bytes()
    need(data[:8] == b'!<arch>\n', 'not a regular archive: ' + str(path))
    offset, records, strings = 8, [], None
    while offset < len(data):
        need(offset + 60 <= len(data), 'short ar member header')
        header = data[offset:offset + 60]
        need(header[58:] == b'`\n', 'invalid ar member trailer')
        size_field = header[48:58].strip()
        need(size_field.isdigit(), 'invalid ar member size')
        size = int(size_field)
        start, end = offset + 60, offset + 60 + size
        need(end <= len(data), 'member exceeds archive bytes')
        name = header[:16].decode('ascii').rstrip()
        payload = data[start:end]
        if name == '//':
            strings = payload
        records.append([offset, start, size, name, payload])
        offset = end + (size % 2)
    need(offset == len(data), 'archive trailing bytes/alignment differs')
    result = []
    for off, start, size, name, payload in records:
        if name in ('/', '//', '/SYM64/'):
            continue
        if re.fullmatch('/[0-9]+', name):
            need(strings is not None, 'long member has no string table')
            loc = int(name[1:])
            need(loc < len(strings), 'long member offset outside string table')
            end = loc
            while end < len(strings) and strings[end] not in (0, 10):
                end += 1
            name = strings[loc:end].decode('utf8').removesuffix('/')
        elif name.startswith('#1/'):
            count = int(name[3:])
            need(count <= size, 'BSD inline name exceeds payload')
            name = payload[:count].decode('utf8').rstrip('\0')
            start += count
            size -= count
            payload = payload[count:]
        else:
            name = name.removesuffix('/')
        result.append({'header_offset': off, 'data_offset': start, 'bytes': size, 'member_name': name,
                       'payload_sha256': hashlib.sha256(payload).hexdigest()})
    return result


def check_command_logs(run, label):
    info = read_json(run / (label + '.json'))
    need(info['returncode'] == 0, 'command failed: ' + label)
    for stream in ('stdout', 'stderr'):
        need(sha(run / (label + '.' + stream + '.log')) == info[stream + '_sha256'], 'raw command log hash differs')
    return identity(run / (label + '.json'))


def audit_core(run, recipe, core, frozen, log_folder=None):
    info = recipe['cores'][core]
    logs = Path(log_folder) if log_folder is not None else run
    obj = Path(info['object'])
    exe = Path(info['exe'])
    codegen_record = check_command_logs(logs, core + '-compile')
    link_record = check_command_logs(logs, core + '-link')
    prescan_target, prescan = make_dependencies(run / (core + '-prescan.d'))
    actual_target, actual = make_dependencies(obj.with_suffix('.d'))
    need(prescan_target == actual_target == str(obj.resolve()), 'wrong dependency target')
    need(actual == prescan == info['prescan_dependencies'], 'actual codegen dependency set differs from frozen prescan')
    need(all(x in frozen for x in actual), 'actual codegen read header outside frozen closure')
    effective, prep_diag = effective_cpu(run / (core + '-effective.stderr.log'))
    actual_cpu, compile_diag = effective_cpu(logs / (core + '-compile.stderr.log'))
    need(effective == actual_cpu == info['effective_CPU'], 'resolved CPU/features differ')
    need(read_json(logs / (core + '-compile.json'))['argv'] == info['compile'], 'actual compile argv differs from recipe')
    need(read_json(logs / (core + '-link.json'))['argv'] == info['link'], 'actual link argv differs from recipe')
    archives = {str(Path(x).resolve()): archive_members(x) for x in info['archives']}
    need(all(x in frozen for x in archives), 'archive not frozen')
    archive_by_name = {}
    for p in archives:
        archive_by_name.setdefault(Path(p).name.casefold(), []).append(p)
    def resolve_archive(value):
        if Path(value).is_absolute():
            value = str(Path(value).resolve())
            need(value in archives, 'trace archive outside frozen closure: ' + value)
            return value
        choices = archive_by_name.get(Path(value).name.casefold(), [])
        need(len(choices) == 1, 'trace archive basename not uniquely frozen')
        return choices[0]
    lines = (logs / (core + '-link.stdout.log')).read_text(encoding='utf8').splitlines() + (logs / (core + '-link.stderr.log')).read_text(encoding='utf8').splitlines()
    groups, loaded, direct_reads = {}, 0, []
    for lineno, line in enumerate(lines, 1):
        m = re.fullmatch(r'lld-link: (Reading|Loaded) (.*?\.(?:a|lib))\((.+?)\)(?: for (.*))?', line, flags=re.I)
        if m:
            archive = resolve_archive(m[2])
            member = m[3].replace('\\', '/')
            candidates = [x for x in archives[archive] if x['member_name'].replace('\\', '/') == member or Path(x['member_name']).name == Path(member).name]
            need(candidates, 'trace member absent from frozen container: ' + member)
            key = (archive, member)
            group = groups.setdefault(key, {'archive': archive, 'member_name': member, 'candidate_offsets': [x['header_offset'] for x in candidates], 'candidate_payloads': sorted({x['payload_sha256'] for x in candidates}), 'reading_lines': [], 'loaded_lines': []})
            group['reading_lines' if m[1].lower() == 'reading' else 'loaded_lines'].append(lineno)
            loaded += m[1].lower() == 'loaded'
        elif line.startswith('lld-link: Reading '):
            p = str(Path(line[len('lld-link: Reading '):]).resolve())
            need(p in frozen or p == str(obj.resolve()), 'direct linker read outside frozen/generated closure: ' + p)
            direct_reads.append(p)
    map_path = obj.with_suffix('.map')
    read_archives = {p for p in direct_reads if Path(p).suffix.casefold() in ('.a', '.lib')}
    read_objects = {p for p in direct_reads if Path(p).suffix.casefold() == '.obj'}
    argv_objects = {str(Path(p).resolve()) for p in info['link'] if Path(p).is_absolute() and Path(p).suffix.casefold() == '.obj'}
    need(read_archives == set(archives), 'actual top-level Reading archives differ from explicit frozen containers')
    need(read_objects == argv_objects and len(read_objects | read_archives) == len(set(direct_reads)), 'direct linker reads differ from actual recipe object set')
    need(map_path.is_file() and map_path.stat().st_size > 0, 'map witness absent')
    need(groups and loaded, 'no member extraction trace')
    aliases = {}
    for archive in archives:
        name = Path(archive).name
        stem = Path(archive).stem
        for alias in (name, stem, stem.removeprefix('lib')):
            aliases.setdefault(alias.casefold(), set()).add(archive)
    map_labels = []
    for lineno, line in enumerate(map_path.read_text(encoding='utf8').splitlines(), 1):
        symbol = re.fullmatch(r'\s*[0-9A-Fa-f]{4}:[0-9A-Fa-f]+\s+(\S+)\s+[0-9A-Fa-f]+\s+(.+?)\s*', line)
        if not symbol:
            continue
        reference = symbol[2].split()[-1]
        if ':' not in reference:
            continue
        label, member = reference.split(':', 1)
        choices = aliases.get(label.casefold(), set())
        need(len(choices) == 1, 'map archive label not uniquely frozen: ' + label)
        archive = next(iter(choices))
        member = member.replace('\\', '/')
        candidates = [x for x in archives[archive] if x['member_name'].replace('\\', '/') == member or Path(x['member_name']).name == Path(member).name]
        need(candidates, 'map member absent from frozen archive')
        traced = [v for (p, n), v in groups.items() if p == archive and (n == member or Path(n).name == Path(member).name)]
        need(traced, 'map member has no raw Reading/Loaded trace')
        map_labels.append({'line': lineno, 'archive': archive, 'member_name': member, 'symbol_label': symbol[1]})
    need(map_labels, 'no independently resolved map archive/member references')
    ambiguous = [v for v in groups.values() if len(v['candidate_payloads']) > 1]
    return {'core': core, 'object': identity(obj), 'exe': identity(exe), 'compile_record': codegen_record, 'link_record': link_record,
            'dependency_count': len(actual), 'prescan_d': identity(run / (core + '-prescan.d')), 'actual_d': identity(obj.with_suffix('.d')),
            'resolved_CPU': actual_cpu, 'ignored_exact_version_diagnostic_lines': {'effective': prep_diag, 'compile': compile_diag},
            'archive_count': len(archives), 'archive_member_count': sum(len(v) for v in archives.values()),
            'archives': [dict(identity(p), nonmetadata_members=len(v)) for p, v in archives.items()],
            'trace_records': [identity(logs / (core + '-link.' + s + '.log')) for s in ('stdout', 'stderr')],
            'map': identity(map_path), 'trace_member_groups': len(groups), 'loaded_lines': loaded, 'direct_reads': direct_reads,
            'independently_resolved_map_archive_member_labels': len(map_labels),
            'duplicate_name_different_payload_groups': ambiguous,
            'member_selection_scope': 'Whole pinned archive/container closure PASS; actual map archive/member labels independently resolve to frozen containers and raw Reading/Loaded groups. Exact duplicate-name selected offsets and COFF symbol resolution are NOT independently attested.',
            'GPU_calls': 0, 'numeric_DLL_loads': 0}
