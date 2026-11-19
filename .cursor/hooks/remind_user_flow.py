import json
import sys
from pathlib import Path

raw = sys.stdin.read()
data = json.loads(raw) if raw.strip() else {}
marker = Path(".cursor/hooks/state/pending-flow.json")
if data.get("status") != "completed" or not marker.exists():
    print("{}")
    sys.exit(0)

try:
    payload = json.loads(marker.read_text(encoding="utf-8"))
except json.JSONDecodeError:
    payload = {}
marker.unlink(missing_ok=True)
files = ", ".join(payload.get("files", [])) or "backend/app"
message = (
    "Изменены файлы API: "
    + files
    + ". До завершения прогони затронутый user flow на http://127.0.0.1:8000 "
    "учёткой TEST_USER_EMAIL и TEST_USER_PASSWORD из backend/.env. "
    "Пароль, SECRET_KEY и SMTP-секреты не печатай и не записывай в issues.md. "
    "Допиши в backend/issues.md новую секцию: дата, сценарий и коды ответов. "
    "Каждую ошибку — отдельным пунктом (метод, путь, ожидание, факт). "
    "Если ошибок нет, напиши это явно. Старые секции не переписывай и не исправляй. Не коммить. "
    "POST /auth/password-reset на реальную почту вызывай только если менялся сам сброс; "
    "иначе проверь неизвестный email и ожидай 404."
)
print(json.dumps({"followup_message": message}, ensure_ascii=False))
