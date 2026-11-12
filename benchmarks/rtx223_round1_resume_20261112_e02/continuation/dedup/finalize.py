from pathlib import Path
import json,hashlib,sqlite3,shutil,datetime
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PRIVATE=HERE/'private'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
old=ROOT/'rtx221-round1-20261112'
src=old/'resources/ledger.sqlite';dst=PRIVATE/'e01-ledger.sqlite';shutil.copy2(src,dst)
db=sqlite3.connect('file:'+str(dst.resolve()).replace('\\','/')+'?mode=ro',uri=True)
epoch_rows=db.execute('select * from epoch').fetchall();attempts=db.execute('select * from attempts').fetchall();db.close()
history=sqlite3.connect('file:'+str((PRIVATE/'thread_history_1.sqlite').resolve()).replace('\\','/')+'?mode=ro',uri=True)
stats=history.execute('select count(*),max(started_at),max(completed_at) from thread_turns').fetchone();history.close()
catalog=json.loads((PRIVATE/'CATALOG_MATCHES.json').read_bytes())
targets=json.loads((PRIVATE/'TARGET_TIMELINES.json').read_bytes())
process=json.loads((HERE/'PROCESS_LOCK_LEDGER.json').read_bytes())
nt=json.loads((PRIVATE/'NT_PROCESSES.json').read_bytes())
prompt=json.loads((PRIVATE/'GLOBAL_MATCHES.json').read_bytes())[0]['full']
(HERE/'ORIGINAL_PROMPT_FROM_LOCAL_CACHE.md').write_text(prompt,encoding='utf8')
known_titles=['合并关闭PR并审阅','第一轮结论汇总']
thread_rows=[]
for x in targets:
    r=x['catalog'][0]
    thread_rows.append({'thread_id':x['thread_id'],'title':r['display_title'],'source_updated_utc':datetime.datetime.fromtimestamp(r['source_updated_at'],datetime.timezone.utc).isoformat(),'async_status':r['chatgpt_async_status'],'timeline_records':len(x['records']),'binding_to_execution':'PR221 candidate by exact prior title' if r['display_title']==known_titles[0] else 'PR223 candidate by title/time only, not content-bound','current_terminal_evidence':False})
expected={
'D:\\rtx192-review-v2\\ledger.sqlite':'58597a16ed833165cd2d3ee1f6d176fc7eb7697fbfd8369b7a51a5862baeabd0',
'D:\\rtx211-q8-20261109\\ledger.sqlite':'e9390101ffa4781cb0b4d859173afdd449aa2847402fdd6a3eb84a06ffcfa42e',
str(ROOT/'q8rtx213-supplement-runtime-20261109/ledger.sqlite'):'5671a7c693408a2e9521dc78d70cd06244afc784c3e9d4c595005ab3b99500da'}
ledger_checks=[{'path':p,'expected_sha256':h,'actual_sha256':sha(p),'match':sha(p)==h} for p,h in expected.items()]
result={
'schema':'heterospec.rtx223.resume-dedup.v1',
'observed_utc':now(),'verdict':'INCONCLUSIVE','gpu_admission':'BLOCKED_DEDUP_UNVERIFIED',
'app_api':{'list_threads':'MCP -32000 from root','read_thread_by_discovered_id':'Both exact candidate IDs returned MCP -32000'},
'local_cli_history':{'threads_database':'state_5.sqlite copy','history_database':'thread_history_1.sqlite copy','latest_completed_utc':datetime.datetime.fromtimestamp(stats[2],datetime.timezone.utc).isoformat(),'turns':stats[0],'target_marker_matches':0,'scope':'Older local Codex sessions end on Nov09; no #221/#223 execution receipts'},
'local_app_catalog':{'database':'codex.db copy including WAL/SHM','integrity':catalog['integrity'],'latest_catalog_source_updated_utc':datetime.datetime.fromtimestamp(catalog['catalog_stats']['latest_source_updated'],datetime.timezone.utc).isoformat(),'candidate_threads':thread_rows,'active_turn_count':catalog['active_turn_count'],'empty_active_turn_table_is_not_terminal_attestation':True},
'process_inventory':{'toolhelp_observed_utc':process['observed_utc'],'toolhelp_visible_processes':process['process_probe']['total_processes'],'NT_observed_utc':nt['utc'],'NT_visible_processes':len(nt['records']),'scope':'Restricted execution process namespace; only current PowerShell/Python tree is exposed. Not a host-wide worker absence proof.','host_scope_verified':False,'no_relevant_worker_observed_in_visible_namespace':True},
'locks':process['locks'],
'legacy_ledgers':ledger_checks,
'parent_epoch_ledger':{'path':str(src),'sha256':sha(src),'copied_before_sqlite_read':True,'epoch_rows':epoch_rows,'attempt_count':len(attempts),'gpu_usage_snapshot':json.loads((old/'resources/LEDGER_SNAPSHOT.json').read_bytes())['reserved'],'pending_attempts':0},
'parent_delivery':{'path':str(ROOT/'HeteroSpec_RTX221_Round1_20261112_v2.zip'),'sha256':sha(ROOT/'HeteroSpec_RTX221_Round1_20261112_v2.zip'),'matches_published':sha(ROOT/'HeteroSpec_RTX221_Round1_20261112_v2.zip')=='791f60490de6784d132d0f182eaf650849aa15cd7bd940cb28a59a21d7647d34'},
'original_prompt':{'source':'Local app prompt-history chatgpt-global item12 markdown','path':'ORIGINAL_PROMPT_FROM_LOCAL_CACHE.md','sha256':sha(HERE/'ORIGINAL_PROMPT_FROM_LOCAL_CACHE.md'),'scope':'User prompt cache only; not an execution/liveness receipt'},
'device_observation':process['nvidia_smi'],'device_idle_alone_not_used_for_admission':True,
'missing_evidence':['Content-bound current terminal/lease evidence for original #221 and #223 execution threads','Host-wide current relevant worker process scope or equivalent trusted supervisor lease'],
'action':'Stop before GPU admission. CPU/source/build/guard tests may continue. Do not delete unknown locks, terminate foreign processes, or infer completion from GPU idle.',
'new_model_requests':0,'new_target_draft_rows':0,'new_GPU_launches':0,
'raw_private_exclusion':'Never export continuation/dedup/private/**; contains copied databases and unrelated cached catalog data',
'preparation_failures':[{'operation':'first query_history shell one-liner','failure':'Quoting syntax error before DB query; resolved with script file'},{'operation':'first local paths in process probe','failure':'Wrong parent directory level gave false missing-file observations; initial receipt retained privately and corrected before final decision'},{'operation':'first NT process probe','failure':'Codec spelling utf16le unsupported; corrected to utf-16-le; no mutation or GPU activity'}],
'script_hashes':{p.name:sha(p) for p in HERE.glob('*.py')}
}
(HERE/'DEDUP_RESULT.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf8')
print(json.dumps({'verdict':result['verdict'],'missing_evidence':result['missing_evidence'],'candidates':thread_rows,'old_ledgers_unchanged':all(x['match'] for x in ledger_checks),'parent_attempts':len(attempts),'visible_process_scope_verified':False,'new_GPU_launches':0},ensure_ascii=True,indent=2))
