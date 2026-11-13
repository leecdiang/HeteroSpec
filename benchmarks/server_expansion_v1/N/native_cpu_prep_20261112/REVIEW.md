# CPU preparation review

Independent mock review found and fixed a concrete initial lifecycle defect: after part of append executed, a row-budget failure left a short frontier available to sampling. Explicit phases now prevent this; partial forward failures poison the session. It also rejects begin-over-active-request, changed canonical/cap, duplicate append, post-terminal sampling, observed head drift and inconsistent pending state. These are mock caller tests, not proof of native KV retention.

The writer's byte descriptor was passed to the existing unmodified #226 comparator. Four bytes of synthetic F16 data were read and compared, including signed zero. Its synthetic receipt was rejected by native snapshot validation. This is an interoperability test, not a 261-check qualification run.

The original source gate uses SHA values from #225 evidence/SOURCE_AUDIT.json, not filenames or matching version labels. A locally available older oracle header has a different SHA from the audited Linux deployment, so it was not substituted. Full native compilation/linking remains blocked; only the independent mock C++ caller was compiled.

No benchmark/GPU process was launched. Repository acquisition initially downloaded a large incomplete full clone; it was stopped and retained separately, then a successful sparse clone obtained the frozen protocol and source excerpts. The partial clone is not experimental evidence, and no old source or result was deleted.
