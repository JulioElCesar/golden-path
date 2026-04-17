import json
from pathlib import Path

import pytest


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """A temporary directory that looks like a git repo with a .gp-config.json."""
    (tmp_path / ".git" / "hooks").mkdir(parents=True)
    config = {
        "workIdPrefix": "FIN",
        "requiredReviewers": 2,
        "service": "test-service",
        "prePushCommands": [],
    }
    (tmp_path / ".gp-config.json").write_text(json.dumps(config))
    return tmp_path
