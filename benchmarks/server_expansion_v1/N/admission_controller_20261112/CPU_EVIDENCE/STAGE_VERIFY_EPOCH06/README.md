# Final stage-consumer CPU evidence

The current source-bound Python suite passed **20/20** on the actual A5000 host
in 394.597 seconds. This is not a model or GPU timing measurement.

The integrated artificial fixture was appended one role at a time. The actual
StageVerifier checked R27 → repeat81 → cold72 → strong81, the exact 261 distinct
frozen IDs, with the previous file seals re-read before each later stage. It
also verified the R handoff has all 18 bound canonical/head/stop/snapshot entries.
Afterward, an earlier-stage request with future files and a removed commit were
rejected. Other tests cover full-vector last-scalar differences, signed zero,
equal nonfinite bits, retained old-head strides, owned source-row binding,
EOG/cap/pending, reset, symlinks, duplicate JSON, mutable manifests and files
changing during or between transport/comparison reads.

All generated values and source identities are explicitly artificial CPU test
data. No native worker, model including vocabulary-only, backend, GPU context,
placement or forward ran. These are **zero native qualification checks**, not
261 native passes. Every stage report says PROVISIONAL_PROVIDED_BYTES_ONLY,
native_qualified=false and admission_authorized=false.

RECEIPT.json binds the exact current module, unit test, fixture/export source and
three immutable ancestor inputs. stdout.log contains the four stage summaries;
stderr.log is the complete unittest output. The logs needed no path redaction
and were copied byte for byte. The empty differential stderr is preserved.
Ordinary unit temporary fixture directories were cleaned by unittest; source
epochs, all raw logs and the separately exported differential raw-byte cases
remain in the private successor directory. No historical experiment data was
removed or overwritten.

The independent frozen-Node comparison is in audit/DIFFERENTIAL_FINAL_01.json:
12/12 artificial cases agree on the stated decision/raw-byte criteria. The
earlier diagnostic-only mismatch and all test epochs remain in the audit
reports. Two older redundant heavy tests were replaced by the incremental
four-stage test, reducing the number of test methods from21 to20 while expanding
positive staged coverage from R/strong to all four stages.
