"""Renewable, hash-chained work reservations. Reservations never erase actual costs."""
from pathlib import Path
from common import canonical, digest, need, read, utc
import json
import os


def load(path):
    rows = []
    previous = '0' * 64
    if not Path(path).exists():
        return rows
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        x = json.loads(line)
        h = x.pop('hash')
        need(x['prev'] == previous and digest(x) == h, 'ledger chain corruption')
        x['hash'] = h
        rows.append(x)
        previous = h
    return rows


def append(path, event):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = load(path)
    event = dict(event, utc=utc(), prev=rows[-1]['hash'] if rows else '0' * 64)
    event['hash'] = digest(event)
    with path.open('a', encoding='utf-8') as f:
        f.write(canonical(event).decode() + '\n')
        f.flush()
        os.fsync(f.fileno())
    return event


def totals(path):
    result = {'credit_limit': 0, 'seconds_limit': 0., 'credits_reserved': 0,
              'completed_model_requests': 0, 'operator_calls': 0, 'owned_seconds': 0., 'open': {}}
    for r in load(path):
        kind = r['event']
        if kind == 'EXTEND':
            need(r['reason'].strip() and r['credits'] >= 0 and r['seconds'] >= 0, 'bad extension')
            result['credit_limit'] += r['credits']
            result['seconds_limit'] += r['seconds']
        elif kind == 'START':
            need(r['attempt'] not in result['open'], 'duplicate active attempt')
            result['open'][r['attempt']] = r
            result['credits_reserved'] += r['credits']
        elif kind == 'END':
            need(r['attempt'] in result['open'], 'END without START')
            start = result['open'].pop(r['attempt'])
            need(0 <= r['completed_model_requests'] <= start['requests'], 'impossible completed count')
            need(r['operator_calls'] >= 0 and r['seconds'] >= 0, 'negative accounting')
            result['completed_model_requests'] += r['completed_model_requests']
            result['operator_calls'] += r['operator_calls']
            result['owned_seconds'] += r['seconds']
        else:
            need(kind == 'NOTE', 'unknown accounting event')
    return result


def extend(path, credits, seconds, reason):
    need(type(credits) is int and credits >= 0 and seconds >= 0 and reason.strip(), 'specific extension reason required')
    need(not totals(path)['open'], 'reconcile active attempts before extension')
    return append(path, {'event': 'EXTEND', 'credits': credits, 'seconds': seconds, 'reason': reason})


def reserve(path, attempt, requests, diagnostic_calls, maximum_seconds):
    t = totals(path)
    need(not t['open'], 'unsettled prior attempt; reconcile real process and receipt')
    need(type(requests) is int and type(diagnostic_calls) is int and min(requests, diagnostic_calls) >= 0, 'counts')
    credits = requests + diagnostic_calls
    need(t['credits_reserved'] + credits <= t['credit_limit'], 'extend reservation with next question; do not reset ledger')
    need(t['owned_seconds'] + maximum_seconds <= t['seconds_limit'], 'extend time reservation before launch')
    need(not any(r.get('attempt') == attempt for r in load(path)), 'attempt ID already used')
    return append(path, {'event': 'START', 'attempt': attempt, 'requests': requests,
                         'diagnostic_calls': diagnostic_calls, 'credits': credits,
                         'maximum_seconds': maximum_seconds})
