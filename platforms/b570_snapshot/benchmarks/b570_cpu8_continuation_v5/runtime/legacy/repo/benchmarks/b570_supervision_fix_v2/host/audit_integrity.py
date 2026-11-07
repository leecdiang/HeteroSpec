"""Whole-round checks. No selection of one convenient detector or close flag."""
from pathlib import PureWindowsPath


def sequence(rows):
    previous = -1
    for index, row in enumerate(rows, 1):
        if row.get('seq') != index or type(row.get('at_ns')) is not int or row['at_ns'] < previous:
            raise ValueError('journal sequence/time gap')
        previous = row['at_ns']


def watch_lifetimes(rows):
    sequence(rows)
    states = {}
    for row in rows:
        event = row['event']
        key = row.get('watch_id')
        if event == 'WATCH_ARMED':
            if key in states:
                raise ValueError('duplicate watcher identity')
            states[key] = dict(pending=False, closing=False, closed=False, armed_count=0)
        elif event in ('IO_ARMED', 'IO_COMPLETION', 'WATCH_CLOSE_BEGIN', 'CANCEL_ISSUED', 'WATCH_CLOSED'):
            if key not in states or states[key]['closed']:
                raise ValueError('event outside watcher lifetime')
            state = states[key]
            if event == 'IO_ARMED':
                if state['pending'] or state['closing']:
                    raise ValueError('overlapping/rearmed closing I/O')
                state['pending'] = True;state['armed_count'] += 1
            elif event == 'IO_COMPLETION':
                if not state['pending']:
                    raise ValueError('completion without pending I/O')
                if not row['success'] and not (state['closing'] and row['error'] == 995):
                    raise ValueError('failed I/O completion')
                state['pending'] = False
            elif event == 'WATCH_CLOSE_BEGIN':
                if state['closing'] or row['pending'] != state['pending']:
                    raise ValueError('incorrect close boundary')
                state['closing'] = True
            elif event == 'CANCEL_ISSUED':
                if not state['closing'] or not state['pending'] or not (row['success'] or row['error'] == 1168):
                    raise ValueError('incorrect cancellation')
            else:
                if not state['armed_count'] or not state['closing'] or state['pending'] or row['pending'] or not row['directory_closed'] or not row['event_closed']:
                    raise ValueError('closed before actual completion')
                state['closed'] = True
    if not states or not all(s['closed'] for s in states.values()):
        raise ValueError('unclosed watcher lifetime')
    ends = [r for r in rows if r['event'] == 'WATCH_STREAM_CLOSED']
    if len(ends) != 1 or ends[0].get('error') is not None or rows[-1] != ends[0]:
        raise ValueError('watch stream not successfully closed')
    return states


def validate_pending_probe(cfg, rows, watch, handle, handles, close_begin, round_close):
    key=handle['watch_id']
    if handle['owner']!='pending_probe' or handle['kind']!='sealed':
        raise ValueError('invalid temporary probe identity')
    specs=[s for s in cfg['cases'] if s['id']=='terminal_pending_completion']
    begins=[r for r in rows if r['event']=='CASE_BEGIN' and r['case_id']=='terminal_pending_completion']
    ends=[r for r in rows if r['event']=='CASE_CLOSED' and r['case_id']=='terminal_pending_completion']
    ready=[r for r in watch if r['event']=='PENDING_PROBE_READY' and r['watch_id']==key]
    signaled=[r for r in watch if r['event']=='PENDING_COMPLETION_SIGNALED' and r['watch_id']==key]
    if not all(len(items)==1 for items in (specs,begins,ends,ready,signaled)):
        raise ValueError('temporary probe lacks unique case/control evidence')
    root=str(PureWindowsPath(handle['root'])).lower()
    if (root!=str(PureWindowsPath(specs[0]['target']).parent).lower()
            or not begins[0]['at_ns']<=handle['at_ns']<ready[0]['at_ns']<signaled[0]['at_ns']<=close_begin[key]<ends[0]['at_ns']):
        raise ValueError('temporary probe outside intended target/control interval')
    if not any(h['watch_id']!=key and h['kind']=='sealed' and h['owner']!='pending_probe'
               and str(PureWindowsPath(h['root'])).lower()==root and h['at_ns']<=handle['at_ns']
               and close_begin[h['watch_id']]>=round_close for h in handles.values()):
        raise ValueError('temporary probe cannot replace permanent protection')


