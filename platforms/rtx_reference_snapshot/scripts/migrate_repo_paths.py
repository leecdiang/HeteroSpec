"""One-time, idempotent migration from the original fixed Windows project root."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPLACEMENT = 'Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1]))'

for path in (ROOT / "scripts").glob("*.py"):
    if path.name == Path(__file__).name:
        continue
    text = path.read_text(encoding="utf-8")
    updated = text.replace('Path(r"D:\\HeteroSpec-PC")', REPLACEMENT).replace("Path(r'D:\\HeteroSpec-PC')", REPLACEMENT)
    updated = updated.replace('default=r"D:\\HeteroSpec-PC\\telemetry\\nvidia_idle_30s.csv"',
                              'default=str(Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1])) / "telemetry" / "nvidia_idle_30s.csv")')
    if updated != text and "import os" not in updated:
        lines = updated.splitlines()
        lines.insert(1 if lines and lines[0].startswith("#!") else 0, "import os")
        updated = "\n".join(lines) + "\n"
    if updated != text:
        path.write_text(updated, encoding="utf-8")

for path in (ROOT / "reports").rglob("*.md"):
    text = path.read_text(encoding="utf-8")
    updated = text.replace("D:\\HeteroSpec-PC\\", "")
    if updated != text:
        path.write_text(updated, encoding="utf-8")
