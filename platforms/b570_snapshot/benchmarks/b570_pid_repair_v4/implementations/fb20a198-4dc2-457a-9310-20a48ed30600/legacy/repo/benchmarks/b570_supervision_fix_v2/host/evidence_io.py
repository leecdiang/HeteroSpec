"""Every consumed byte belongs to a unique, authenticated manifest member."""
import hashlib
import json
from pathlib import Path, PurePosixPath
from storage_policy import checked_path


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('nonfinite JSON: ' + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)


class Evidence:
    def __init__(self, root, manifest):
        self.root = checked_path(root)
        self.manifest = checked_path(manifest, self.root)
        self.manifest_bytes = self.manifest.read_bytes()
        data = strict_json(self.manifest_bytes)
        self.members = {}
        self.consumed = set()
        for row in data['members']:
            name = row['path']
            p = PurePosixPath(name)
            if (not isinstance(name, str) or not name or p.is_absolute()
                    or '..' in p.parts or '\\' in name or ':' in name
                    or p.as_posix() != name or name in self.members):
                raise ValueError('unsafe/duplicate manifest member')
            self.members[name] = row
        if not self.members:
            raise ValueError('empty evidence manifest')
        for name in self.members:
            self.bytes(self.root / name)
        self.consumed.clear()

    def bytes(self, path):
        p = checked_path(path, self.root)
        if p == self.manifest:
            raw = p.read_bytes()
            if raw != self.manifest_bytes:
                raise ValueError('input manifest changed')
            return raw
        name = p.relative_to(self.root).as_posix()
        if name not in self.members:
            raise ValueError('consumed input absent from manifest: ' + name)
        row = self.members[name]
        raw = p.read_bytes()
        if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('manifest member changed: ' + name)
        self.consumed.add(name)
        return raw

    def json(self, path):
        return strict_json(self.bytes(path))

    def rows(self, path):
        raw = self.bytes(path)
        if raw and not raw.endswith(b'\n'):
            raise ValueError('incomplete journal record')
        return [strict_json(line) for line in raw.splitlines()]
