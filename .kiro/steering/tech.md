# Technical Steering — Golden Path Platform

## Stack

| Layer | Technology | Rationale |
|---|---|---|
| CLI | Python + Click + Rich | Broad developer familiarity; `uv` for fast distribution |
| Framework | TypeScript + CDK v2 | Type-safe infrastructure; CDK is the company IaC standard |
| CI/CD | GitHub Actions | Company standard; native integration with PRs |
| Local emulation | LocalStack | Zero-credential local testing for DynamoDB/Lambda |
| Package distribution | `uv` (CLI), `npm/pnpm` (framework) | Modern tooling; no PyPI/npm registry required |

## Architecture constraints

- **No external registries** — both packages are installed directly from `github:JulioElCesar/golden-path`
- **AWS Free Tier** — all CDK stacks use PAY_PER_REQUEST DynamoDB + Lambda; no NAT gateways or provisioned capacity
- **Framework compiled on install** — the `prepare` lifecycle script runs `tsc` automatically when the package is installed from Git
- **DORA events are append-only JSON Lines** — no database required; uploaded as GitHub Actions artifacts

## Critical file paths

| File | Purpose |
|---|---|
| `cli/pyproject.toml` | CLI package definition; `gp` entry point |
| `src/index.ts` | Framework public API |
| `src/constructs/platform-function.ts` | Core CDK construct |
| `src/workflows/pr-pipeline.ts` | PR pipeline generator |
| `transactionify/lib/transactionify-stack.ts` | Integration example (consumes framework) |
| `transactionify/scripts/generate-workflows.ts` | Generates `.github/workflows/` YAML from TypeScript |
| `transactionify/.gp-config.json` | Per-repo Golden Path configuration |

## Testing strategy

- **CLI** — pytest with Click's `CliRunner`; fixtures mock git and filesystem
- **Framework constructs** — CDK `Template.fromStack()` assertions
- **Framework workflows** — pure TypeScript unit tests (no CDK or AWS dependencies)
- **Integration** — `docker-compose.yml` runs Lambda tests against LocalStack
- **Contract** — `schemathesis` validates the OpenAPI spec in CI (dry-run in PR pipeline)

## Versioning

Both packages follow semver, starting at `0.1.0`. Teams pin to a Git tag:
```
# CLI
git+https://github.com/JulioElCesar/golden-path@v0.1.0#subdirectory=cli

# Framework
github:JulioElCesar/golden-path#v0.1.0
```
