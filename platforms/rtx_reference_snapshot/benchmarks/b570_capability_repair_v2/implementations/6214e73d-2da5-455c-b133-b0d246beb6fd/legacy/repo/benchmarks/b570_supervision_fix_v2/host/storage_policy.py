"""Shared path policy; no special CPU permission or content-equality exemption."""
import os
from pathlib import Path
import stat

NOTIFY_FILTER = 1 | 2 | 4 | 8 | 0x10 | 0x100


def checked_path(path, root=None):
    # Inspect lexical ancestors before resolve() erases reparse/alias evidence.
    p = Path(os.path.abspath(path))
    for item in [p, *p.parents]:
        s = item.lstat()
        if stat.S_ISLNK(s.st_mode) or getattr(s, 'st_file_attributes', 0) & 0x400:
            raise ValueError('alias/reparse path forbidden')
    resolved = p.resolve(strict=True)
    if root is not None:
        base = checked_path(root)
        if resolved != base and base not in resolved.parents:
            raise ValueError('resolved path outside registered root')
    return resolved


def identity(path):
    p = checked_path(path)
    s = p.stat()
    if not p.is_dir() and s.st_nlink != 1:
        raise ValueError('hard-linked file forbidden')
    return dict(path=str(p), volume=s.st_dev, file_id=s.st_ino,
                bytes=s.st_size, mtime_ns=s.st_mtime_ns, ctime_ns=s.st_ctime_ns,
                mode=s.st_mode, attributes=getattr(s, 'st_file_attributes', 0))


def authorize(path, root, kind, state):
    p = checked_path(path, root)
    ident = identity(p)
    # CLOSING never admits a replacement just because its contents match.
    return kind == 'content' and state == 'ACTIVE', p, ident


def notification_kind(kind, action, registered_slot):
    # Metadata MODIFIED for a known slot has one policy across overlapping guards.
    # Add/delete/rename of the slot name remains a namespace mutation.
    if kind in ('namespace', 'rootmeta') and registered_slot and action == 3:
        return 'content'
    return kind


def injection_target(target, fixture, task_root):
    root = checked_path(fixture)
    base = checked_path(task_root)
    path = checked_path(target, root)
    if base not in root.parents or path == root:
        raise ValueError('injection must stay inside a fresh task fixture')
    return path, root
