# Active-KV source/layout and read-only audit

All five complete frozen source gates match. Complete files were copied from the
actual cache and rehashed; none was reconstructed from excerpts. The reference
source tree's3545 files, loop4/packed trees'3539 each, and every recorded dependency
file in five relevant BUILD closures all match. Seven original/later worker ELF
files match BUILD receipts. These files were never invoked.

The original numerical reference tree is run-01/stage-03/sources/reference and its
backend archives are run-01/build-R-01/native/llama/. The matching strong core trees
are run-01/stage-04/sources/loop4 and packed, with archives under the corresponding
run-01/build-loop4-01 and build-packed-01/native/llama/. Original CUDA86/static build
cache and full command records are copied privately. The CPU producer runtime is
not substituted for these numerical libraries. Historical BUILD_NOT_QUALIFIED
fields are build-time records, not a new assessment of old study qualifications.

The actual public C++ memory API accepts llama_io_write_i. Its scalar write and
write_tensor(tensor,offset,size) callbacks can stream the existing memory export
without a monolithic sequence vector. Direct memory export omits the context's
outer io_magic/seq_id prefix and must not be mislabeled the original sequence.bin.

Reference source locations:

- llama-io.h9–18: scalar/tensor streaming callbacks.
- llama-memory.h125: virtual memory state_write.
- llama-kv-cache.cpp2053–2120: active sequence-cell range selection.
- llama-kv-cache.cpp2203–2232: native position/sequence metadata.
- llama-kv-cache.cpp2236–2332: types and actual K/V tensor slices.
- llama-model.cpp2695–2700: default dense cache uses !flash_attn for V transpose.
- llama-context.cpp3088–3092: full sequence export prefix.

Flash attention disabled means Vtrans=true. Both nominal K/V storage view shapes
are [1024,4096], but V physical bytes are dim-major: source233–244 creates those
views and source2326–2328 explicitly addresses (physical+j*kv_size)*2. K uses
physical*1024*2. Inferring V physical order from nominal ne alone is incorrect.

Prepared active_kv.cpp validates one C4096 sequence/stream, F16 K/V, no cell_ext,
layer IDs0..35, all actual physical cells' unique logical positions0..head-1 and
sequence ownership. It parses native scalar framing and authenticates actual
storage/slice order. K/V are gathered as exact F16LE [8,head,128] bytes using the
observed physical map. Only active values are checked/emitted; inactive bytes
never reach the sink. Peak adapter tensor buffers are8MiB physical + up to8MiB
canonical, plus bounded scalar metadata. Actual hardware capture was not run.

The concrete ProductionGate precedes synchronize and every tensor read and denies
this entire native path in the current build. Native source compiled against both
reference and loop4 headers. Because -O2 deletes the permanently denied body,
-O0 -fno-lto compilation was also inspected to retain real llama/cache/tensor API
references for the parent's actual-library link. No native-linked executable was
run. The separate standard-library-only synthetic host test passed194 checks,
covering all36 layer labels, nonidentity physical maps, transposed V, finite active
values, ignored inactive NaNs, malformed metadata and reset/empty framing.

The resource snapshot is an observation, not admission: target GPU currently has
no compute PID; another GPU has one compute process whose identity was not
collected/published. Current task is CPU-only, so no GPU execution is authorized.
An additional valid allocation/window and full native qualification remain needed.

PUBLIC_READONLY_AUDIT.json contains exact hashes and sanitized figures. Complete
source files, private allocation/ledger inventory and original logs remain in the
private audit directory. No model object, backend init, context, placement or
forward was created; full GGUF bytes were read only for file SHA-256.

