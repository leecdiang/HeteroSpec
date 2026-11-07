# Additive draft delivery contract

Base: actual main `e87291d26df32f2cb9571e005ab173b1c7a6830b` verified live on2026-10-08. Branch: `codex/b570-pr64-cpu-closeout-v2`. Allowed diff: additions only under `benchmarks/b570_pr64_cpu_closeout_v2/`.

Scientific dependencies stay external: PR63 `66594b349955e66146702325559c26019ea16485`; PR64 `68421206452c22caef19c9fb34452cb04a3f99b3`. Their heads/states must be read again after delivery. No old study merged into this branch. No merge, release, tag or manuscript update.

The small archive contains only this CPU evidence snapshot and its code/hashes; original raw/KV/model bulk is referenced by its immutable CAS. Fresh remote delivery is verified **after** creating the new Draft PR, so the final head-bound readback receipt is outside the commit that it checks (private retained receipt plus PR closeout comment). This avoids a self-referential head/hash claim.

Readback: initialize a separate temporary Git directory, fetch only this new remote branch into an empty object store with depth1 and a blob size filter, verify exact commit, enumerate its entire added directory and read every blob with Git, compare every SHA256/size to local delivery files, then compare the additive diff against the fixed main base. ZIP bytes and internal INDEX are rechecked from the fetched blob. Never use an existing checkout/object store as proof of fresh remote bytes.

The final report/PR comment must say VERIFIED only after these steps pass; until then the scientific CPU audit and remote delivery are separate states.
