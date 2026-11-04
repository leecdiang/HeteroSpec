# Reproduce from this repository

From the repository root:

    cd experiments/masked_q8_mma/ftz_audit
    python check_domain.py
    python audit_recipe.py --cuda /path/to/cuda-13.2.2 \
      --frozen-entries ../frozen_reference_audit/ptx --output /fresh/ftz-audit

Both scripts reject Python -O because assertions are checks. The three committed frozen PTX entry snippets are read only and checked against fixed hashes; they are not executed as standalone PTX modules. The new experimental source is compiled independently. The fatbinary contains sm89 and sm120a, not a universal SM80+ image.

The recorded `validation-v2` results were independently reviewed. `published-layout-validation/RECIPE_RESULTS.json` repeats the actual compilation with the short filenames used by the committed frozen-reference audit; candidate kernel hash and opcode counts match. Full generated PTX, SASS and binary files are not committed here; rebuild them with the script. Their exact recorded hashes, resource logs and instruction summary remain available.

A successful compilation is not GPU numerical validation. The recorded GPU witness exits77 due to the missing driver/device. On a suitable device it is only one finite fixture, not full R qualification. Only fused=true can match the observed frozen update recipe; keep unfused modes as negative controls.

Run the separate portable review on your freshly generated artifacts:

    python independent/review_ftz.py --audit . --validation /fresh/ftz-audit \
      --frozen-entries ../frozen_reference_audit/ptx \
      --original-source ../kernels.cu --output /fresh/ftz-review.json

The reviewer uses explicit exceptions rather than assertions, checks the frozen-entry/source/helper hashes, verifies every artifact recorded by the recipe, checks FTZ scalar opcodes and independently reconstructs half scales and the signed-byte FMA witness on CPU. It does not run the GPU binary. Historical REVIEW.json remains unchanged; REVIEW_PUBLISHED_LAYOUT.json records the rerun using the published short PTX names.
