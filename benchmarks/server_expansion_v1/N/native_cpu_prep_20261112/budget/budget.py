"""CPU-only durable mock budget rehearsal. No GPU/native execution entry point.

A successful reservation permits *only mock work*. This module deliberately cannot
admit N1a execution. The 76/85,738/10 proposal is not a default authorization.
Filesystem assumptions: local POSIX fsync/flock semantics; no network filesystem.
"""
import fcntl
import hashlib
import json
import os
import time
from pathlib import Path

class Blocked(RuntimeError):
    pass

def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode() + b'\n'

def integer(value):
    if type(value) is not int or value < 0:
        raise Blocked('nonnegative integer required')
    return value

class MockBudget:
    def __init__(self, directory, manifest, *, clock=time.time, monotonic=time.monotonic, write=os.write, sync=os.fsync):
        self.directory = Path(directory)
        self.clock, self.write, self.sync = clock, write, sync
        self.monotonic = monotonic
        self.lock_fd = None
        self.poisoned = False
        self.manifest = json.loads(encoded(manifest))
        m = self.manifest
        if m.get('mode') != 'CPU_MOCK_ONLY' or not m.get('run_id') or not m.get('source_sha256'):
            raise Blocked('explicit CPU_MOCK_ONLY identity required')
        if len(m['source_sha256']) != 64 or any(c not in '0123456789abcdef' for c in m['source_sha256']):
            raise Blocked('invalid source digest')
        if type(m.get('deadline_epoch')) not in (int, float) or not (0 < m['deadline_epoch'] < float('inf')):
            raise Blocked('finite fixed deadline required')
        self.monotonic_deadline = monotonic() + max(0, m['deadline_epoch'] - clock())
        for key in ('requests', 'rows', 'placements'):
            integer(m['limits'][key])
        for item, cap in m['request_rows'].items():
            if not item or not isinstance(item, str):
                raise Blocked('invalid request ID')
            integer(cap)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock_fd = os.open(self.directory / 'LOCK', os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.fingerprint = hashlib.sha256(encoded(m)).hexdigest()
            self.events, self.requests, self.placements = [], {}, set()
            self.counts = dict(requests=0, rows=0, placements=0)
            if (self.directory / 'UNCERTAIN').exists():
                raise Blocked('uncertain durable transaction; manual reconciliation required')
            log = self.directory / 'ledger.jsonl'
            if log.exists():
                raw = log.read_bytes()
                if not raw.endswith(b'\n'):
                    raise Blocked('partial ledger; manual reconciliation required')
                for line in raw.splitlines():
                    event = json.loads(line)
                    self._apply(event)
                if not self.events or self.events[0] != self._header():
                    raise Blocked('manifest identity mismatch')
            else:
                self._append(self._header())
        except BaseException:
            self.close()
            raise

    def _header(self):
        return dict(kind='header', manifest_sha256=self.fingerprint, manifest=self.manifest)

    def _apply(self, event):
        if not self.events:
            if event != self._header():
                raise Blocked('identity mismatch')
        else:
            kind = event.get('kind')
            ident = event.get('id')
            if kind == 'request':
                if ident in self.requests or ident not in self.manifest['request_rows']:
                    raise Blocked('duplicate or unplanned request')
                self.requests[ident] = 0
                self.counts['requests'] += 1
            elif kind == 'rows':
                amount = integer(event['amount'])
                if not amount or ident not in self.requests:
                    raise Blocked('invalid row reservation')
                self.requests[ident] += amount
                self.counts['rows'] += amount
                if self.requests[ident] > self.manifest['request_rows'][ident]:
                    raise Blocked('per-request row cap')
            elif kind == 'placement':
                if not isinstance(ident, str) or not ident or ident in self.placements:
                    raise Blocked('duplicate/invalid placement')
                self.placements.add(ident)
                self.counts['placements'] += 1
            else:
                raise Blocked('unknown event')
            if any(self.counts[k] > self.manifest['limits'][k] for k in self.counts):
                raise Blocked('total cap')
        self.events.append(event)

    def _append(self, event):
        # Validate before touching disk, without accepting memory state on failure.
        old = (list(self.events), dict(self.requests), set(self.placements), dict(self.counts))
        try:
            self._apply(event)
        finally:
            self.events, self.requests, self.placements, self.counts = old
        marker = self.directory / 'UNCERTAIN'
        fd = None
        dfd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(fd, b'write transaction not committed\n')
            self.sync(fd)
            os.close(fd); fd = None
            self.sync(dfd)
            fd = os.open(self.directory / 'ledger.jsonl', os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
            data = encoded(event)
            # A short write is uncertain, not retried under the same allowance.
            if self.write(fd, data) != len(data):
                raise OSError('short ledger write')
            self.sync(fd)
            os.close(fd); fd = None
            self.sync(dfd)
            marker.unlink()
            self.sync(dfd)
            self._apply(event)
        except BaseException:
            self.poisoned = True
            raise
        finally:
            if fd is not None:
                os.close(fd)
            os.close(dfd)

    def _ready(self):
        if self.lock_fd is None or self.poisoned:
            raise Blocked('closed/poisoned ledger')
        if self.clock() >= self.manifest['deadline_epoch'] or self.monotonic() >= self.monotonic_deadline:
            raise Blocked('fixed run deadline exceeded')

    def begin_request(self, request_id):
        self._ready()
        self._append(dict(kind='request', id=request_id))

    def reserve_rows(self, request_id, rows):
        self._ready()
        self._append(dict(kind='rows', id=request_id, amount=rows))

    def reserve_mock_placement(self, placement_id):
        self._ready()
        self._append(dict(kind='placement', id=placement_id))

    def admit_native(self, *_args, **_kwargs):
        raise Blocked('CPU_ONLY: native context, GPU placement and forward forbidden')

    def close(self):
        if self.lock_fd is not None:
            os.close(self.lock_fd)
            self.lock_fd = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
