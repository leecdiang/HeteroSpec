#!/usr/bin/env python3
"""Copy this manuscript into a NEW local repository folder; no Git/network actions."""
from __future__ import annotations
import argparse,shutil
from pathlib import Path

def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',required=True,type=Path)
    ap.add_argument('--apply',action='store_true',help='Actually copy; by default only preview.')
    args=ap.parse_args()
    src=Path(__file__).resolve().parents[1]; repo=args.repo.expanduser().resolve()
    if not (repo/'.git').exists(): raise SystemExit('Destination must be a local Git checkout (.git directory or worktree file).')
    dst=repo/'paper/jsa/manuscript_v0150'
    if dst.exists(): raise SystemExit(f'Refusing to overwrite an existing directory: {dst}')
    if dst==src or src in dst.parents: raise SystemExit('Source and destination must be separate.')
    print(f'New destination: {dst}')
    if not args.apply:
        print('Preview only. Rerun with --apply after reviewing. No files or Git objects changed.');return
    def ignore(path: str,names: list[str])->set[str]:
        suffixes=('.aux','.log','.out','.toc','.fls','.fdb_latexmk','.blg','.pass1.txt','.pass2.txt','.pass3.txt','.bibtex.txt')
        return {n for n in names if n=='__pycache__' or n.endswith(suffixes)}
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(src,dst,ignore=ignore)
    print('Copied manuscript only. No commit, push, PR or merge was performed. Review PR_BODY.md before creating a Draft PR.')
if __name__=='__main__': main()
