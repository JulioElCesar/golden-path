# Golden Path Platform

The **Golden Path** is a shared engineering platform for 10+ independent full-cycle teams. It standardises the development lifecycle and ensures every team — regardless of stack — reports consistent, comparable DORA metrics.

The platform ships as two independently installable packages:

| Component | Language | Install |
|---|---|---|
| **Golden Path CLI** (`gp`) | Python | `uv tool install "git+https://github.com/JulioElCesar/golden-path#subdirectory=cli"` |
| **Workflow Framework** (`@golden-path/workflow-framework`) | TypeScript | `npm install github:JulioElCesar/golden-path` |

The [transactionify](https://github.com/JulioElCesar/transactionify) repository is the reference implementation showing both tools in production.

---

## Quick Start — CLI

Requires [uv](https://docs.astral.sh/uv/) ≥ 0.4.

```bash
# Install globally
uv tool install "git+https://github.com/JulioElCesar/golden-path#subdirectory=cli"

# Verify
gp --version
```

### Initialise a repository

```bash
cd your-service-repo
gp init
# Prompts for Work ID prefix (e.g. FIN), service name, reviewer count.
# Writes .gp-config.json and installs the pre-push hook.
```

### Create a compliant branch

```bash
gp branch FIN-42 feat add-payment-webhook
# Creates: feat/FIN-42-add-payment-webhook
```

**Allowed types:** `feat`, `fix`, `chore`, `refactor`, `test`, `docs`

### Validate conventions

```bash
gp check
# Checks branch name and last commit message against .gp-config.json rules.
# Exit 1 on violation — safe to run in CI (set GITHUB_HEAD_REF for PR context).
```

### Manage pre-push hooks

```bash
gp hooks install    # install the pre-push hook
gp hooks status     # check installation status
gp hooks uninstall  # remove the hook
```

The pre-push hook runs `gp check` then the `prePushCommands` listed in `.gp-config.json` before every `git push`.

---

## Quick Start — Workflow Framework

Requires Node.js ≥ 18 and npm/pnpm.

```bash
# npm
npm install github:JulioElCesar/golden-path

# pnpm
pnpm add github:JulioElCesar/golden-path
```

npm/pnpm will clone the repo, run `npm run build` (compiles TypeScript → `dist/`), and link the package. No separate build step needed.

### Use CDK constructs

```typescript
import { PlatformFunction, PlatformHttpGateway } from "@golden-path/workflow-framework";
import * as lambda from "aws-cdk-lib/aws-lambda";

// Opinionated Lambda wrapper — X-Ray, 256 MB, 30 s timeout, Python 3.12, log retention.
const fn = new PlatformFunction(this, "CreateAccount", {
  description: "Creates a new account for the authenticated user",
  handler: "myservice.handlers.account.create.main.handler",
  code: lambda.Code.fromAsset("src/python"),
  environment: { TABLE_NAME: table.tableName },
});

// HTTP API Gateway v2 with consistent naming and CORS defaults.
const gateway = new PlatformHttpGateway(this, "Gateway");
gateway.addRoute({ path: "/api/v1/accounts", method: HttpMethod.POST, handler: fn.lambda });
```

### Generate GitHub Actions workflows

```typescript
import { buildPrPipeline, buildIntegrationPipeline } from "@golden-path/workflow-framework";

const prWorkflow = buildPrPipeline({
  service: "my-service",
  workIdPrefix: "PLAT",
  defaultBranch: "main",
  pythonVersion: "3.12",
  nodeVersion: "20",
  awsRegion: "us-east-1",
});
```

Run `npm run generate-workflows` in any service that has the framework installed to regenerate `.github/workflows/` YAML. Commit the output — it is the source of truth for CI.

### Emit DORA telemetry

```typescript
import { DoraEmitter } from "@golden-path/workflow-framework";

const emitter = new DoraEmitter();
emitter.emit({
  eventType: "deployment_succeeded",
  service: "my-service",
  environment: "production",
  actor: "github-actions",
  sha: process.env.GITHUB_SHA,
  outcome: "success",
  durationMs: 45_000,
});
```

Events are written to `dora-events.jsonl`, uploaded as a GitHub Actions artifact, and optionally forwarded to CloudWatch Logs (`/golden-path/dora-events`).

---

## Repository Layout

```
golden-path/
├── src/                         # Framework TypeScript source
│   ├── constructs/              # PlatformFunction, PlatformHttpGateway (CDK L2)
│   ├── workflows/               # buildPrPipeline, buildIntegrationPipeline
│   └── dora/                    # DoraEmitter + event schema
├── test/                        # Framework Jest tests
│   ├── constructs/
│   └── workflows/
├── cli/                         # Python CLI (uv subdirectory install)
│   ├── pyproject.toml
│   └── src/gp/
│       ├── main.py
│       ├── commands/            # branch, check, hooks, init_
│       ├── manifest.py
│       ├── policy.py
│       ├── vcs.py
│       └── git_hooks.py
├── package.json                 # Framework package (@golden-path/workflow-framework)
├── tsconfig.json
├── ADR.md                       # Architecture decision record
├── CONTRIBUTING.md
└── .kiro/                       # Spec-Driven Development steering files
    ├── specs/
    └── steering/
```

---

## Convention Reference

### Branch naming
```
<type>/<WORK-ID>-<slug>

feat/FIN-42-add-payment-webhook
fix/FIN-7-correct-balance-rounding
```

### Commit messages
```
<type>: <WORK-ID> <description>

feat: FIN-42 Add payment webhook endpoint
fix(api): FIN-7 Correct balance rounding for EUR accounts
```

Work ID prefixes are defined per-repo in `.gp-config.json → workIdPrefix` (e.g. `FIN`, `PLAT`, `SRE`).

---

## Framework Development

```bash
# From the repo root (golden-path/)
npm install
npm run build    # compile TypeScript → dist/
npm test         # run Jest
npm run lint     # type-check without emit
```

## CLI Development

```bash
cd cli/
uv sync          # create venv and install deps
uv run pytest    # run tests
uv run gp --help # smoke test
```

---

## DORA Metrics

Every pipeline stage emits a structured event. The full schema lives in `src/dora/types.ts`.

| Metric | Derived from |
|---|---|
| Deployment Frequency | count of `deployment_succeeded` per day per environment |
| Lead Time for Changes | time from `pr_opened` → `deployment_succeeded` in production |
| Change Failure Rate | ratio of `deployment_failed` to total deployments |
| MTTR | time from `incident_opened` → `incident_resolved` |

Aggregate with AWS Athena, a CloudWatch Metric Filter, or any log analytics tool.

---

## GitHub Repository Setup

Configure these in **Settings → Secrets** and **Settings → Environments** before running pipelines:

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM access key with CDK deploy permissions |
| `AWS_SECRET_ACCESS_KEY` | IAM secret key |
| `AWS_REGION` | Deployment region (default `us-east-1`) |
| `AMAZON_Q_ROLE_ARN` | IAM role for Amazon Q Developer automated review |

**Environments to create:** `sandbox`, `staging`, `production`

Enable **Required reviewers** on the `production` environment to enforce the two-reviewer rule at the deployment gate.

---

## AWS Free Tier Compliance

All constructs default to Free Tier eligible services:

| Service | Usage | Free Tier |
|---|---|---|
| DynamoDB | `PAY_PER_REQUEST` | 25 GB storage, 200M requests/month |
| Lambda | Python 3.12 | 1M requests/month |
| API Gateway | HTTP API v2 | 1M calls/month (first 12 months) |
| CloudWatch Logs | Lambda + DORA events | 5 GB ingestion/month |
| X-Ray | Active tracing on all functions | 100k traces/month |
