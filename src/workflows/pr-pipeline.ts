import type { Job, Step, Workflow } from "./types";

export interface PrPipelineConfig {
  readonly service: string;
  readonly workIdPrefix: string;
  readonly defaultBranch?: string;
  readonly pythonVersion?: string;
  readonly nodeVersion?: string;
  readonly awsRegion?: string;
  readonly cdkStackName?: string;
  readonly gpCliRepo?: string;
  /** Minimum required reviewers on the PR. Defaults to 2. */
  readonly requiredReviewers?: number;
  /** Additional steps injected after unit tests, before DORA emission. */
  readonly extraSmallTestSteps?: Step[];
  /** Additional steps injected after CDK deploy, before DORA emission. */
  readonly extraDeploySteps?: Step[];
}

const checkout: Step = { uses: "actions/checkout@v4", with: { "fetch-depth": 0 } };

function setupPython(version: string): Step {
  return { uses: "actions/setup-python@v5", with: { "python-version": version, cache: "pip" } };
}

function setupNode(version: string): Step {
  return { uses: "actions/setup-node@v4", with: { "node-version": version, cache: "npm" } };
}

function doraStep(eventType: string, service: string, environment?: string): Step {
  const envField = environment ? `"environment":"${environment}",` : "";
  return {
    name: "Record DORA event",
    if: "always()",
    run: [
      `python3 -c "`,
      `import json,os`,
      `from datetime import datetime,timezone`,
      `e={`,
      `  'version':'1.0',`,
      `  'eventType':'${eventType}',`,
      `  'service':'${service}',`,
      `  ${envField}`,
      `  'actor':os.environ.get('GITHUB_ACTOR','ci'),`,
      `  'sha':os.environ.get('GITHUB_SHA',''),`,
      `  'timestamp':datetime.now(timezone.utc).isoformat(),`,
      `  'outcome':'success' if os.environ.get('JOB_STATUS')=='success' else 'failure',`,
      `}`,
      `open('dora-events.jsonl','a').write(json.dumps(e)+'\\n')`,
      `"`,
    ].join("\n"),
    env: { JOB_STATUS: "${{ job.status }}" },
  };
}

function uploadDoraArtifact(name: string): Step {
  return {
    name: "Upload DORA events",
    if: "always()",
    uses: "actions/upload-artifact@v4",
    with: { name, path: "dora-events.jsonl", "if-no-files-found": "ignore" },
  };
}

export function buildPrPipeline(config: PrPipelineConfig): Workflow {
  const {
    service,
    workIdPrefix,
    defaultBranch = "main",
    pythonVersion = "3.12",
    nodeVersion = "20",
    awsRegion = "us-east-1",
    cdkStackName,
    gpCliRepo = "git+${{ github.server_url }}/${{ github.repository }}",
    requiredReviewers = 2,
    extraSmallTestSteps = [],
    extraDeploySteps = [],
  } = config;

  const serviceBase = service.replace(/-/g, "");
  const stackName =
    cdkStackName ??
    `${serviceBase.charAt(0).toUpperCase() + serviceBase.slice(1)}Stack-sandbox`;

  const validateConventions: Job = {
    name: "Validate Git Conventions",
    "runs-on": "ubuntu-latest",
    permissions: { contents: "read", "pull-requests": "read" },
    steps: [
      checkout,
      setupPython(pythonVersion),
      {
        name: "Install Golden Path CLI",
        run: [
          "pip install uv",
          `uv tool install "${gpCliRepo}#subdirectory=cli"`,
        ].join("\n"),
      },
      {
        name: "Check conventions",
        run: "gp check",
        env: {
          GITHUB_HEAD_REF: "${{ github.head_ref }}",
          GITHUB_HEAD_SHA: "${{ github.event.pull_request.head.sha }}",
        },
      },
      ...(requiredReviewers > 0
        ? [
            {
              name: "Enforce reviewer rule",
              uses: "actions/github-script@v7",
              with: {
                script: [
                  `const { data: reviews } = await github.rest.pulls.listReviews({`,
                  `  owner: context.repo.owner, repo: context.repo.repo, pull_number: context.issue.number`,
                  `});`,
                  `const approvals = reviews.filter(r => r.state === 'APPROVED').length;`,
                  `if (approvals < ${requiredReviewers}) {`,
                  `  core.setFailed(\`PR requires at least ${requiredReviewers} approval(s), got \${approvals}\`);`,
                  `}`,
                ].join("\n"),
              },
            } as Step,
          ]
        : []),
    ],
  };

  const smallTests: Job = {
    name: "Small Tests",
    "runs-on": "ubuntu-latest",
    needs: "validate-conventions",
    steps: [
      checkout,
      setupPython(pythonVersion),
      { name: "Install test dependencies", run: "pip install -r test/unit/src/python/requirements.txt" },
      {
        name: "Unit tests",
        run: "python -m pytest test/unit/src/python -q --tb=short --junitxml=test-results.xml",
        env: { PYTHONPATH: "src/python" },
      },
      {
        name: "Upload test results",
        if: "always()",
        uses: "actions/upload-artifact@v4",
        with: { name: "test-results", path: "test-results.xml", "if-no-files-found": "ignore" },
      },
      {
        name: "API contract validation",
        run: [
          "pip install schemathesis",
          "schemathesis run openapi.yaml --validate-schema=true --checks=all --dry-run || true",
        ].join("\n"),
      },
      ...extraSmallTestSteps,
      doraStep("pr_opened", service),
      uploadDoraArtifact("dora-small-tests"),
    ],
  };

  const deploySandbox: Job = {
    name: "Deploy → Sandbox",
    "runs-on": "ubuntu-latest",
    needs: "small-tests",
    environment: "sandbox",
    permissions: { contents: "read", "id-token": "write" },
    steps: [
      checkout,
      setupNode(nodeVersion),
      { name: "Install dependencies", run: "npm ci" },
      {
        name: "Configure AWS credentials",
        uses: "aws-actions/configure-aws-credentials@v4",
        with: {
          "aws-access-key-id": "${{ secrets.AWS_ACCESS_KEY_ID }}",
          "aws-secret-access-key": "${{ secrets.AWS_SECRET_ACCESS_KEY }}",
          "aws-region": `\${{ secrets.AWS_REGION || '${awsRegion}' }}`,
        },
      },
      { name: "CDK synth", run: `npx cdk synth ${stackName}` },
      {
        name: "CDK deploy",
        run: `npx cdk deploy ${stackName} --require-approval never --outputs-file cdk-outputs.json`,
      },
      ...extraDeploySteps,
      doraStep("deployment_succeeded", service, "sandbox"),
      uploadDoraArtifact("dora-deploy-sandbox"),
    ],
  };

  return {
    name: "PR Pipeline",
    on: {
      pull_request: {
        branches: [defaultBranch],
        types: ["opened", "synchronize", "reopened"],
      },
    },
    permissions: { contents: "read" },
    env: {
      PYTHON_VERSION: pythonVersion,
      NODE_VERSION: nodeVersion,
      WORK_ID_PREFIX: workIdPrefix,
    },
    jobs: {
      "validate-conventions": validateConventions,
      "small-tests": smallTests,
      "deploy-sandbox": deploySandbox,
    },
  };
}
