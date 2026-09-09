import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from fndzlda.update import (
    apply_zipball,
    check_and_apply,
    parse_remote_sha,
    repo_root,
    restart_argv,
    same_commit,
    write_commit,
)


def _zip_pkg(files: dict[str, str], sha: str = "abc1234deadbeef") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, body in files.items():
            zf.writestr(f"FndZlda-{sha}/fndzlda/{name}", body)
        zf.writestr("FndZlda-{sha}/README.md", "nope")
        zf.writestr(f"FndZlda-{sha}/fndzlda/__pycache__/x.pyc", "no")
    return buf.getvalue()


class TestUpdate(unittest.TestCase):
    def test_parse_remote_sha(self):
        sha = "a" * 40
        self.assertEqual(parse_remote_sha(json.dumps({"sha": sha})), sha)
        self.assertEqual(parse_remote_sha("not json"), "")
        self.assertEqual(parse_remote_sha(json.dumps({"sha": "nope"})), "")

    def test_same_commit_short_or_full(self):
        full = "b0045bdd1b8b2b034a5ce201ce688c346713c826"
        self.assertTrue(same_commit(full, full[:7]))
        self.assertTrue(same_commit(full[:12], full))
        self.assertFalse(same_commit("", full))
        self.assertFalse(same_commit(full, "ffffff0"))

    def test_zipball_writes_py_only(self):
        tmp = Path(tempfile.mkdtemp())
        pkg = tmp / "fndzlda"
        pkg.mkdir()
        (pkg / "old.py").write_text("old", encoding="utf-8")
        blob = _zip_pkg({"__init__.py": "__version__ = '1.0.1'\n", "hunter.py": "x = 1\n"})
        n = apply_zipball(pkg, blob)
        self.assertEqual(n, 2)
        self.assertEqual((pkg / "__init__.py").read_text(encoding="utf-8"), "__version__ = '1.0.1'\n")
        self.assertEqual((pkg / "old.py").read_text(encoding="utf-8"), "old")

    def test_restart_argv_breaks_update_loop(self):
        self.assertEqual(restart_argv(["--want", "both"])[0], "--no-update")
        self.assertEqual(restart_argv(["--no-update", "--once"]), ["--no-update", "--once"])

    def test_skip_when_disabled(self):
        r = check_and_apply(no_update=True, restart=False, quiet=True)
        self.assertEqual(r.action, "skip")

    def test_current_when_sha_matches(self):
        tmp = Path(tempfile.mkdtemp())
        pkg = tmp / "fndzlda"
        pkg.mkdir()
        sha = "c" * 40
        write_commit(pkg, sha)
        restarts = []

        def http_get(url: str):
            return json.dumps({"sha": sha}).encode()

        r = check_and_apply(
            package=pkg,
            http_get=http_get,
            restart=True,
            reexec=lambda argv: restarts.append(argv),
            quiet=True,
        )
        self.assertEqual(r.action, "current")
        self.assertEqual(restarts, [])

    def test_zipball_update_then_restart(self):
        tmp = Path(tempfile.mkdtemp())
        pkg = tmp / "fndzlda"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("__version__ = '0'\n", encoding="utf-8")
        sha = "d" * 40
        blob = _zip_pkg({"__init__.py": "__version__ = '2'\n"}, sha=sha)
        restarts = []

        def http_get(url: str):
            if "api.github.com" in url:
                return json.dumps({"sha": sha}).encode()
            return blob

        r = check_and_apply(
            package=pkg,
            http_get=http_get,
            restart=True,
            argv=["--want", "both"],
            reexec=lambda argv: restarts.append(list(argv or [])),
            quiet=True,
        )
        self.assertEqual(r.action, "updated")
        self.assertEqual(restarts, [["--want", "both"]])
        self.assertIn("2", (pkg / "__init__.py").read_text(encoding="utf-8"))
        self.assertTrue(same_commit((pkg / ".commit").read_text(encoding="utf-8"), sha))

    def test_git_pull_when_repo(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / ".git").mkdir()
        pkg = tmp / "fndzlda"
        pkg.mkdir()
        pulled = []
        sha = "e" * 40

        def http_get(url: str):
            return json.dumps({"sha": sha}).encode()

        def git_pull(root, remote):
            pulled.append((str(root), remote))

        r = check_and_apply(
            package=pkg,
            http_get=http_get,
            git_pull=git_pull,
            restart=False,
            quiet=True,
        )
        self.assertEqual(r.action, "updated")
        self.assertEqual(pulled, [(str(tmp.resolve()), sha)])

    def test_failed_check_does_not_raise(self):
        tmp = Path(tempfile.mkdtemp())
        pkg = tmp / "fndzlda"
        pkg.mkdir()

        def http_get(url: str):
            raise TimeoutError("nope")

        r = check_and_apply(package=pkg, http_get=http_get, restart=False, quiet=True)
        self.assertEqual(r.action, "failed")

    def test_repo_root_finds_git(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / ".git").mkdir()
        pkg = tmp / "fndzlda"
        pkg.mkdir()
        self.assertEqual(repo_root(pkg), tmp.resolve())
        other = Path(tempfile.mkdtemp()) / "fndzlda"
        other.mkdir(parents=True)
        self.assertIsNone(repo_root(other))
