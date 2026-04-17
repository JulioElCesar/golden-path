import json
from pathlib import Path

import pytest

from gp.manifest import MANIFEST_FILE, RepoManifest


def test_load_manifest(tmp_repo: Path) -> None:
    manifest = RepoManifest.load(tmp_repo)
    assert manifest.work_id_prefix == "FIN"
    assert manifest.required_reviewers == 2
    assert manifest.service == "test-service"


def test_load_walks_up_to_find_manifest(tmp_repo: Path) -> None:
    nested = tmp_repo / "src" / "deep" / "dir"
    nested.mkdir(parents=True)
    manifest = RepoManifest.load(nested)
    assert manifest.work_id_prefix == "FIN"


def test_load_raises_when_manifest_absent(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match=MANIFEST_FILE):
        RepoManifest.load(tmp_path)


def test_write_roundtrip(tmp_path: Path) -> None:
    manifest = RepoManifest(
        work_id_prefix="PLAT",
        required_reviewers=3,
        service="platform-svc",
        pre_push_commands=["pytest -q"],
    )
    path = tmp_path / MANIFEST_FILE
    manifest.write(path)

    loaded = RepoManifest.load(tmp_path)
    assert loaded.work_id_prefix == "PLAT"
    assert loaded.required_reviewers == 3
    assert loaded.service == "platform-svc"
    assert loaded.pre_push_commands == ["pytest -q"]


def test_write_produces_valid_json(tmp_path: Path) -> None:
    manifest = RepoManifest(work_id_prefix="SRE", required_reviewers=2, service="sre-svc")
    path = tmp_path / MANIFEST_FILE
    manifest.write(path)
    data = json.loads(path.read_text())
    assert data["workIdPrefix"] == "SRE"
