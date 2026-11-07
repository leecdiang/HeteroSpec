# Reference/source history through PR162

The full reviewed CUDA mechanism/reproduction chain is retained at `rtx_reference_snapshot/`, exactly Git tree `9f4ffed5d6048bab85e3e48907fa453f7111e0f0` from final delivery commit `0f2bb3a3482e58f6f48aadf936a8a43c14bcbf37`. Its scientific data snapshot and delivery-only successor remain distinct. The original Llama failed practical-performance screen is not changed.

Namespace preservation avoids overwriting later main's common manifests and manuscript with historical same-name files. To replay, create a detached worktree at that exact commit. Use sparse checkout or a partial clone for Linux preparation; the Linux build does not need the historical KV/raw archives. Snapshot inclusion does not claim all old sources are Linux-portable or requalified. New Linux work uses the final PR195 recipe, with this history available only for original-source provenance.
