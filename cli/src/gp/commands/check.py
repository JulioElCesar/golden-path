from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.table import Table

from gp.manifest import RepoManifest
from gp.policy import DeliveryPolicy
from gp.vcs import current_branch, last_commit_message

console = Console()


@click.command("check")
@click.option("--branch", "branch_override", default=None, help="Branch name to check (defaults to current)")
@click.option("--commit", "commit_override", default=None, help="Commit message to check (defaults to HEAD)")
def check(branch_override: str | None, commit_override: str | None) -> None:
    """Validate branch name and commit message against the delivery policy."""
    try:
        manifest = RepoManifest.load()
    except FileNotFoundError as exc:
        console.print(f"[red]✗[/red] {exc}")
        sys.exit(1)

    policy = DeliveryPolicy(manifest.work_id_prefix)

    branch_name = branch_override or current_branch()
    commit_msg = commit_override or last_commit_message()

    branch_errors = policy.validate_branch(branch_name)
    commit_errors = policy.validate_commit(commit_msg)

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("icon", style="bold", width=2)
    table.add_column("check", style="bold")
    table.add_column("value", style="dim")

    branch_ok = not branch_errors
    commit_ok = not commit_errors

    table.add_row(
        "[green]✓[/green]" if branch_ok else "[red]✗[/red]",
        "Branch name",
        branch_name,
    )
    table.add_row(
        "[green]✓[/green]" if commit_ok else "[red]✗[/red]",
        "Commit message",
        commit_msg.split("\n")[0][:72],
    )

    console.print(table)

    all_errors = branch_errors + commit_errors
    if all_errors:
        console.print()
        for error in all_errors:
            console.print(f"[red]✗[/red] {error}")
        sys.exit(1)

    work_id = policy.extract_work_id(branch_name)
    if work_id:
        console.print(f"\n[dim]Work ID:[/dim] [cyan]{work_id}[/cyan]")
