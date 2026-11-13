'use strict';
// Prospective resource arithmetic only. No deployment, model or device API.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
if(process.argv.length!==4)throw Error('Usage: node resource_budget.js FRESH_RESOURCE_SNAPSHOT_JSON FRESH_OUTPUT_JSON');
const [snapshotFile,out]=process.argv.slice(2);const bytes=fs.readFileSync(snapshotFile),packet=JSON.parse(bytes),snapshot=packet.resource_snapshot||packet;
const availableStorage=Number.isSafeInteger(snapshot.available_storage_bytes)?snapshot.available_storage_bytes:Math.min(...snapshot.disks.map(d=>d.available_bytes));
const devices=snapshot.target_device||snapshot.target_UUID_matching_devices||[];
const digest=x=>crypto.createHash('sha256').update(x).digest('hex');
const publicDevices=devices.map(d=>({uuid_sha256:d.uuid_sha256||snapshot.target_uuid_sha256||(d.uuid?digest(Buffer.from(d.uuid)):null),name:d.name,free_MiB:Number(d.free_MiB)}));
const MiB=1024**2,GiB=1024**3,requests=76,kv=36*8*4096*128*2*2,vocabularyRow=151936*4;
const tensorPerRequest=3*kv+132*vocabularyRow,metadataBudget=76*5*MiB;
const tensorBytes=76*tensorPerRequest,journal=512*MiB,raw=tensorBytes+metadataBudget+journal;
const archive=Math.ceil(raw*1.02)+16*MiB,restore=raw,buildText=8*GiB,protectedFree=100*GiB;
const required=raw+archive+restore+buildText+protectedFree;
if(required!==553094505923)throw Error('Unexpected frozen prospective resource arithmetic');
// Metadata composition is independent of a per-request average: final turns
// have a RESET and may be larger than setups. Preserve the global380MiB bound.
const state=252,owned=72,records=99,producer=32;
const plannedMetadata=state*(MiB+2*64*1024)+owned*(64*1024+2*64*1024)+records*64*1024+producer*MiB;
const failureMetadata=4*(4*(MiB+2*64*1024)+2*(64*1024+2*64*1024)+3*64*1024+MiB);
const markerAllowance=MiB;
if(plannedMetadata+failureMetadata+markerAllowance>metadataBudget)throw Error('Metadata no longer fits aggregate380MiB envelope');
const baseFiles=252*6+72*4+99,producerFiles=producer;
const failureFiles=4*(4*6+2*4+3+1),partialMarkers=4*6*2;
const captureDirectories=252+72+4*(4+2);
const knownArchiveEntries=baseFiles+producerFiles+failureFiles+partialMarkers+captureDirectories;
const archiveEntryCeiling=4096;
const result={schema:'hs.N1chain.prospective-resource-budget.v1',status:'PROPOSED_NOT_APPROVED_NOT_MEASURED',execution_authorized:false,
 current_GPU_execution_authorized:false,model_or_backend_or_context_or_placement_or_forward_operations_performed:0,
 source_snapshot_sha256:crypto.createHash('sha256').update(bytes).digest('hex'),observed_utc:snapshot.observed_utc,
 proposed_limits:{planned_requests:72,failed_consumption_request_reserve:4,request_ceiling:76,planned_model_rows:69354,failed_consumption_row_reserve:16384,model_rows_ceiling:85738,
  backend_initializations:10,model_loads:10,native_context_creations:10,placement_reservations:10,preflight_probes:2,workers:8,
  placement_semantics:'Reserve once before native ELF exec, verify existing reservation inside worker; probes are placeholders until separately approved and implemented.',
  command_ceiling_proposal:250000,journal_bytes_hard_ceiling:journal,automatic_retry:false,STATE_reentry:false},
 byte_budget:{active_KV_C4096_F16:kv,full_F32_vocabulary_row:vocabularyRow,raw_tensor_ceiling:tensorBytes,aggregate_metadata_ceiling:metadataBudget,
  planned_metadata_composition_ceiling:plannedMetadata,failure_metadata_composition_ceiling:failureMetadata,partial_marker_bytes_allowance:markerAllowance,
  global_journal_ceiling:journal,raw_including_journal:raw,archive_ceiling:archive,strict_restore_ceiling:restore,
  build_and_text_excluding_global_journal_allowance:buildText,protected_free_space:protectedFree,available_space_required:required,
  note:'Includes132 fullrows/request conservatively covering sampling/frontier and ownership copies; RESET rawtensorbytes are0. Archive uses2percent expansion plus16MiB headers; source/model weights are separately bound, not duplicated into rawcaptures.'},
 archive_file_budget:{planned_state_payload_files:252*6,planned_owned_payload_files:72*4,planned_transition_and_binding_files:99,planned_base_files:baseFiles,
  actual_planned_producer_receipts:24,planned_files_including_actual_producer_receipts:baseFiles+24,
  producer_scope:'Own producer for R/repeat/strong natural requests only; cold oracle replays R canonical IDs and has no independent producer. The32-record bound is conservative allowance, not an executed or planned32-producer count.',
  additional_natural_or_oracle_producer_receipt_allowance:producerFiles,failed_request_file_allowance:failureFiles,OPEN_UNCERTAIN_partial_marker_allowance:partialMarkers,
  capture_directory_entry_allowance:captureDirectories,known_file_and_directory_entries:knownArchiveEntries,outer_archive_entry_ceiling:archiveEntryCeiling,
  remaining_entries_for_worker_logs_indices_global_ledger_and_build_metadata:archiveEntryCeiling-knownArchiveEntries,
  required_archive_guard:'At most4096 outerentries, each header/PAX envelope at most4096bytes;16MiB totalheader budget. Do not silently include an unbounded extracted upstream tree.'},
 current_readonly_resources:{available_RAM_bytes:snapshot.memory.MemAvailable_KiB*1024,available_workspace_bytes:availableStorage,target_devices:publicDevices,target_compute_process_count:snapshot.target_compute_process_count??snapshot.target_compute_processes?.length??null},
 disk_snapshot_exceeds_proposed_requirement:availableStorage>=required,
 required_RAM_bytes_proposal:48*GiB,required_worker_RSS_hard_ceiling_proposal:24*GiB,protected_host_RAM_proposal:24*GiB,
 wall_time:{watchdog_seconds:18000,status:'UNMEASURED_WATCHDOG_NOT_ETA',note:'RPC/fsync cost and real model/capture work are unmeasured. Exceeding deadline must preserve partial data and stop, without starting a new worker.'},
 gates:['Fresh resource/UUID/quiet-window verification before any future admission.','Native schema producer receipts, capture/record size caps, entrycount/ledger caps and actual controller graph must remain enforced.','Ten deployment limits include two prospective probe placements and eight workers; no existing quota or old STATE is reused.','Accounting ACKs, static source maps and compiled linkage are not native execution permission.']};
fs.writeFileSync(out,JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({required_bytes:required,metadata_budget:metadataBudget,metadata_composition:plannedMetadata+failureMetadata+markerAllowance,base_files:baseFiles,known_archive_entries:knownArchiveEntries,status:result.status},null,2));
