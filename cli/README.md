# Golden Path CLI (`gp`)

Developer-facing CLI for the Golden Path platform. Enforces engineering conventions and manages the local development workflow.

## Install

Requires [uv](https://docs.astral.sh/uv/) ≥ 0.4.

```bash
uv tool install "git+https://github.com/JulioElCesar/golden-path#subdirectory=cli"
gp --version
```

## Commands

| Command | Description |
|---|---|
| `gp init` | Initialise a repo — writes `.gp-config.json` and installs the pre-push hook |
| `gp check` | Validate branch name and last commit message against Work ID conventions |
| `gp branch <WORK-ID> <type> <slug>` | Create a convention-compliant branch |
| `gp hooks install \| uninstall \| status` | Manage the pre-push git hook |
| `gp hooks run pre-push` | Run the `prePushCommands` from `.gp-config.json` |

See the [platform README](../README.md) for full usage details.
