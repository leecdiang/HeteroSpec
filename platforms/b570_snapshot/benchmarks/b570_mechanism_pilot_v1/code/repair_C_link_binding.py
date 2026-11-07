"""Before first model request, resolve actual common import-library binding."""
from pathlib import Path
import json,shutil,datetime
R=Path(__file__).parent;P=Path('C:/hs/b570-direct-id-v1-src');F=R/'candidate-front'
assert not any(json.loads(l).get('unit_id','').startswith('C/') for l in (R/'LEDGER.jsonl').read_text().splitlines())
shutil.copyfile(R/'C_FREEZE.json',R/'C_PRE_FORWARD_FREEZE_0.json')
shutil.copytree(P/'common',R/'candidate-common')
s=(F/'CMakeLists.txt').read_text(encoding='utf8')
s=s.replace('foreach(kind native target)', '''file(GLOB COMMON "../candidate-common/*.cpp" "../candidate-common/jinja/*.cpp")
add_library(llama-common-b570-pilot STATIC ${COMMON})
target_compile_features(llama-common-b570-pilot PRIVATE cxx_std_17)
target_compile_options(llama-common-b570-pilot PRIVATE /utf-8 /bigobj)
target_compile_definitions(llama-common-b570-pilot PRIVATE LLAMA_SUBPROCESS _CRT_SECURE_NO_WARNINGS LLAMA_SHARED GGML_SHARED GGML_BACKEND_SHARED GGML_USE_CPU GGML_USE_VULKAN)
target_include_directories(llama-common-b570-pilot PRIVATE ../candidate-common "${PINNED_SOURCE}/include" "${PINNED_SOURCE}/ggml/include" "${PINNED_SOURCE}/vendor")
target_link_libraries(llama-common-b570-pilot PUBLIC llama-b570-pilot "${PINNED_BUILD}/common/Release/llama-common-base.lib" "${PINNED_BUILD}/vendor/cpp-httplib/Release/cpp-httplib.lib" "${PINNED_BUILD}/ggml/src/Release/ggml.lib" "${PINNED_BUILD}/ggml/src/Release/ggml-base.lib" ws2_32 shell32)
foreach(kind native target)''')
s=s.replace('"${PINNED_BUILD}/common/Release/llama-common.lib"','llama-common-b570-pilot')
(F/'CMakeLists.txt').write_text(s,encoding='utf8')
for p in (R/'sessions').glob('C-*'):
 if not (p/'SESSION.json').exists():
  (p/'PREFLIGHT_FAILURE.json').write_text(json.dumps(dict(reason='Windows loader missing old llama.dll through original llama-common.dll dependency. Original llama-common.lib is an import library, not a static library.',exit_code=3221225781,model_loads=0,full_requests=0,auxiliary_forwards=0,fix='Rebuild unchanged pinned common source as isolated static common library linked exclusively to private llama-b570-pilot DLL.'),indent=2)+'\n')
  (p/'SESSION_CLOSE.json').write_text(json.dumps(dict(process_exit_code=3221225781,model_session_cleanup_seconds=0,preflight_only=True))+'\n')
amend=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),kind='PRE_FIRST_FORWARD_BUILD_BINDING_CORRECTION',all_C_model_attempts_before_amendment=0,old_freeze='C_PRE_FORWARD_FREEZE_0.json',scientific_family_unchanged=True,decision_commit='415a503e4a378e596f970695ec2234d40745097b',reason='dumpbin proved old common.lib is a DLL import library. Rebuild unchanged common code in isolation; do not load two llama libraries or overwrite published DLLs.',scientific_retry=False,additional_private_sources='unchanged pinned common sources',numerical_changes_after_scientific_output=0)
(R/'C_PRE_FORWARD_BINDING_AMENDMENT.json').write_text(json.dumps(amend,indent=2)+'\n',encoding='utf8')
print('Binding amended before any C model load/request; old freeze and failure retained.')
