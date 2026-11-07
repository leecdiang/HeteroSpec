"""Portable v6 guard primitives; native adapter MUST call these on the live path.
No Windows qualification, transport authenticity, or CPU8 PASS is implied here.
"""
import hashlib
import json
from pathlib import PureWindowsPath

CASES=('normal_single','normal_transition','terminal_pending_completion',
       'frozen_input','late_closed_slot_write','resource_read_failure',
       'directory_read_timeout','journal_write_failure')
RESERVES={'development':(7200,3600),'acceptance':(3600,1800),'delivery':(0,0)}

def need(ok,why):
    if not ok: raise ValueError(why)

def strict_int(v):
    need(type(v) is int and v>=0,'nonnegative integer required')
    return v

def digest(data):
    return hashlib.sha256(data).hexdigest()

def reserve(stage,used_lifetime_s,next_lifetime_bound_s,used_wall_s,next_wall_bound_s):
    """Integer CEILING charges, one campaign origin. No budget reset at stages."""
    need(stage in RESERVES,'unknown stage')
    u,n,w,t=map(strict_int,(used_lifetime_s,next_lifetime_bound_s,used_wall_s,next_wall_bound_s))
    life_reserve,wall_reserve=RESERVES[stage]
    need(u+n+life_reserve<=21600,'reserved lifetime unavailable')
    need(w+t+wall_reserve<=21600,'reserved wall unavailable')
    return {'stage':stage,'lifetime_remaining_after_reserve':21600-u-n-life_reserve,
            'wall_remaining_after_reserve':21600-w-t-wall_reserve}

def role_guard(mode,root,original_root):
    need(mode in ('live','reconstruct'),'unknown verifier role')
    same=PureWindowsPath(root)==PureWindowsPath(original_root)
    if mode=='live': need(same,'live qualification requires original run root')
    return 'LIVE_CHECKS_REQUIRED' if mode=='live' else 'RECONSTRUCTION_ONLY'

def bind_invocation(intent,events,external_hashes):
    """Reconcile exact tool exports against trusted capture-index hashes.
    external_hashes comes from the capture supervisor, NOT candidate receipt JSON.
    This checks evidence consistency; it cannot authenticate the capture provider.
    Normalized event JSON records must retain raw provider exports separately.
    """
    need(type(events) is list and bool(events),'actual tool events missing')
    need(len(events)==len(external_hashes),'capture membership mismatch')
    seen=set();session=None;terminal=False
    for i,(raw,expected) in enumerate(zip(events,external_hashes)):
        need(type(raw) is bytes and digest(raw)==expected,'tool capture bytes')
        e=json.loads(raw);cid=e['call_id'];need(type(cid) is str and cid and cid not in seen,'tool call identity');seen.add(cid)
        need(e['invocation_id']==intent['invocation_id'],'wrong invocation')
        req=e['request'];resp=e['response'];need(not terminal,'event after terminal')
        if i==0:
            need(e['operation']=='exec' and req==intent['request'],'actual request mismatch')
            session=resp.get('session_id')
            need(session is None or (type(session) is int and session>0),'session type')
        else:
            need(session is not None and e['operation']=='poll','unexpected tool operation')
            need(req.get('session_id')==session and type(req.get('session_id')) is int,'session mismatch')
            returned=resp.get('session_id')
            need(returned is None or (type(returned) is int and returned==session),'response session mismatch')
        need(type(resp.get('output')) is str,'actual output missing')
        if resp.get('exit_code') is not None:
            need(type(resp['exit_code']) is int and resp['exit_code']==0,'tool nonzero exit')
            terminal=True
    need(terminal,'tool has not completed')
    return {'status':'INVOCATION_CONSISTENT','terminal_call_id':cid,
            'output':json.loads(events[-1])['response']['output']}

def bind_download(raw_body,expected_git_blob,expected_sha256,expected_size):
    need(type(raw_body) is bytes,'download bytes required')
    need(len(raw_body)==strict_int(expected_size),'download length')
    need(digest(raw_body)==expected_sha256,'download digest')
    actual=hashlib.sha1(b'blob '+str(len(raw_body)).encode()+b'\0'+raw_body).hexdigest()
    need(actual==expected_git_blob,'download Git identity')
    return digest(raw_body)

def final_gate(*,mode,live_budget_checked,cases,review_clean,delivery_verified,tool_bound):
    """Only downstream of original native/raw/freeze checks; never a standalone auditor."""
    need(mode in ('live','reconstruct'),'unknown verifier role')
    if mode=='reconstruct':return 'RECONSTRUCTION_ONLY'
    need(live_budget_checked is True,'current budget checks mandatory')
    need(review_clean is True,'final deployed review missing')
    need(type(cases) is list and [x.get('id') for x in cases]==list(CASES),'eight exact ordered cases')
    need(all(x.get('native_qualified') is True for x in cases),'native qualification missing')
    if delivery_verified is not True or tool_bound is not True:return 'CPU8_CASES_PASS_DELIVERY_PENDING'
    return 'CPU8_INTEGRATION_PASS'
