from __future__ import annotations

import subprocess
import sys

import click
from rich.console import Console

from gp import git_hooks
from gp.manifest import RepoManifest
from gp.vcs import repo_root

console = Console()


@click.group("hooks")
def hooks() -> None:
    """Manage Golden Path git hooks."""


@hooks.command("install")
def install() -> None:
    """Install the pre-push hook into .git/hooks/."""
    try:
        root = repo_root()
    except subprocess.CalledProcessError:
        console.print("[red]✗[/red] Not inside a git repository.")
        sys.exit(1)

    hook_path = git_hooks.install(root)
    console.print(
        f"[green]✓[/green] Installed pre-push hook at "
        f"[cyan]{hook_path.relative_to(root)}[/cyan]"
    )


@hooks.command("uninstall")
def uninstall() -> None:
    """Remove the Golden Path pre-push hook."""
    try:
        root = repo_root()
    except subprocess.CalledProcessError:
        console.print("[red]✗[/red] Not inside a git repository.")
        sys.exit(1)

    if git_hooks.uninstall(root):
        console.print("[green]✓[/green] Removed pre-push hook.")
    else:
        console.print("[yellow]![/yellow] No Golden Path hook found to remove.")


@hooks.command("status")
def status() -> None:
    """Show whether the Golden Path pre-push hook is installed."""
    try:
        root = repo_root()
    except subprocess.CalledProcessError:
        console.print("[red]✗[/red] Not inside a git repository.")
        sys.exit(1)

    if git_hooks.is_installed(root):
        console.print("[green]✓[/green] Pre-push hook is installed.")
    else:
        console.print("[yellow]![/yellow] Pre-push hook is [bold]not[/bold] installed. Run 'gp hooks install'.")


@hooks.command("run")
@click.argument("hook_name", metavar="HOOK", type=click.Choice(["pre-push"]))
def run(hook_name: str) -> None:
    """Execute the configured commands for a hook (called by the hook script itself)."""
    try:
        manifest = RepoManifest.load()
    except FileNotFoundError as exc:
        console.print(f"[red]✗[/red] {exc}")
        sys.exit(1)

    if not manifest.pre_push_commands:
        console.print("[dim]No prePushCommands configured — skipping.[/dim]")
        return

    for cmd in manifest.pre_push_commands:
        console.print(f"[dim]→[/dim] {cmd}")
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            console.print(f"[red]✗[/red] Command failed: {cmd}")
            sys.exit(result.returncode)

    console.print("[green]✓[/green] All pre-push checks passed.")