def round_integrity(cfg, rows, watch, controller_end, launch, launcher_close):
    sequence(rows)
    watch_lifetimes(watch)
    if (not rows or rows[0]['event'] != 'ROUND_STARTED' or rows[-1]['event'] != 'ROUND_CLOSED'
            or sum(r['event'] == 'ROUND_CLOSED' for r in rows) != 1
            or any(r['event'] == 'ROUND_STOP' for r in rows)):
        raise ValueError('round closure failed')
    if (controller_end.get('error') is not None or not controller_end.get('CPU_only')
            or controller_end['finished_ns'] < rows[-1]['at_ns']
            or launch.get('exit_code') != 0 or launch['end_ns'] < controller_end['finished_ns']
            or launcher_close.get('status') != 'CLOSED_SUCCESS'
            or launcher_close.get('controller_exit_code') != 0
            or launcher_close.get('error') is not None or launcher_close.get('stop_reason') is not None
            or launcher_close.get('readers_completed') != 2):
        raise ValueError('controller/launcher did not close successfully')
    specs = {s['id']: s for s in cfg['cases']}
    windows = {}
    current = None
    slot_states = {key: 'PREPARED' for key in cfg['registry']}
    transitions = {'PREPARED': {'ACTIVE'}, 'ACTIVE': {'CLOSING'}, 'CLOSING': {'SEALED', 'FAILED'}}
    decisions = {r['seq']: r for r in watch if r['event'] == 'NOTIFY_DECISION'}
    matched = set()
    roots = {str(PureWindowsPath(r['root'])).lower() for r in watch if r['event'] == 'WATCH_ARMED' and r['kind'] != 'rootmeta'}
    handles = {r['watch_id']: r for r in watch if r['event'] == 'WATCH_ARMED'}
    close_begin = {r['watch_id']: r['at_ns'] for r in watch if r['event'] == 'WATCH_CLOSE_BEGIN'}
    round_close = [r['at_ns'] for r in rows if r['event'] == 'ROUND_CLOSE_BEGIN']
    if len(round_close) != 1:
        raise ValueError('missing unique round close begin')
    for slot, entry in cfg['registry'].items():
        root = str(PureWindowsPath(entry['path'])).lower()
        original = [h for h in handles.values() if h['owner'] == slot and h['kind'] == 'content' and str(PureWindowsPath(h['root'])).lower() == root]
        if len(original) != 1:
            raise ValueError('registered slot lacks unique content guard')
    for h in handles.values():
        if h['owner']=='pending_probe':
            validate_pending_probe(cfg,rows,watch,h,handles,close_begin,round_close[0])
            continue
        if h['kind'] in ('namespace', 'rootmeta') or (h['kind'] == 'sealed' and h['owner'] not in cfg['registry']):
            if close_begin[h['watch_id']] < round_close[0]:
                raise ValueError('persistent guard stopped before round close')
    # Parent guards must cover the registered directory itself, not just descendants.
    for root in roots:
        parent = str(PureWindowsPath(root).parent).lower()
        if not any(h['kind'] == 'rootmeta' and str(PureWindowsPath(h['root'])).lower() == parent for h in handles.values()):
            raise ValueError('protected root metadata unguarded')
    for row in rows:
        event = row['event']
        if event == 'CASE_BEGIN':
            if current is not None or row['case_id'] in windows or row['case_id'] not in specs:
                raise ValueError('overlapping/duplicate/unknown case')
            current = row['case_id'];windows[current] = [row['at_ns'], None]
        elif event == 'CASE_CLOSED':
            if current != row['case_id'] or not row['cleanup_complete']:
                raise ValueError('case close mismatch')
            windows[current][1] = row['at_ns'];current = None
        elif event == 'SLOT_STATE':
            slot = row['slot'];old = slot_states.get(slot)
            if row['previous'] != old or row['state'] not in transitions.get(old, set()):
                raise ValueError('illegal slot transition')
            if row['state']=='ACTIVE':
                initial=next(h for h in handles.values() if h['owner']==slot and h['kind']=='content')
                io=[r for r in watch if r.get('watch_id')==initial['watch_id'] and r['event'] in ('IO_ARMED','IO_COMPLETION','WATCH_CLOSE_BEGIN') and r['at_ns']<=row['at_ns']]
                if not io or io[-1]['event']!='IO_ARMED':raise ValueError('slot activation without pending content I/O')
            slot_states[slot] = row['state']
            if row['state'] in ('SEALED', 'FAILED'):
                handoff = row['handoff']
                armed = handles.get(handoff['new'])
                closed = [r for r in watch if r['event'] == 'WATCH_CLOSED' and r['watch_id'] == handoff['old']]
                new_io=[r for r in watch if r.get('watch_id')==handoff['new'] and r['event']=='IO_ARMED']
                old_handle=handles.get(handoff['old']);root=str(PureWindowsPath(cfg['registry'][slot]['path'])).lower()
                if (not armed or not old_handle or len(closed) != 1
                        or not new_io or new_io[0]['at_ns']>=close_begin[handoff['old']]
                        or armed['owner'] != slot or old_handle['owner'] != slot
                        or armed['kind'] != 'sealed' or old_handle['kind'] != 'content'
                        or any(str(PureWindowsPath(h['root'])).lower()!=root for h in (armed,old_handle))
                        or close_begin[armed['watch_id']] < round_close[0]
                        or not (armed['at_ns'] < closed[0]['at_ns'] <= row['at_ns'])):
                    raise ValueError('immutable handoff missing or interrupted')
        elif event == 'DETECTOR':
            if current is None or row.get('case_id') != current:
                raise ValueError('rejection outside its active case')
            spec = specs[current]
            if (spec['kind'] != 'negative' or row['code'] != spec['detector']
                    or row['target'].lower() != spec['target'].lower()
                    or row.get('fault_id') != f"{cfg['round']}:{current}"):
                raise ValueError('unrelated rejection cannot qualify another fault')
            detail = row.get('detail') or {}
            if row['code'] == 'SEALED_WRITE_REJECTED':
                decision = decisions.get(detail.get('decision_seq'))
                if (not decision or decision['seq'] in matched or decision['allowed']
                        or not decision.get('in_scope', True)
                        or decision['watch_id'] != detail.get('watch_id')
                        or decision['raw_seq'] != detail.get('raw_seq')
                        or decision['canonical'] != row['target'].lower()
                        or decision['at_ns'] > row['at_ns']):
                    raise ValueError('raw decision/detector binding mismatch')
                matched.add(decision['seq'])
        elif event in ('GO_SENT', 'CONTINUE_SENT'):
            if current is None or any(r['event'] == 'DETECTOR' and r.get('case_id') == current and r['at_ns'] <= row['at_ns'] for r in rows):
                raise ValueError('command after rejection/outside case')
    if current is not None:
        raise ValueError('unclosed case')
    for decision in decisions.values():
        handle = handles[decision['watch_id']]
        in_scope = handle['kind'] != 'rootmeta' or decision['canonical'] in roots
        if decision.get('in_scope') is not in_scope:
            raise ValueError('notification scope mismatch')
        if in_scope and not decision['allowed'] and decision['seq'] not in matched:
            raise ValueError('unreconciled denied raw event')
        if decision['allowed']:
            owner = decision['owner']
            prior = [r for r in rows if r['event'] == 'SLOT_STATE' and r['slot'] == owner and r['at_ns'] <= decision['at_ns']]
            if (not in_scope or owner not in cfg['registry'] or not prior or prior[-1]['state'] != 'ACTIVE'
                    or (handle['kind'] != 'content' and (decision['action'] != 3 or decision['canonical'] != str(PureWindowsPath(cfg['registry'][owner]['path'])).lower()))
                    or decision['state'] != 'ACTIVE' or decision.get('policy_error')
                    or not decision.get('file_identity')):
                raise ValueError('allowed event not backed by active slot state')
    if any(state not in ('PREPARED', 'SEALED', 'FAILED') for state in slot_states.values()):
        raise ValueError('slot left active/closing')
    return True
