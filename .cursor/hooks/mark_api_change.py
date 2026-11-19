import json
import sys
from pathlib import Path

raw = sys.stdin.read()
data = json.loads(raw) if raw.strip() else {}
path = str(data.get("file_path", "")).replace("\\", "/")
normalized = path.lower()
watched = (
    "/backend/app/routers/",
    "/backend/app/services/",
    "/backend/app/schemas/",
)
if not any(part in normalized for part in watched):
    sys.exit(0)

state = Path(".cursor/hooks/state")
state.mkdir(parents=True, exist_ok=True)
marker = state / "pending-flow.json"
files: list[str] = []
if marker.exists():
    try:
        files = list(json.loads(marker.read_text(encoding="utf-8")).get("files", []))
    except json.JSONDecodeError:
        files = []
if path not in files:
    files.append(path)
marker.write_text(json.dumps({"files": files}, ensure_ascii=False, indent=2), encoding="utf-8")
