import { buildPrPipeline } from "../../src/workflows/pr-pipeline";
import { buildIntegrationPipeline } from "../../src/workflows/integration-pipeline";

const baseConfig = {
  service: "transactionify",
  workIdPrefix: "FIN",
};

describe("buildPrPipeline", () => {
  test("returns a workflow with the expected name", () => {
    const wf = buildPrPipeline(baseConfig);
    expect(wf.name).toBe("PR Pipeline");
  });

  test("triggers on pull_request to main by default", () => {
    const wf = buildPrPipeline(baseConfig);
    expect(wf.on.pull_request?.branches).toContain("main");
  });

  test("respects custom defaultBranch", () => {
    const wf = buildPrPipeline({ ...baseConfig, defaultBranch: "master" });
    expect(wf.on.pull_request?.branches).toContain("master");
  });

  test("contains validate-conventions, small-tests, and deploy-sandbox jobs", () => {
    const wf = buildPrPipeline(baseConfig);
    expect(Object.keys(wf.jobs)).toEqual(
      expect.arrayContaining(["validate-conventions", "small-tests", "deploy-sandbox"]),
    );
  });

  test("validate-conventions runs before small-tests", () => {
    const wf = buildPrPipeline(baseConfig);
    const smallTests = wf.jobs["small-tests"];
    expect(smallTests.needs).toContain("validate-conventions");
  });

  test("deploy-sandbox depends on small-tests", () => {
    const wf = buildPrPipeline(baseConfig);
    const deploy = wf.jobs["deploy-sandbox"];
    expect(deploy.needs).toContain("small-tests");
  });

  test("deploy-sandbox targets sandbox environment", () => {
    const wf = buildPrPipeline(baseConfig);
    expect(wf.jobs["deploy-sandbox"].environment).toBe("sandbox");
  });

  test("exposes WORK_ID_PREFIX env var", () => {
    const wf = buildPrPipeline(baseConfig);
    expect(wf.env?.WORK_ID_PREFIX).toBe("FIN");
  });

  test("uses custom python version when provided", () => {
    const wf = buildPrPipeline({ ...baseConfig, pythonVersion: "3.11" });
    expect(wf.env?.PYTHON_VERSION).toBe("3.11");
  });

  test("injects extraSmallTestSteps before DORA emission", () => {
    const extra = { name: "Go tests", run: "cd src/go && go test ./..." };
    const wf = buildPrPipeline({ ...baseConfig, extraSmallTestSteps: [extra] });
    const steps = wf.jobs["small-tests"].steps;
    const extraIdx = steps.findIndex((s) => s.name === "Go tests");
    const doraIdx = steps.findIndex((s) => s.name === "Record DORA event");
    expect(extraIdx).toBeGreaterThan(-1);
    expect(extraIdx).toBeLessThan(doraIdx);
  });

  test("injects extraDeploySteps before DORA emission", () => {
    const extra = { name: "Smoke ping", run: "curl -f $API_URL/health" };
    const wf = buildPrPipeline({ ...baseConfig, extraDeploySteps: [extra] });
    const steps = wf.jobs["deploy-sandbox"].steps;
    const extraIdx = steps.findIndex((s) => s.name === "Smoke ping");
    const doraIdx = steps.findIndex((s) => s.name === "Record DORA event");
    expect(extraIdx).toBeGreaterThan(-1);
    expect(extraIdx).toBeLessThan(doraIdx);
  });

  test("omitting extra steps leaves job lengths unchanged", () => {
    const withExtras = buildPrPipeline({
      ...baseConfig,
      extraSmallTestSteps: [{ name: "X", run: "true" }],
      extraDeploySteps: [{ name: "Y", run: "true" }],
    });
    const without = buildPrPipeline(baseConfig);
    expect(withExtras.jobs["small-tests"].steps.length).toBe(
      without.jobs["small-tests"].steps.length + 1,
    );
    expect(withExtras.jobs["deploy-sandbox"].steps.length).toBe(
      without.jobs["deploy-sandbox"].steps.length + 1,
    );
  });
});

describe("buildIntegrationPipeline", () => {
  test("triggers on push to main", () => {
    const wf = buildIntegrationPipeline(baseConfig);
    expect(wf.on.push?.branches).toContain("main");
  });

  test("contains smoke-tests, deploy-staging, and deploy-production jobs", () => {
    const wf = buildIntegrationPipeline(baseConfig);
    expect(Object.keys(wf.jobs)).toEqual(
      expect.arrayContaining(["smoke-tests", "deploy-staging", "deploy-production"]),
    );
  });

  test("production deploy depends on staging", () => {
    const wf = buildIntegrationPipeline(baseConfig);
    const prod = wf.jobs["deploy-production"];
    expect(prod.needs).toContain("deploy-staging");
  });
});
