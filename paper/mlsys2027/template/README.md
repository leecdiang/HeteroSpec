# Official MLSys template staging area

MLSys 2027 explicitly instructs authors to use the **same LaTeX submission format as MLSys 2025** and links the official archive `mlsys2025style.zip`.

Official source:
https://media.mlsys.org/Conferences/MLSYS2025/mlsys2025style.zip

## Rule

Import the official archive **unchanged** into this directory (or an immediately adjacent `style/` directory) before creating the compilable manuscript source.

Do not reconstruct the style from memory and do not copy an unofficial mirror when the official package is available.

After import:
1. record SHA256 for every template/style file;
2. commit the original style files in one dedicated commit;
3. create the manuscript source by copying the official example;
4. retain the double-blind submission mode for the review version;
5. do not alter margins, font sizes, spacing, or column geometry.

The current repository setup intentionally does not invent LaTeX invocation details that were not verified from the official archive.
