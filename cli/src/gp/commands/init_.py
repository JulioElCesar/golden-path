from __future__ import annotations

import json
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

    _inject_npm_script(Path.cwd())
    _scaffold_generate_script(Path.cwd(), prefix.upper(), service)
    _scaffold_tsconfig(Path.cwd())

    console.print(
        Panel(
            f"[bold]Golden Path initialized[/bold]\n\n"
            f"  Work ID prefix  : [cyan]{prefix.upper()}[/cyan]\n"
            f"  Service         : [cyan]{service}[/cyan]\n"
            f"  Min reviewers   : [cyan]{reviewers}[/cyan]\n\n"
            f"  Branch pattern  : [dim]feat/{prefix.upper()}-123-my-feature[/dim]\n"
            f"  Commit pattern  : [dim]feat: {prefix.upper()}-123 Add my feature[/dim]\n\n"
            f"  Next step       : [yellow]npm install && npm run generate-workflows[/yellow]",
            title="[bold green]✓ Done",
            border_style="green",
        )
    )


GENERATE_WORKFLOWS_TEMPLATE = '''\
import {{ generateWorkflows }} from "@golden-path/workflow-framework";

generateWorkflows({{
  service: "{service}",
  workIdPrefix: "{prefix}",
  defaultBranch: "main",
  pythonVersion: "3.12",
  nodeVersion: "20",
  awsRegion: "us-east-1",
  requiredReviewers: 2,
}});
'''

TSCONFIG_TEMPLATE = '''\
{{
  "compilerOptions": {{
    "target": "ES2020",
    "module": "commonjs",
    "esModuleInterop": true,
    "strict": false,
    "skipLibCheck": true
  }}
}}
'''


_FRAMEWORK_PACKAGE = "github:JulioElCesar/golden-path"
_DEV_DEPS = {
    "ts-node": "^10.9.0",
    "typescript": "~5.3.0",
    "@types/node": "^20.0.0",
}


def _inject_npm_script(cwd: Path) -> None:
    """Inject generate-workflows script and required dependencies into package.json."""
    pkg = cwd / "package.json"
    if not pkg.exists():
        return

    data = json.loads(pkg.read_text(encoding="utf-8"))
    changed = False

    scripts = data.setdefault("scripts", {})
    if "generate-workflows" not in scripts:
        scripts["generate-workflows"] = "ts-node scripts/generate-workflows.ts"
        changed = True

    deps = data.setdefault("dependencies", {})
    if "@golden-path/workflow-framework" not in deps:
        deps["@golden-path/workflow-framework"] = _FRAMEWORK_PACKAGE
        changed = True

    pnpm_built = data.setdefault("pnpm", {}).setdefault("onlyBuiltDependencies", [])
    if "@golden-path/workflow-framework" not in pnpm_built:
        pnpm_built.append("@golden-path/workflow-framework")
        changed = True

    dev_deps = data.setdefault("devDependencies", {})
    for pkg_name, version in _DEV_DEPS.items():
        if pkg_name not in dev_deps:
            dev_deps[pkg_name] = version
            changed = True

    if changed:
        pkg.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        console.print("[green]✓[/green] Updated package.json (script + dependencies)")


def _scaffold_generate_script(cwd: Path, prefix: str, service: str) -> None:
    """Create scripts/generate-workflows.ts if it does not already exist."""
    target = cwd / "scripts" / "generate-workflows.ts"
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(GENERATE_WORKFLOWS_TEMPLATE.format(prefix=prefix, service=service), encoding="utf-8")
    console.print("[green]✓[/green] Created scripts/generate-workflows.ts")


def _scaffold_tsconfig(cwd: Path) -> None:
    """Create a minimal tsconfig.json if one does not exist."""
    target = cwd / "tsconfig.json"
    if target.exists():
        return
    target.write_text(TSCONFIG_TEMPLATE, encoding="utf-8")
    console.print("[green]✓[/green] Created tsconfig.json")
