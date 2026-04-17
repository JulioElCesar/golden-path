from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from gp import git_hooks
from gp.manifest import MANIFEST_FILE, RepoManifest
from gp.vcs import repo_root

console = Console()


@click.command("init")
@click.option("--prefix", prompt="Work ID prefix (e.g. FIN)", help="Ticket prefix for your team")
@click.option(
    "--service",
    prompt="Service name",
    default=lambda: Path.cwd().name,
    show_default=False,
    help="Service identifier used in pipeline events",
)
@click.option("--reviewers", default=2, show_default=True, help="Minimum required reviewers")
@click.option("--no-hooks", is_flag=True, help="Skip installing git hooks")
def init(prefix: str, service: str, reviewers: int, no_hooks: bool) -> None:
    """Initialize Golden Path conventions for this repository."""
    config_path = Path.cwd() / MANIFEST_FILE

    if config_path.exists():
        click.confirm(f"{MANIFEST_FILE} already exists. Overwrite?", abort=True)

    manifest = RepoManifest(
        work_id_prefix=prefix.upper(),
        required_reviewers=reviewers,
        service=service,
        pre_push_commands=[],
    )
    manifest.write(config_path)
    console.print(f"[green]✓[/green] Created {MANIFEST_FILE}")

    if not no_hooks:
        try:
            root = repo_root()
            hook = git_hooks.install(root)
            console.print(f"[green]✓[/green] Installed pre-push hook at {hook.relative_to(root)}")
        except Exception as exc:
            console.print(f"[yellow]![/yellow] Could not install git hook: {exc}")

    console.print(
        Panel(
            f"[bold]Golden Path initialized[/bold]\n\n"
            f"  Work ID prefix  : [cyan]{prefix.upper()}[/cyan]\n"
            f"  Service         : [cyan]{service}[/cyan]\n"
            f"  Min reviewers   : [cyan]{reviewers}[/cyan]\n\n"
            f"  Branch pattern  : [dim]feat/{prefix.upper()}-123-my-feature[/dim]\n"
            f"  Commit pattern  : [dim]feat: {prefix.upper()}-123 Add my feature[/dim]",
            title="[bold green]✓ Done",
            border_style="green",
        )
    )
