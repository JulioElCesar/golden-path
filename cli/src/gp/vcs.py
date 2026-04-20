from __future__ import annotations

import os
import subprocess
from pathlib import Path


def current_branch() -> str:
    """Return the current branch, respecting CI environment overrides."""
    ci_branch = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GIT_BRANCH")
    if ci_branch:
        return ci_branch
    return _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])


def last_commit_message() -> str:
    # In a GitHub Actions PR context, HEAD is a synthetic merge commit.
    # GITHUB_HEAD_SHA is the actual tip of the PR branch.
    head_sha = os.environ.get("GITHUB_HEAD_SHA")
    if head_sha:
        return _run(["git", "log", "-1", "--format=%B", head_sha])
    return _run(["git", "log", "-1", "--format=%B"])


def repo_root() -> Path:
    return Path(_run(["git", "rev-parse", "--show-toplevel"]))


def _run(cmd: list[str]) -> str:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        cwd=Path.cwd(),
    )
    return result.stdout.strip()
