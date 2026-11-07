"""Portable fail-closed guards. No OS launches; constants are protocol limits."""
import datetime
import hashlib
import json
import math
from pathlib import Path


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


class FrozenBaseline:
    """The caller must supply the digest registered BEFORE the measured launch."""
    def __init__(self, root, expected):
        require(isinstance(expected, str) and len(expected) == 64, 'initial freeze digest required')
        self.root = Path(root).resolve()
        self.expected = expected
        raw = (self.root / 'CAPABILITY_FREEZE.json').read_bytes()
        require(digest(raw) == expected, 'initial freeze digest mismatch')
        frozen = json.loads(raw)
        self.members = tuple(sorted(frozen['files'].items()))
        require(self.members, 'empty freeze')
        for name, value in self.members:
            p = Path(name)
            require(not p.is_absolute() and '..' not in p.parts and ':' not in name and '\\' not in name,
                    'freeze path')
            require(self.root in (self.root / p).resolve().parents, 'freeze escape')
        self.check()

    def check(self):
        require(digest((self.root / 'CAPABILITY_FREEZE.json').read_bytes()) == self.expected,
                'FREEZE_REPLACED')
        for name, value in self.members:
            p = self.root / name
            require(self.root in p.resolve().parents and not p.is_symlink(), 'freeze escape')
            require(digest(p.read_bytes()) == value, 'SOURCE_DRIFT: ' + name)


class ProgressGuard:
    def __init__(self, pid, created_filetime):
        self.identity = (pid, created_filetime)
        self.last = None

    def check(self, row, now_ns):
        require((row['pid'], row['created_filetime']) == self.identity, 'watchdog identity')
        require(type(row['progress_seq']) is int and row['progress_seq'] > 0 and
                type(row['progress_ns']) is int, 'watchdog progress types')
        require(0 <= now_ns - row['progress_ns'] <= 5_000_000_000, 'WATCHDOG_PROGRESS_STALE')
        pair = (row['progress_seq'], row['progress_ns'])
        if self.last is not None:
            require(pair == self.last or (pair[0] > self.last[0] and pair[1] > self.last[1]),
                    'watchdog replay/regression')
        self.last = pair
        return dict(watchdog_progress_seq=pair[0], watchdog_progress_ns=pair[1],
                    watchdog_progress_age_ns=now_ns-pair[1])


def utc(value):
    require(isinstance(value, str), 'UTC string required')
    result = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(result.tzinfo is not None and result.utcoffset() == datetime.timedelta(0), 'UTC required')
    return result


def finite(value):
    require(type(value) in (float, int) and math.isfinite(value) and value >= 0, 'invalid elapsed time')
    return value


def revision_budget(registrations):
    runs, revisions, attempts = set(), set(), 0
    for r in registrations:
        require(type(r['revision']) is int and 0 <= r['revision'] <= 2, 'D0 revision budget')
        require(r['run'] not in runs, 'duplicate D0 run')
        runs.add(r['run']); revisions.add(r['revision'])
        n = r['case_attempts']
        require(type(n) is int and n > 0, 'invalid D0 attempt reservation')
        attempts += n
    require(len(revisions) <= 3 and attempts <= 20, 'D0 budget')
    return dict(revisions=len(revisions), reserved_attempts=attempts)


def wall_budget(acquisition, freeze, registrations, start, receipt, completion=None):
    """Reconstruct budget to an explicit frontier; never assert costs after it."""
    result = revision_budget(registrations)
    origin = utc(acquisition['first_preparation_utc'])
    frozen = utc(freeze['frozen_utc'])
    d0 = (frozen-origin).total_seconds()
    require(0 <= d0 <= 5400, 'D0_90_MINUTE_LIMIT')
    for r in registrations:
        require(origin <= utc(r['registered_utc']) <= frozen, 'D0 registration time')
    began = utc(start['started_utc'])
    age = (began-origin).total_seconds()
    require(age >= d0 and abs(age-finite(receipt['task_elapsed_before_watchdog_seconds'])) <= 0.01,
            'task origin/start reconciliation')
    require(type(receipt['begin_ns']) is int and type(receipt['end_ns']) is int and
            receipt['begin_ns'] == start['begin_ns'] <= receipt['end_ns'], 'watchdog time interval')
    measured_end = age+(receipt['end_ns']-receipt['begin_ns'])/1e9
    require(measured_end <= 21600, 'TASK_6_HOUR_LIMIT')
    result.update(development_seconds=d0, task_through_watchdog_seconds=measured_end)
    if completion is not None:
        # A terminal external receipt, bound separately by SHA256, covers restoration/delivery.
        final = (utc(completion['observed_utc'])-origin).total_seconds()
        require(abs(final-finite(completion['task_elapsed_seconds'])) <= 0.01,
                'completion elapsed reconciliation')
        require(completion['restoration_verified'] is True and completion['tool_exit_verified'] is True,
                'completion prerequisites')
        require(measured_end <= final <= 21600, 'TASK_6_HOUR_LIMIT')
        delivery = final-measured_end
        require(delivery <= 1800, 'DELIVERY_30_MINUTE_LIMIT')
        result.update(task_through_completion_seconds=final, delivery_seconds=delivery,
                      frontier_utc=completion['observed_utc'])
    return result


def admit_development_case(started, reserved):
    require(type(started) is int and type(reserved) is int and 0 <= started < reserved,
            'D0_RUN_RESERVATION_EXHAUSTED')
    return started + 1


def reconcile_development_attempts(root, registrations):
    """Count raw starts, including failed cases; declared PASS counts are irrelevant."""
    root = Path(root).resolve()
    revision_budget(registrations)
    total = 0
    for registration in registrations:
        rel = Path(registration['run'])
        require(not rel.is_absolute() and '..' not in rel.parts and ':' not in str(rel), 'D0 run path')
        folder = (root / rel).resolve()
        require(root in folder.parents, 'D0 run escape')
        count = 0
        for path in folder.glob('*/EVENTS.jsonl'):
            raw = path.read_bytes()
            require(not raw or raw.endswith(b'\n'), 'partial D0 case journal')
            rows = [json.loads(line) for line in raw.splitlines()]
            starts = [row for row in rows if row.get('event') == 'CASE_BEGIN']
            require(len(starts) == 1, 'D0 case start missing/duplicate')
            count += 1
        require(count <= registration['case_attempts'], 'D0 actual attempts exceed reservation')
        total += count
    require(total <= 20, 'D0 actual attempt budget')
    return total
