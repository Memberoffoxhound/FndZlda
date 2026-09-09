"""On load, check GitHub main and pull the latest commit.

Git clones fast-forward with git. Windows EXE / install.sh copies
download the commit zip and replace the fndzlda package, then restart
so the new code actually runs. A failed check never blocks the hunt.
"""
from __future__ import annotations

import io
import json
import os
import shutil
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

REPO = "Memberoffoxhound/FndZlda"
BRANCH = "main"
API_URL = f"https://api.github.com/repos/{REPO}/commits/{BRANCH}"
ZIP_URL = f"https://codeload.github.com/{REPO}/zip/{{sha}}"
UA = "FndZlda"
TIMEOUT = 12.0

PACKAGE = Path(__file__).resolve().parent
COMMIT_FILE = PACKAGE / ".commit"


@dataclass
class UpdateResult:
    action: str  # skip, current, updated, failed
    local: str = ""
    remote: str = ""
    detail: str = ""


def parse_remote_sha(body: str) -> str:
    try:
        data = json.loads(body or "")
    except json.JSONDecodeError:
        return ""
    sha = data.get("sha") if isinstance(data, dict) else ""
    if not isinstance(sha, str):
        return ""
    sha = sha.strip().lower()
    if len(sha) < 7 or any(c not in "0123456789abcdef" for c in sha):
        return ""
    return sha


def same_commit(local: str, remote: str) -> bool:
    a, b = (local or "").lower().strip(), (remote or "").lower().strip()
    if not a or not b:
        return False
    n = min(len(a), len(b), 40)
    return n >= 7 and a[:n] == b[:n]


def repo_root(start: Path | None = None) -> Path | None:
    cur = (start or PACKAGE).resolve()
    if cur.is_file():
        cur = cur.parent
    for _ in range(8):
        if (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def _http_get(url: str, timeout: float = TIMEOUT) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read()


def _git(args: list[str], cwd: Path, timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "echo"
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


def local_sha(package: Path = PACKAGE, root: Path | None = None) -> str:
    root = root if root is not None else repo_root(package)
    if root is not None:
        try:
            proc = _git(["rev-parse", "HEAD"], root, timeout=5.0)
        except (OSError, subprocess.TimeoutExpired):
            proc = None
        if proc is not None and proc.returncode == 0:
            sha = (proc.stdout or "").strip().lower()
            if sha:
                return sha
    marker = package / ".commit"
    try:
        return marker.read_text(encoding="utf-8").strip().lower()[:40]
    except OSError:
        return ""


def write_commit(package: Path, sha: str) -> None:
    try:
        (package / ".commit").write_text(sha.strip().lower() + "\n", encoding="utf-8")
    except OSError:
        pass


def apply_zipball(package: Path, blob: bytes) -> int:
    """Replace package *.py from a GitHub commit zip. Returns files written."""
    written = 0
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            parts = Path(info.filename).parts
            if "__pycache__" in parts or info.filename.endswith(".pyc"):
                continue
            # FndZlda-<sha>/fndzlda/foo.py
            try:
                idx = parts.index("fndzlda")
            except ValueError:
                continue
            rest = parts[idx + 1 :]
            if len(rest) != 1 or not rest[0].endswith(".py") or rest[0] in (".", ".."):
                continue
            dest = package / rest[0]
            dest.write_bytes(zf.read(info.filename))
            written += 1
    cache = package / "__pycache__"
    shutil.rmtree(cache, ignore_errors=True)
    return written


def restart_argv(argv: list[str] | None) -> list[str]:
    rest = list(argv or [])
    if "--no-update" not in rest:
        rest.insert(0, "--no-update")
    return rest


def _reexec(argv: list[str] | None) -> None:
    os.execv(sys.executable, [sys.executable, "-m", "fndzlda", *restart_argv(argv)])


def check_and_apply(
    *,
    no_update: bool = False,
    restart: bool = True,
    argv: list[str] | None = None,
    package: Path | None = None,
    http_get=None,
    git_pull=None,
    reexec=None,
    quiet: bool = False,
) -> UpdateResult:
    """Fetch GitHub main. Pull or unpack if we are behind. Optionally restart."""
    if no_update or os.environ.get("FNDZLDA_NO_UPDATE"):
        return UpdateResult("skip", detail="disabled")
    pkg = package or PACKAGE
    get = http_get or _http_get
    try:
        raw = get(API_URL)
        if isinstance(raw, str):
            body = raw
        else:
            body = raw.decode("utf-8", "replace")
        remote = parse_remote_sha(body)
    except (OSError, urllib.error.URLError, TimeoutError, ValueError) as e:
        result = UpdateResult("failed", detail=str(e) or "network")
        _say(result, quiet)
        return result
    if not remote:
        result = UpdateResult("failed", detail="bad GitHub response")
        _say(result, quiet)
        return result
    root = repo_root(pkg)
    local = local_sha(pkg, root)
    if same_commit(local, remote):
        result = UpdateResult("current", local=local, remote=remote)
        _say(result, quiet)
        return result

    try:
        if root is not None and git_pull is None:
            proc = _git(["pull", "--ff-only", "origin", BRANCH], root)
            if proc.returncode != 0:
                err = (proc.stderr or proc.stdout or "git pull failed").strip()
                low = err.lower()
                if "not possible to fast-forward" in low or "diverg" in low:
                    result = UpdateResult(
                        "skip", local=local, remote=remote, detail="diverged"
                    )
                    if not quiet:
                        print("  local git is ahead or diverged — not pulling")
                    return result
                raise RuntimeError(err)
        elif root is not None and git_pull is not None:
            git_pull(root, remote)
        else:
            zip_bytes = get(ZIP_URL.format(sha=remote))
            if isinstance(zip_bytes, str):
                zip_bytes = zip_bytes.encode("utf-8")
            n = apply_zipball(pkg, zip_bytes)
            if n < 1:
                raise RuntimeError("zip had no fndzlda/*.py files")
        write_commit(pkg, remote)
    except Exception as e:
        result = UpdateResult("failed", local=local, remote=remote, detail=str(e))
        _say(result, quiet)
        return result

    result = UpdateResult("updated", local=local, remote=remote)
    _say(result, quiet)
    if restart:
        (reexec or _reexec)(argv)
    return result


def _say(result: UpdateResult, quiet: bool) -> None:
    if quiet:
        return
    short = (result.remote or result.local or "")[:7]
    if result.action == "current":
        print(f"  hunter is current  {short}")
    elif result.action == "updated":
        print(f"  updated from GitHub  {short}. restarting.")
    elif result.action == "failed":
        print("  could not check for updates — using this copy")
