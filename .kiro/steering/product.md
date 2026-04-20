# Product Steering — Golden Path Platform

## Mission

Provide a "Golden Path" that makes it easier for 10+ independent engineering teams to follow company conventions than to break them. Every team's work should be traceable, comparable, and auditable from a single platform.

## Users

- **Service engineers** — use the CLI daily for branch creation, convention checks, and hook management
- **Platform engineers** — maintain the CLI and Framework, review inner-source contributions
- **Engineering managers** — consume DORA metrics for reporting and continuous improvement

## Non-goals

- Replacing existing project management tooling (Jira, Linear)
- Enforcing code style beyond the Work ID convention (that's per-team linting)
- Providing a deployment dashboard (use existing observability tools)

## Key design principles

1. **Convention over configuration** — the defaults should work for 80% of teams without customization
2. **Fail fast, fail loudly** — a broken convention should fail at `git push`, not at PR review
3. **Polyglot by design** — the framework's CDK constructs and pipelines work regardless of Lambda runtime
4. **Audit trail as a side effect** — DORA events are emitted automatically; teams don't opt in

## Success metrics

- Convention violations caught pre-push (not post-merge)
- All DORA metrics derivable from pipeline artifact data alone
- New service onboarding completable in < 30 minutes with `gp init`
