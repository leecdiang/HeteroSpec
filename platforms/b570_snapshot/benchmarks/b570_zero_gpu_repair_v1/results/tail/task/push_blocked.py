import subprocess,json
from pathlib import Path
B=Path(__file__).resolve().parents[1];R=B/'repo';G='C:/hs/pr108-tools/git/cmd/git.exe'
subprocess.run([G,'add','--','benchmarks/b570_zero_gpu_repair_v1'],cwd=R,check=True)
subprocess.run([G,'add','-f','--','benchmarks/b570_zero_gpu_repair_v1/results/RAW_EVIDENCE.zip'],cwd=R,check=True)
subprocess.run([G,'-c','user.name=Codex','-c','user.email=codex@openai.com','-c','commit.gpgsign=false','commit','-m','Record blocked final implementation review and complete CPU evidence'],cwd=R,check=True)
subprocess.run([G,'push','origin','HEAD:refs/heads/codex/b570-zero-gpu-repair-20261016'],cwd=R,check=True)
subprocess.run([G,'rev-parse','HEAD'],cwd=R,check=True)
