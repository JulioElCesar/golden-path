import type { Job, Step, Workflow } from "./types";

export interface IntegrationPipelineConfig {
  readonly service: string;
  readonly workIdPrefix: string;
  readonly defaultBranch?: string;
  readonly pythonVersion?: string;
  readonly nodeVersion?: string;
  readonly awsRegion?: string;
  readonly cdkBaseStackName?: string;
}

const checkout: Step = { uses: "actions/checkout@v4", with: { "fetch-depth": 0 } };

function setupPython(version: string): Step {
  return { uses: "actions/setup-python@v5", with: { "python-version": version, cache: "pip" } };
}

function setupNode(version: string): Step {
  return { uses: "actions/setup-node@v4", with: { "node-version": version, cache: "npm" } };
}

function cdkDeployJob(
  service: string,
  environment: "staging" | "production",
  stackSuffix: string,
  needs: string | string[],
  awsRegion: string,
  nodeVersion: string,
): Job {
  const stackName = `${service.replace(/-/g, "")}Stack-${stackSuffix}`;
  return {
    name: `Deploy → ${environment.charAt(0).toUpperCase() + environment.slice(1)}`,
    "runs-on": "ubuntu-latest",
    needs,
    environment,
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
        run: `npx cdk deploy ${stackName} --require-approval never --outputs-file cdk-outputs-${stackSuffix}.json`,
      },
      {
        name: "Record DORA deployment event",
        if: "always()",
        run: [
          `python3 -c "`,
          `import json,os`,
          `from datetime import datetime,timezone`,
          `e={`,
          `  'version':'1.0',`,
          `  'eventType':'deployment_succeeded' if os.environ.get('JOB_STATUS')=='success' else 'deployment_failed',`,
          `  'service':'${service}',`,
          `  'environment':'${environment}',`,
          `  'actor':os.environ.get('GITHUB_ACTOR','ci'),`,
          `  'sha':os.environ.get('GITHUB_SHA',''),`,
          `  'timestamp':datetime.now(timezone.utc).isoformat(),`,
          `  'outcome':'success' if os.environ.get('JOB_STATUS')=='success' else 'failure',`,
          `}`,
          `open('dora-events.jsonl','a').write(json.dumps(e)+'\\n')`,
          `"`,
        ].join("\n"),
        env: { JOB_STATUS: "${{ job.status }}" },
      },
      {
        name: "Upload DORA events",
        if: "always()",
        uses: "actions/upload-artifact@v4",
        with: {
          name: `dora-deploy-${stackSuffix}`,
          path: "dora-events.jsonl",
          "if-no-files-found": "ignore",
        },
      },
    ],
  };
}

export function buildIntegrationPipeline(config: IntegrationPipelineConfig): Workflow {
  const {
    service,
    workIdPrefix,
    defaultBranch = "main",
    pythonVersion = "3.12",
    nodeVersion = "20",
    awsRegion = "us-east-1",
  } = config;

  const smokeTests: Job = {
    name: "Smoke Tests",
    "runs-on": "ubuntu-latest",
    steps: [
      checkout,
      setupPython(pythonVersion),
      {
        name: "Install test dependencies",
        run: "pip install -r test/unit/src/python/requirements.txt",
      },
      {
        name: "Unit tests",
        run: "python -m pytest test/unit/src/python -q --tb=short",
      },
    ],
  };

  return {
    name: "Integration Pipeline",
    on: {
      push: { branches: [defaultBranch] },
    },
    permissions: { contents: "read" },
    env: {
      PYTHON_VERSION: pythonVersion,
      NODE_VERSION: nodeVersion,
      WORK_ID_PREFIX: workIdPrefix,
    },
    jobs: {
      "smoke-tests": smokeTests,
      "deploy-staging": cdkDeployJob(service, "staging", "staging", "smoke-tests", awsRegion, nodeVersion),
      "deploy-production": cdkDeployJob(service, "production", "prod", "deploy-staging", awsRegion, nodeVersion),
    },
  };
}
