import os
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1]))
SOURCE = ROOT / "datasets" / "Spec-Bench" / "data" / "spec_bench" / "question.jsonl"
OUT = ROOT / "env"
SEED = 20260903


rows = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()]
mt_categories = {"writing", "roleplay", "reasoning", "math", "coding", "extraction", "stem", "humanities"}
groups = defaultdict(list)
for row in rows:
    task = "multi_turn" if row["category"] in mt_categories else row["category"]
    groups[task].append(row["question_id"])

rng = random.Random(SEED)
pilot = []
holdout = []
for category in sorted(groups):
    ids = sorted(groups[category], key=str)
    rng.shuffle(ids)
    if len(ids) != 80:
        raise RuntimeError(f"Expected 80 rows for {category}, found {len(ids)}")
    pilot.extend({"question_id": value, "category": category} for value in ids[:10])
    holdout.extend({"question_id": value, "category": category} for value in ids[10:])

if len(pilot) != 60 or len(holdout) != 420:
    raise RuntimeError("Unexpected split size")
if {item["question_id"] for item in pilot} & {item["question_id"] for item in holdout}:
    raise RuntimeError("Pilot and holdout overlap")

metadata = {
    "seed": SEED,
    "source": str(SOURCE),
    "source_rows": len(rows),
    "category_counts": Counter(row["category"] for row in rows),
    "pilot_per_category": 10,
    "holdout_per_category": 70,
}
(OUT / "specbench_pilot_ids.json").write_text(json.dumps({"metadata": metadata, "items": pilot}, indent=2), encoding="utf-8")
(OUT / "specbench_holdout_ids.json").write_text(json.dumps({"metadata": metadata, "items": holdout}, indent=2), encoding="utf-8")
print(json.dumps({"pilot": len(pilot), "holdout": len(holdout), "categories": sorted(groups)}, indent=2))
