import click

from gp.commands import branch, check, hooks, init_


@click.group()
@click.version_option(package_name="golden-path-cli")
def cli() -> None:
    """Golden Path CLI — enforce engineering conventions across teams."""


cli.add_command(init_.init)
cli.add_command(check.check)
cli.add_command(branch.branch)
cli.add_command(hooks.hooks)
