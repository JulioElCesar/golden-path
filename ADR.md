# Architecture Decision Record — Golden Path Platform

**Version:** 0.1.0 | **Status:** Active | **Owner:** Platform / DevEx team

---

## 1. Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     github.com/JulioElCesar/golden-path              │
│                                                                     │
│   package.json  ──►  @golden-path/workflow-framework  (npm/pnpm)   │
│   cli/          ──►  golden-path-cli  (uv / Python)                │
└─────────────────────────────────────────────────────────────────────┘
             │                              │
       npm install                   uv tool install
    github:JulioElCesar/           git+https://...#subdirectory=cli
         golden-path
             │                              │
             ▼                              ▼
┌────────────────────────┐      ┌───────────────────────────────────┐
│  Service Repo (any)    │      │  Developer Workstation            │
│                        │      │                                   │
│  lib/stack.ts          │      │  gp init        → .gp-config.json │
│    PlatformFunction    │      │  gp branch      → git checkout -b │
│    PlatformHttpGateway │      │  gp check       → validates WORK ID│
│                        │      │  gp hooks       → pre-push hook   │
│  scripts/              │      └───────────────────────────────────┘
│   generate-workflows   │
│     buildPrPipeline()  │
│     buildIntegration() │
│         │              │
│         ▼              │
│  .github/workflows/    │      ┌───────────────────────────────────┐
│    pr-pipeline.yml     │─────►│  GitHub Actions                   │
│    integration.yml     │      │                                   │
│                        │      │  validate-conventions  (gp check) │
│  .gp-config.json       │      │  small-tests           (pytest)   │
│    workIdPrefix: "FIN" │      │  deploy-sandbox        (cdk)      │
│    prePushCommands:... │      │  deploy-staging        (cdk)      │
│                        │      │  deploy-production     (cdk + gate)│
└────────────────────────┘      │         │                         │
                                │         ▼                         │
                                │  DoraEmitter → dora-events.jsonl  │
                                │    → GitHub Actions Artifact      │
                                │    → CloudWatch /golden-path/dora │
                                └───────────────────────────────────┘
```

### Component Responsibilities

| Component | Language | Responsibility |
|---|---|---|
| **CLI (`gp`)** | Python + Click | Local developer loop: branch naming, commit validation, hook management, repo init |
| **Framework** | TypeScript + CDK v2 | CI/CD: type-safe pipeline generators, opinionated CDK constructs, DORA telemetry |
| **`.gp-config.json`** | JSON | Per-repo configuration: work ID prefix, service name, pre-push commands |
| **Generated YAML** | GitHub Actions | The committed source of truth for what runs in CI — regenerated via `npm run generate-workflows` |

### Key Design Decisions

**CLI in Python, Framework in TypeScript.** CDK is TypeScript, so the framework lives there — type-safe constructs and pipeline builders fit naturally. The CLI targets the developer terminal; Python's tooling (`uv`, `click`, `rich`) makes it faster to iterate on and easier to install across any OS without a Node dependency.

**Generated YAML, not dynamic YAML.** Pipelines are built from TypeScript, then the resulting YAML is committed. This means pipeline diffs are reviewable in PRs, the CI runner has zero dependency on the framework at runtime, and rolling back a pipeline change is a plain `git revert`.

**No registry dependency.** Both packages install directly from Git — `github:` for npm/pnpm, `#subdirectory=` for uv. Teams pin to a semver tag. No PyPI or npm publish step, no registry credentials to rotate.

---

## 2. Homologation — How 10+ Teams Adopt the Platform

### Bootstrap (Day 1 — ~30 minutes per team)

```bash
# 1. Install the CLI once per developer machine
uv tool install "git+https://github.com/JulioElCesar/golden-path#subdirectory=cli"

# 2. Initialise the service repo
gp init   # prompts: Work ID prefix, service name, reviewer count

# 3. Install the framework
npm install github:JulioElCesar/golden-path

# 4. Generate CI pipeline YAML
npm run generate-workflows   # writes .github/workflows/

# 5. Add AWS secrets + create sandbox/staging/prod environments in GitHub Settings
```

`.gp-config.json` is the join point between the CLI, the framework, and the generated workflows. Change the prefix there and everything — hooks, CI validation, DORA events — adapts automatically.

### Enforcement (Day 2 — no manual action)

