# Golden Path Platform

The **Golden Path** is a shared engineering platform for 10+ independent full-cycle teams. It standardises how we work — branch naming, commit conventions, CI pipelines, AWS infrastructure, DORA metrics — so every team operates under the same rules and reports comparable data, regardless of their stack.

The platform ships as two independent, installable packages:

| Component | Language | Install via |
|---|---|---|
| **Golden Path CLI** (`gp`) | Python | `uv` (from Git) |
| **Workflow Framework** (`@golden-path/workflow-framework`) | TypeScript | `pnpm` or `npm` (from Git) |

The [transactionify](https://github.com/JulioElCesar/transactionify) repository is the reference implementation — it has the CLI configured, the framework installed, and the generated CI pipelines committed.

---

## Installing the CLI

Requires [uv](https://docs.astral.sh/uv/) ≥ 0.4.

```bash
uv tool install "git+https://github.com/JulioElCesar/golden-path#subdirectory=cli"

# Verify
gp --version
```

To pin to a specific release:

```bash
uv tool install "git+https://github.com/JulioElCesar/golden-path@v0.1.0#subdirectory=cli"
```

### Initialise a new service repo

```bash
cd your-service-repo
gp init
# Prompts: Work ID prefix (e.g. FIN), service name, reviewer count.
# Writes .gp-config.json and installs the pre-push hook.
```

### Create a branch

```bash
gp branch FIN-42 feat add-payment-webhook
# → feat/FIN-42-add-payment-webhook
```

Allowed types: `feat`, `fix`, `chore`, `refactor`, `test`, `docs`

### Validate conventions

```bash
gp check
# Checks branch name and last commit message against .gp-config.json.
# Exits 1 on any violation. Safe to run in CI (set GITHUB_HEAD_REF for PR context).
```

### Manage the pre-push hook

```bash
gp hooks install    # writes .git/hooks/pre-push
gp hooks status     # shows whether it's installed
gp hooks uninstall  # removes it
```

The hook runs `gp check` then any `prePushCommands` from `.gp-config.json` before every `git push`.

---

## Installing the Framework

Requires Node.js ≥ 18.

```bash
# pnpm
pnpm add github:JulioElCesar/golden-path

# npm
npm install github:JulioElCesar/golden-path
```

`npm`/`pnpm` runs `tsc` automatically on install via the `prepare` lifecycle script — no separate build step needed.

To pin to a release tag:

```bash
pnpm add github:JulioElCesar/golden-path#v0.1.0
```

---

## Onboarding a Service (End-to-End)

This is the full sequence for wiring a new service into the Golden Path. It takes about 30 minutes.

**1. Install the CLI globally** (once per developer machine)

```bash
uv tool install "git+https://github.com/JulioElCesar/golden-path#subdirectory=cli"
```

**2. Initialise the service repo**

```bash
cd your-service-repo
gp init   # answer the prompts; accept the defaults or customise
```

This writes `.gp-config.json` and installs the pre-push hook.

**3. Install the framework**

```bash
npm install github:JulioElCesar/golden-path
```

**4. Add a workflow generation script**

Create `scripts/generate-workflows.ts`:

```typescript
import { dump } from "js-yaml";
import { writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import { buildPrPipeline, buildIntegrationPipeline } from "@golden-path/workflow-framework";

const dir = join(__dirname, "..", ".github", "workflows");
mkdirSync(dir, { recursive: true });

const config = {
  service: "your-service",
  workIdPrefix: "YOUR",   // must match .gp-config.json
  gpCliRepo: "https://github.com/JulioElCesar/golden-path",
};

writeFileSync(join(dir, "pr-pipeline.yml"), dump(buildPrPipeline(config)));
writeFileSync(join(dir, "integration-pipeline.yml"), dump(buildIntegrationPipeline(config)));
```

Add to `package.json` scripts:
```json
"generate-workflows": "ts-node scripts/generate-workflows.ts"
```

**5. Generate and commit the workflow YAML**

```bash
npm run generate-workflows
git add .github/workflows/
git commit -m "chore: YOUR-1 Add Golden Path CI pipelines"
```

**6. Configure GitHub**

In your repo's **Settings → Environments**, create three environments: `sandbox`, `staging`, `production`.

In each environment's **Secrets**, add:

| Secret | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM access key with CDK deploy permissions |
| `AWS_SECRET_ACCESS_KEY` | IAM secret key |
| `AWS_REGION` | `us-east-1` (or your region) |

Optional: add `AMAZON_Q_ROLE_ARN` to enable the AI PR review workflow.

Enable **Required reviewers** on the `production` environment to enforce the two-reviewer gate at deploy time.

**7. Bootstrap CDK** (once per AWS account/region)

```bash
npx cdk bootstrap aws://YOUR_ACCOUNT_ID/us-east-1
```

That's it. Open a PR and the pipeline runs automatically.

---

## Using CDK Constructs

```typescript
import { PlatformFunction, PlatformHttpGateway } from "@golden-path/workflow-framework";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as apigwv2 from "aws-cdk-lib/aws-apigatewayv2";

// Lambda with opinionated defaults: X-Ray tracing, 256 MB, 30 s timeout,
// Python 3.12, log retention tied to environment (7 days non-prod, 30 days prod).
const fn = new PlatformFunction(this, "CreateAccount", {
  description: "Creates a new account for the authenticated user",
  handler: "myservice.handlers.account.create.main.handler",
  code: lambda.Code.fromAsset("src/python"),
  environment: { TABLE_NAME: table.tableName },
});

// HTTP API Gateway v2 with consistent naming and CORS defaults.
const gateway = new PlatformHttpGateway(this, "Gateway");
gateway.addRoute({
  path: "/api/v1/accounts",
  method: apigwv2.HttpMethod.POST,
  handler: fn.lambda,
  authorizer,
});
```

---

## Extending Pipelines Without Forking

Teams can inject custom steps into the standard pipeline stages:

```typescript
buildPrPipeline({
  service: "payments",
  workIdPrefix: "PAY",
  gpCliRepo: "https://github.com/JulioElCesar/golden-path",

  // Runs after API contract validation, before DORA emission.
  extraSmallTestSteps: [
    { name: "Go unit tests", run: "cd src/go && go test ./..." },
  ],

  // Runs after CDK deploy, before DORA emission.
  extraDeploySteps: [
    { name: "Health check", run: "curl -f $API_URL/health" },
  ],
})
```

For larger additions — new constructs, new pipeline stages — open a PR to `golden-path` following the process in [CONTRIBUTING.md](./CONTRIBUTING.md).

---

## Emitting DORA Telemetry

Every pipeline stage emits structured events automatically. You can also emit from application code:

```typescript
import { DoraEmitter } from "@golden-path/workflow-framework";

const emitter = new DoraEmitter();
emitter.emit({
  eventType: "deployment_succeeded",
  service: "my-service",
  environment: "production",
  actor: process.env.GITHUB_ACTOR ?? "ci",
  sha: process.env.GITHUB_SHA,
  outcome: "success",
  durationMs: 45_000,
});
```

Events are written to `dora-events.jsonl` (JSONL format) and uploaded as GitHub Actions artifacts. The full schema is in [`src/dora/types.ts`](./src/dora/types.ts).

| DORA Metric | Derived from |
|---|---|
| Deployment Frequency | count of `deployment_succeeded` per day per environment |
| Lead Time for Changes | time from first `pr_opened` to `deployment_succeeded` in production |
| Change Failure Rate | ratio of `deployment_failed` to total deployments |
| MTTR | time from `incident_opened` to `incident_resolved` |

Aggregate with AWS Athena, a CloudWatch Metric Filter, or any tool that can query JSONL.

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
<type>[(<scope>)]: <WORK-ID> <description>

feat: FIN-42 Add payment webhook endpoint
fix(api): FIN-7 Correct balance rounding for EUR accounts
```

Valid types: `feat`, `fix`, `chore`, `refactor`, `test`, `docs`

The Work ID prefix (e.g. `FIN`, `PLAT`, `SRE`) is defined per-repo in `.gp-config.json → workIdPrefix`.

---

## Repo Layout

```
golden-path/
├── src/                         # Framework TypeScript source
│   ├── constructs/              # PlatformFunction, PlatformHttpGateway
│   ├── workflows/               # buildPrPipeline, buildIntegrationPipeline
│   └── dora/                    # DoraEmitter + event schema
├── test/                        # Framework Jest tests
├── cli/                         # Python CLI (gp)
│   ├── pyproject.toml
│   └── src/gp/
│       ├── commands/            # branch, check, hooks, init
│       ├── manifest.py          # .gp-config.json reader/writer
│       ├── policy.py            # convention enforcement
│       └── git_hooks.py         # pre-push hook installer
├── CODEOWNERS
├── package.json
├── tsconfig.json
├── ADR.md
└── CONTRIBUTING.md
```

---

## Local Development

### Framework

```bash
npm install
npm run build    # compile TypeScript → dist/
npm test         # Jest
npm run lint     # tsc --noEmit (type-check only)
```

### CLI

```bash
cd cli/
uv sync
uv run pytest -v
uv run gp --help
```

---

## AWS Free Tier

All constructs default to Free Tier eligible services:

| Service | Configuration | Free Tier |
|---|---|---|
| Lambda | Python 3.12, 256 MB | 1M requests/month |
| DynamoDB | `PAY_PER_REQUEST` | 25 GB + 200M requests/month |
| API Gateway | HTTP API v2 | 1M calls/month (first 12 months) |
| CloudWatch Logs | Lambda + DORA events | 5 GB ingestion/month |
| X-Ray | Active tracing | 100K traces/month |
