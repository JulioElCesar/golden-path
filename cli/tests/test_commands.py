"""Integration tests for CLI commands using Click's test runner."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from gp.main import cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestCheckCommand:
    def test_valid_branch_and_commit(self, runner: CliRunner, tmp_repo: Path) -> None:
        with runner.isolated_filesystem(temp_dir=tmp_repo):
            result = runner.invoke(
                cli,
                ["check", "--branch", "feat/FIN-42-add-payments", "--commit", "feat: FIN-42 Add payments"],
            )
        assert result.exit_code == 0, result.output

    def test_invalid_branch_exits_nonzero(self, runner: CliRunner, tmp_repo: Path) -> None:
        with runner.isolated_filesystem(temp_dir=tmp_repo):
            result = runner.invoke(
                cli,
                ["check", "--branch", "add-payments", "--commit", "feat: FIN-42 Add payments"],
            )
        assert result.exit_code != 0
        assert "convention" in result.output.lower()

    def test_invalid_commit_exits_nonzero(self, runner: CliRunner, tmp_repo: Path) -> None:
        with runner.isolated_filesystem(temp_dir=tmp_repo):
            result = runner.invoke(
                cli,
                ["check", "--branch", "feat/FIN-42-add-payments", "--commit", "add payments"],
            )
        assert result.exit_code != 0

    def test_missing_manifest_exits_nonzero(self, runner: CliRunner, tmp_path: Path) -> None:
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["check", "--branch", "feat/FIN-1-x", "--commit", "feat: FIN-1 X"])
        assert result.exit_code != 0
        assert "gp init" in result.output


class TestBranchCommand:
    def test_dry_run_prints_branch_name(self, runner: CliRunner, tmp_repo: Path) -> None:
        with runner.isolated_filesystem(temp_dir=tmp_repo):
            result = runner.invoke(cli, ["branch", "FIN-42", "feat", "add-payments", "--dry-run"])
        assert result.exit_code == 0, result.output
        assert "feat/FIN-42-add-payments" in result.output

    def test_normalizes_work_id_to_uppercase(self, runner: CliRunner, tmp_repo: Path) -> None:
        with runner.isolated_filesystem(temp_dir=tmp_repo):
            result = runner.invoke(cli, ["branch", "fin-42", "feat", "add-payments", "--dry-run"])
        assert result.exit_code == 0
        assert "FIN-42" in result.output

    def test_invalid_work_id_prefix_exits_nonzero(self, runner: CliRunner, tmp_repo: Path) -> None:
        with runner.isolated_filesystem(temp_dir=tmp_repo):
            result = runner.invoke(cli, ["branch", "ABC-42", "feat", "add-payments", "--dry-run"])
        assert result.exit_code != 0

    def test_slug_normalizes_spaces_to_hyphens(self, runner: CliRunner, tmp_repo: Path) -> None:
        with runner.isolated_filesystem(temp_dir=tmp_repo):
            result = runner.invoke(cli, ["branch", "FIN-10", "fix", "correct balance rounding", "--dry-run"])
        assert result.exit_code == 0
        assert "correct-balance-rounding" in result.output


class TestHooksCommands:
    def test_install_creates_hook_file(self, runner: CliRunner, tmp_repo: Path) -> None:
        with patch("gp.commands.hooks.repo_root", return_value=tmp_repo):
            result = runner.invoke(cli, ["hooks", "install"])
        assert result.exit_code == 0, result.output
        hook = tmp_repo / ".git" / "hooks" / "pre-push"
        assert hook.exists()
        assert "Golden Path" in hook.read_text()

    def test_uninstall_removes_hook(self, runner: CliRunner, tmp_repo: Path) -> None:
        from gp import git_hooks
        git_hooks.install(tmp_repo)

        with patch("gp.commands.hooks.repo_root", return_value=tmp_repo):
            result = runner.invoke(cli, ["hooks", "uninstall"])
        assert result.exit_code == 0
        assert not (tmp_repo / ".git" / "hooks" / "pre-push").exists()

    def test_status_shows_installed(self, runner: CliRunner, tmp_repo: Path) -> None:
        from gp import git_hooks
        git_hooks.install(tmp_repo)

        with patch("gp.commands.hooks.repo_root", return_value=tmp_repo):
            result = runner.invoke(cli, ["hooks", "status"])
        assert result.exit_code == 0
        assert "installed" in result.output.lower()