| Layer | Mechanism | What it enforces |
|---|---|---|
| **Pre-push hook** | `gp hooks install` (installed by `gp init`) | Work ID in branch + commit before every push |
| **PR Pipeline** | Generated `validate-conventions` job | Same check in CI, blocks merge if violated |
| **PR Template** | `.github/PULL_REQUEST_TEMPLATE.md` | Work ID in PR title, test plan checklist, reviewer attestation |
| **CDK constructs** | `PlatformFunction`, `PlatformHttpGateway` | Consistent tagging, naming, and observability on all Lambda/APIGW resources |
| **DORA emitter** | `DoraEmitter` in every pipeline stage | Every team reports identical metric events |

### Incentive to adopt (not just mandate)

- `gp init` takes under a minute and eliminates the boilerplate of writing your own CI pipeline from scratch.
- Teams get sandbox deployments on every PR for free — no CDK expertise required.
- Non-compliant repos can't merge until they pass `gp check`.

---

## 3. Scalability — Avoiding the Platform Bottleneck

### Extension model

Teams extend pipelines without modifying the framework:

```json
// .gp-config.json
{
  "prePushCommands": [
    "cd src/go && go test ./...",
    "cd infra && cdk synth"
  ]
}
```

`gp hooks run pre-push` executes these commands in order before every push. Teams own their pre-push logic; the platform owns the hook contract.

For CI stages, teams pass typed escape hatches directly to the pipeline builder:

```typescript
buildPrPipeline({
  service: "payments",
  workIdPrefix: "PAY",
  extraSmallTestSteps: [
    { name: "Go tests", run: "cd src/go && go test ./..." },
  ],
  extraDeploySteps: [
    { name: "Smoke ping", run: "curl -f $API_URL/health" },
  ],
})
```

`extraSmallTestSteps` are injected after API contract validation, before the DORA event. `extraDeploySteps` are injected after CDK deploy, before the DORA event. Teams own their additions; the platform owns the contract around them.

### Inner-source model

For larger changes (new constructs, new pipeline stages), teams open a PR to the `golden-path` repo — the same workflow they already use. The Platform team reviews and merges. CODEOWNERS enforces that `src/constructs/` and `src/workflows/` always get Platform review; `cli/` changes can be reviewed by any two engineers.

This keeps the platform team as reviewers, not gatekeepers. Teams can self-serve 80% of changes.

### Versioning and rollback

Teams pin to a tag. An upgrade is a one-line change:

```bash
npm install github:JulioElCesar/golden-path#v0.2.0
```

A breaking change requires a major version bump with a migration guide in `CONTRIBUTING.md`. Teams migrate on their own schedule.

---

## 4. Shift-Left Strategy

The goal is to detect defects at the earliest, cheapest point in the delivery loop.

```
Commit  →  Push  →  PR  →  Sandbox  →  Staging  →  Production
  │          │        │        │            │
  │          │        │        │            └── Integration Pipeline
  │          │        │        └────────────── PR Pipeline: deploy-sandbox
  │          │        └─────────────────────── PR Pipeline: small-tests + validate-conventions
  │          └──────────────────────────────── pre-push hook: gp check + prePushCommands
  └─────────────────────────────────────────── IDE + commit-msg hook (future)
```

### Each gate and what it catches

| Gate | Cost | Catches |
|---|---|---|
| **Pre-push hook** | ~5 s | Work ID violations, test failures on the developer's own machine |
| **`validate-conventions`** (CI) | ~30 s | Same as hook, but also catches PRs opened without the hook installed |
| **`small-tests`** (CI) | ~3 min | Unit test regressions, OpenAPI contract drift, CDK synth errors |
| **`deploy-sandbox`** (CI) | ~8 min | CDK deploy failures, Lambda packaging errors, IAM permission issues |
| **`deploy-staging`** (Integration Pipeline) | ~10 min | Environment-specific config errors, smoke test failures against real infra |
| **`deploy-production`** (Integration Pipeline) | manual gate | Human review of staging behaviour; only after two approvers |

### Property-Based Testing

`small-tests` includes a placeholder for `hypothesis`-based PBT on the Python services. PBT generates edge-case inputs automatically — it finds boundary bugs (off-by-one amounts, null UUIDs, currency precision) that hand-written tests miss. This runs in ~2 minutes before any cloud resource is touched.

### API Contract Validation

`schemathesis run openapi.yaml --dry-run` validates that the OpenAPI spec is self-consistent on every PR. Full contract testing (against a live sandbox) runs in the Integration Pipeline after sandbox deploy.

### DORA as a feedback signal

MTTR (Time to Fix) is tracked from `deployment_failed` to the next successful `deployment_succeeded` in the same environment. Teams see this metric in GitHub Actions summaries on every run. A rising MTTR signals that the pipeline is catching real problems — or that the team needs to invest in test quality.
