"""CPU raw-byte transport. Does not call a native runtime or certify captures.

Receipts deliberately use a synthetic schema rejected by N1a native snapshot
validation. Numerical tensor descriptors are compatible with raw_compare.js.
"""
from dataclasses import dataclass
import copy
import hashlib
import json
import math
import os
import re
import struct
from pathlib import Path


class CaptureError(ValueError):
    pass


def _need(value, message):
    if not value:
        raise CaptureError(message)


def _name(name):
    _need(isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9_-]+', name), 'unsafe identifier')
    return name


def _write_all(fd, data, write):
    offset = 0
    while offset < len(data):
        count = write(fd, memoryview(data)[offset:])
        _need(type(count) is int and 0 < count <= len(data) - offset, 'invalid/zero write')
        offset += count


@dataclass(frozen=True, init=False)
class OwnedTensor:
    """Immutable copy taken synchronously, before the caller mutates its buffer."""
    def __init__(self, raw, dtype, shape, axes):
        _need(isinstance(raw, (bytes, bytearray, memoryview)), 'raw bytes required')
        _need(dtype in ('F16LE', 'F32LE'), 'unsupported dtype')
        _need(type(shape) in (list, tuple) and len(shape) > 0, 'shape required')
        _need(all(type(n) is int and n >= 0 for n in shape), 'invalid shape')
        _need(type(axes) in (list, tuple) and len(axes) == len(shape), 'axes mismatch')
        _need(all(isinstance(a, str) and a for a in axes) and len(set(axes)) == len(axes), 'invalid axes')
        size = math.prod(shape) * (2 if dtype == 'F16LE' else 4)
        _need(size <= 2**53 - 1 and len(raw) == size, 'raw byte length mismatch')
        copied = bytes(raw)
        fmt = '<H' if dtype == 'F16LE' else '<I'
        mask = 0x7c00 if dtype == 'F16LE' else 0x7f800000
        for (bits,) in struct.iter_unpack(fmt, copied):
            _need(bits & mask != mask, 'nonfinite raw value')
        object.__setattr__(self, "_bytes", copied)
        object.__setattr__(self, "dtype", dtype)
        object.__setattr__(self, "shape", tuple(shape))
        object.__setattr__(self, "axes", tuple(axes))

    @property
    def raw(self):
        return self._bytes


class CaptureWriter:
    """Single exclusive capture directory with commit-last completion marker.

    Any I/O failure permanently closes this writer. Partial files are preserved and
    cannot be resumed/replaced; a new capture ID is needed. Root must already be
    a trusted, non-symlink directory; all subsequent operations use directory FDs.
    No actual numerical qualification is represented by these synthetic receipts.
    """
    def __init__(self, root, capture_id, *, run_id, operation_id, context_id,
                 source_sha256, executable_sha256, write=os.write):
        self._fd = None
        self._rootfd = None
        self._closed = False
        self._failed = False
        self._descriptors = {}
        self._write = write
        _name(capture_id)
        for label, digest in [('source', source_sha256), ('executable', executable_sha256)]:
            _need(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest), label + ' hash required')
        for value in (run_id, operation_id, context_id):
            _name(value)
        root = Path(root)
        _need(root.is_absolute(), 'absolute trusted root required')
        # Reject symlink components before open, and O_NOFOLLOW final component.
        current = Path(root.anchor)
        for part in root.parts[1:]:
            current = current / part
            _need(not current.is_symlink(), 'symlink root component')
        self._rootfd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.mkdir(capture_id, mode=0o700, dir_fd=self._rootfd)
            self._fd = os.open(capture_id, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=self._rootfd)
            os.fsync(self._rootfd)
        except BaseException:
            if self._fd is not None:
                os.close(self._fd)
                self._fd = None
            os.close(self._rootfd)
            self._rootfd = None
            raise
        self.capture_id = capture_id
        self.identity = dict(run_id=run_id, operation_id=operation_id, context_id=context_id,
                             source_sha256=source_sha256, executable_sha256=executable_sha256)

    def _ready(self):
        _need(not self._closed and not self._failed, 'capture closed/failed')

    def _file(self, name, raw):
        self._ready()
        fd = None
        try:
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=self._fd)
            _write_all(fd, raw, self._write)
            os.fsync(fd)
        except BaseException:
            self._failed = True
            raise
        finally:
            if fd is not None:
                os.close(fd)

    def tensor(self, name, owned):
        self._ready()
        _name(name)
        _need(isinstance(owned, OwnedTensor), 'owned tensor required')
        _need(name not in self._descriptors, 'duplicate tensor')
        filename = name + '.bin'
        self._file(filename, owned.raw)
        desc = dict(file=self.capture_id + '/' + filename, dtype=owned.dtype,
                    shape=list(owned.shape), axes=list(owned.axes), bytes=len(owned.raw),
                    sha256=hashlib.sha256(owned.raw).hexdigest())
        self._descriptors[name] = desc
        return copy.deepcopy(desc)

    def commit(self):
        self._ready()
        _need(self._descriptors, 'empty capture')
        result = dict(schema='hs.N1a.synthetic-capture.v1', evidence_class='SYNTHETIC',
                      native_qualified=False, actual_model_rows=0, actual_gpu_contexts=0,
                      **self.identity, tensors=self._descriptors)
        result['capture_writer_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        encoded = json.dumps(result, sort_keys=True, separators=(',', ':')).encode() + b'\n'
        # Incomplete marker is never named COMPLETE. Hard-link publishes only
        # after all bytes and fsync finish, without overwriting an existing name.
        self._file('manifest.pending', encoded)
        try:
            os.link('manifest.pending', 'COMPLETE.json', src_dir_fd=self._fd, dst_dir_fd=self._fd, follow_symlinks=False)
            os.fsync(self._fd)
        except BaseException:
            self._failed = True
            raise
        self.close()
        return result

    def close(self):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        if self._rootfd is not None:
            os.close(self._rootfd)
            self._rootfd = None
        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
