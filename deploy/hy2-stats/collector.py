#!/usr/bin/env python3
"""Accumulate Hysteria traffic counters across server restarts."""
import json
import os
import tempfile
import urllib.request
from datetime import datetime, timezone

api_url = os.environ.get("HY2_STATS_URL", "http://127.0.0.1:19999/traffic")
secret = os.environ["HY2_STATS_SECRET"]
state_path = os.environ.get("HY2_STATS_STATE", "/var/www/html/hy2-stats/traffic-total.json")

request = urllib.request.Request(api_url, headers={"Authorization": secret})
with urllib.request.urlopen(request, timeout=10) as response:
    current = json.load(response)

try:
    with open(state_path, encoding="utf-8") as stream:
        state = json.load(stream)
except (FileNotFoundError, json.JSONDecodeError):
    state = {"users": {}, "raw": {}}

totals = state.get("users", {})
previous = state.get("raw", {})
for user, counters in current.items():
    old = previous.get(user, {"tx": 0, "rx": 0})
    total = totals.setdefault(user, {"tx": 0, "rx": 0})
    for key in ("tx", "rx"):
        value = int(counters.get(key, 0))
        before = int(old.get(key, 0))
        total[key] += value if value < before else value - before

state = {
    "updatedAt": datetime.now(timezone.utc).isoformat(),
    "users": totals,
    "raw": current,
}
directory = os.path.dirname(state_path)
os.makedirs(directory, exist_ok=True)
fd, temporary = tempfile.mkstemp(prefix="traffic-total.", dir=directory, text=True)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(state, stream, ensure_ascii=False, separators=(",", ":"))
        stream.write("\n")
    os.chmod(temporary, 0o644)
    os.replace(temporary, state_path)
except Exception:
    try:
        os.unlink(temporary)
    except FileNotFoundError:
        pass
    raise
