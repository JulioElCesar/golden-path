# Contributing to the Golden Path Platform

This guide covers inner-source contributions to the CLI (`cli/`) and the Workflow Framework (root of this repo). The [transactionify](https://github.com/JulioElCesar/transactionify) repository is the reference client — changes there follow the same conventions but are scoped to `src/python/` and `lib/`.

---

## Who can contribute?

Anyone in the organisation. This is an inner-source project. The Platform team reviews and merges, but any team can propose changes.

---

## Before you start

1. Check the [Issues](../../issues) tab — someone may already be working on it.
2. For significant changes (new commands, new CDK constructs, new pipeline stages), open an issue first to agree on the design. This avoids wasted effort.
3. Small fixes and documentation improvements — just open a PR.

---

## Setup

### CLI (`cli/`)

```bash
cd cli/
uv sync
uv run pytest           # must pass before submitting
uv run ruff check src/  # must pass
```

### Framework (repo root)

```bash
npm install
npm test                # must pass before submitting
npm run lint            # must pass (tsc --noEmit)
```

---

## Conventions

All contributions must follow the Golden Path conventions enforced by the CLI itself.

### Branch naming
```
<type>/<WORK-ID>-<slug>

feat/FIN-42-add-branch-command
fix/PLAT-7-fix-config-lookup
```

### Commit messages
```
<type>: <WORK-ID> <description>

feat: FIN-42 Add gp branch command
```

**Types:** `feat`, `fix`, `chore`, `refactor`, `test`, `docs`

Install the pre-push hook to enforce these locally:
```bash
gp init     # or
gp hooks install
```

---

## Adding a new CLI command

1. Create `cli/src/gp/commands/your_command.py`
2. Register it in `cli/src/gp/main.py`
3. Add tests in `cli/tests/test_commands.py` (at minimum: happy path + one error case)
4. Document the command in `README.md` under **CLI Reference**

Commands must:
- Load config via `GpConfig.load()` — never hardcode prefixes or paths
- Exit with code 1 on error, 0 on success
- Use `rich.Console` for all output (no raw `print()`)

---

## Adding a new CDK construct

1. Create `src/constructs/your-construct.ts`
2. Export it from `src/constructs/index.ts`
3. Add tests in `test/constructs/your-construct.test.ts`
4. Document usage in `README.md`

Construct guidelines:
- Extend `Construct`, not `Stack`
- All required props must be `readonly`
- Apply `golden-path:managed: true` tag to all created resources
- Avoid CloudFormation intrinsic functions in prop defaults — keep them deterministic

---

## Adding a new language runtime

The framework is intentionally polyglot. To add support for a new runtime (e.g., Go, Clojure):

1. Open an issue tagged `new-language` with the runtime name and target Lambda runtime ARN
2. Add a new runtime preset in `src/constructs/platform-function.ts`:
   ```typescript
   // Example: add Go support
   export const RUNTIMES = {
     python312: lambda.Runtime.PYTHON_3_12,
     go122: lambda.Runtime.PROVIDED_AL2023,   // Go with custom runtime
     nodejs20: lambda.Runtime.NODEJS_20_X,
   };
   ```
3. Update the CLI `prePushCommands` documentation to cover the new runtime's test runner
4. Add a language-specific example to `README.md`

---

## Adding a new pipeline stage

Pipeline stages live in `src/workflows/`. To add a stage:

1. Define the `Job` object in the relevant pipeline function (`buildPrPipeline` or `buildIntegrationPipeline`)
2. Add it to the `jobs` record with a correct `needs` dependency
3. Add a test in `test/workflows/` asserting the new job exists and has the right `needs`
4. Run `npm run generate-workflows` in transactionify to regenerate the YAML
5. Commit both the TypeScript change and the generated YAML

---

## Pull Request requirements

- Two reviewers minimum (enforced by the pipeline)
- All CI checks green (conventions, tests, CDK synth)
- CHANGELOG entry not required for small fixes, but appreciated for new features

---

## Release process (Platform team only)

Releases are tagged on `main` following semver (`v0.1.0`, `v0.2.0`, etc.).

```bash
# Bump version in cli/pyproject.toml and package.json
git tag v0.2.0
git push origin v0.2.0
```

Teams pin to a tag for stability:
```bash
# CLI
uv tool install "git+https://github.com/JulioElCesar/golden-path@v0.2.0#subdirectory=cli"

# Framework
npm install github:JulioElCesar/golden-path#v0.2.0
```

---

## Questions?

Open a discussion in the [Discussions](../../discussions) tab, or reach out in `#platform-devex` on Slack.
