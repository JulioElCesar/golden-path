from __future__ import annotations

import subprocess
import sys

import click
from rich.console import Console

from gp.manifest import RepoManifest
from gp.policy import BRANCH_TYPES, DeliveryPolicy

console = Console()


@click.command("branch")
@click.argument("work_id")
@click.argument("type_", metavar="TYPE", type=click.Choice(list(BRANCH_TYPES)))
@click.argument("slug")
@click.option("--dry-run", is_flag=True, help="Print the branch name without creating it")
def branch(work_id: str, type_: str, slug: str, dry_run: bool) -> None:
    """Create a convention-compliant branch.

    \b
    WORK_ID   Ticket reference, e.g. FIN-42
    TYPE      One of: feat, fix, chore, refactor, test, docs
    SLUG      Short kebab-case description, e.g. add-payment-endpoint
    """
    try:
        manifest = RepoManifest.load()
    except FileNotFoundError as exc:
        console.print(f"[red]✗[/red] {exc}")
        sys.exit(1)

    policy = DeliveryPolicy(manifest.work_id_prefix)

    if not policy.valid_work_id(work_id.upper()):
        console.print(
            f"[red]✗[/red] Invalid Work ID '{work_id}'. "
            f"Expected format: {manifest.work_id_prefix}-<N> (e.g. {manifest.work_id_prefix}-42)"
        )
        sys.exit(1)

    clean_slug = slug.lower().replace(" ", "-").replace("_", "-")
    branch_name = f"{type_}/{work_id.upper()}-{clean_slug}"

    errors = policy.validate_branch(branch_name)
    if errors:
        for err in errors:
            console.print(f"[red]✗[/red] {err}")
        sys.exit(1)

    if dry_run:
        console.print(f"[dim]Would create:[/dim] [cyan]{branch_name}[/cyan]")
        return

    try:
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        console.print(f"[green]✓[/green] Created and switched to [cyan]{branch_name}[/cyan]")
    except subprocess.CalledProcessError:
        console.print(f"[red]✗[/red] Failed to create branch '{branch_name}'")
        sys.exit(1)
