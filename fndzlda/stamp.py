"""Version + last-commit date for the startup banner."""
from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fndzlda import __version__

PACKAGE = Path(__file__).resolve().parent
COMMIT_FILE = PACKAGE / ".commit"


def _git_date() -> str:
    cur = PACKAGE
    for _ in range(6):
        if (cur / ".git").exists():
            try:
                proc = subprocess.run(
                    ["git", "log", "-1", "--format=%cI"],
                    cwd=str(cur),
                    capture_output=True,
                    text=True,
                    timeout=4,
                )
            except (OSError, subprocess.TimeoutExpired):
                return ""
            if proc.returncode == 0:
                return (proc.stdout or "").strip()
            return ""
        if cur.parent == cur:
            break
        cur = cur.parent
    return ""


def _file_date() -> str:
    if not COMMIT_FILE.is_file():
        return ""
    try:
        lines = COMMIT_FILE.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    if len(lines) >= 2 and lines[1].strip():
        return lines[1].strip()
    return ""


def _short_sha() -> str:
    try:
        text = COMMIT_FILE.read_text(encoding="utf-8").splitlines()[0].strip()
    except OSError:
        text = ""
    return text[:7]


def _pretty_date(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return datetime.now().astimezone().strftime("%Y-%m-%d")
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%Y-%m-%d")
    except ValueError:
        return raw[:10]


def banner_line() -> str:
    date = _pretty_date(_file_date() or _git_date())
    sha = _short_sha()
    if sha:
        return f"v{__version__}  ·  {date}  ·  {sha}"
    return f"v{__version__}  ·  {date}"
