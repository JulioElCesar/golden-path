from __future__ import annotations

from pathlib import Path

_MARKER = "# Golden Path managed hook"

_HOOK_TEMPLATE = """\
#!/usr/bin/env bash
# Golden Path managed hook — do not edit manually.
# Regenerate with: gp hooks install
set -euo pipefail

echo "→ Golden Path pre-push checks"

gp check || { echo "✗ Convention check failed. Run 'gp check' for details."; exit 1; }
gp hooks run pre-push || exit 1
"""


def install(repo_root: Path) -> Path:
    hook_path = _hook_path(repo_root)
    hook_path.write_text(_HOOK_TEMPLATE, encoding="utf-8")
    hook_path.chmod(0o755)
    return hook_path


def uninstall(repo_root: Path) -> bool:
    path = _hook_path(repo_root)
    if path.exists() and _MARKER in path.read_text(encoding="utf-8"):
        path.unlink()
        return True
    return False


def is_installed(repo_root: Path) -> bool:
    path = _hook_path(repo_root)
    return path.exists() and _MARKER in path.read_text(encoding="utf-8")


def _hook_path(repo_root: Path) -> Path:
    return repo_root / ".git" / "hooks" / "pre-push"
