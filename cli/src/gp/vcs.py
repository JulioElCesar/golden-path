from __future__ import annotations

import os
import subprocess
from pathlib import Path


def current_branch() -> str:
    """Return the current branch, respecting CI environment overrides."""
    # GitHub Actions sets GITHUB_HEAD_REF for pull_request events
    ci_branch = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GIT_BRANCH")
    if ci_branch:
        return ci_branch
    return _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])


def last_commit_message() -> str:
    return _run(["git", "log", "-1", "--format=%B"])


def repo_root() -> Path:
    return Path(_run(["git", "rev-parse", "--show-toplevel"]))


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()
