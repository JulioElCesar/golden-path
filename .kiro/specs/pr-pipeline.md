# Spec: PR Pipeline

**Status:** Implemented  
**Owner:** Platform team  
**Related:** `src/workflows/pr-pipeline.ts`, `transactionify/.github/workflows/pr-pipeline.yml`

---

## Context

Every service repository that adopts the Golden Path gets a PR Pipeline. It runs on `pull_request` events and provides rapid feedback before code reaches `main`.

## Jobs

### 1. `validate-conventions`

**Trigger:** Always (first gate)  
**Purpose:** Enforce Work ID in branch name and commit message; enforce two-reviewer minimum.

**Steps:**
1. Checkout with full history (`fetch-depth: 0`)
2. Install Golden Path CLI via `uv`
3. Run `gp check` — validates branch name and HEAD commit against `.gp-config.json`
4. GitHub Script: assert `requested_reviewers.length >= 2`

**Failure behavior:** Blocks `small-tests` and `deploy-sandbox`. PR author sees inline errors from `gp check`.

### 2. `small-tests`

**Trigger:** After `validate-conventions` passes  
**Purpose:** Fast validation with no cloud dependency.

**Steps:**
1. Install test dependencies
2. `pytest test/unit/src/python -q` — full unit test suite
3. `schemathesis run openapi.yaml --dry-run` — schema validity check (non-blocking)
4. Emit DORA `pr_opened` event → `dora-events.jsonl`
5. Upload `dora-events.jsonl` as artifact

**Failure behavior:** Blocks `deploy-sandbox`.

### 3. `deploy-sandbox`

**Trigger:** After `small-tests` passes  
**Environment:** `sandbox` (GitHub environment with AWS credentials)  
**Purpose:** Validate the CDK stack synthesizes and deploys cleanly.

**Steps:**
1. `npm ci`
2. Configure AWS credentials from GitHub Secrets
3. `cdk synth TransactionifyStack-sandbox`
4. `cdk deploy TransactionifyStack-sandbox --require-approval never`
5. Emit DORA `deployment_succeeded` / `deployment_failed` event
6. Upload DORA artifact

**Failure behavior:** Fails the pipeline; PR blocked until fixed. CDK state is left in sandbox — the next deploy corrects it.

---

## DORA events emitted

| Stage | Event type | Condition |
|---|---|---|
| `small-tests` | `pr_opened` | Always (on completion) |
| `deploy-sandbox` | `deployment_succeeded` | Job succeeds |
| `deploy-sandbox` | `deployment_failed` | Job fails |

---

## Extending the pipeline

To add a new stage (e.g., integration tests against a running sandbox), edit `buildPrPipeline()` in `src/workflows/pr-pipeline.ts` and add a new `Job` with appropriate `needs`. Run `npm run generate-workflows` in the transactionify repo to propagate the change to YAML.

---

## Known limitations

- API contract validation (`schemathesis`) runs in `--dry-run` mode in the PR pipeline because there is no live endpoint to test against. Full contract testing runs in the Integration Pipeline against a deployed staging environment (future work).
- The Amazon Q PR Review runs as a separate workflow (`pr-review.yml`) to avoid blocking the pipeline on AI availability.
