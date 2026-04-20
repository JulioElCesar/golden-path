import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import { Template } from "aws-cdk-lib/assertions";
import { PlatformFunction } from "../../src/constructs/platform-function";

function makeStack(stackName: string) {
  const app = new cdk.App();
  return new cdk.Stack(app, stackName, { stackName });
}

describe("PlatformFunction", () => {
  test("creates a Lambda function with the correct name", () => {
    const stack = makeStack("my-service-sandbox");
    new PlatformFunction(stack, "CreateAccount", {
      handler: "transactionify.handlers.create.handler",
      code: lambda.Code.fromInline("def handler(e,c): pass"),
    });

    const template = Template.fromStack(stack);
    template.hasResourceProperties("AWS::Lambda::Function", {
      FunctionName: "my-service-sandbox-create-account",
    });
  });

  test("applies mandatory platform tags", () => {
    const stack = makeStack("svc-sandbox");
    new PlatformFunction(stack, "MyHandler", {
      handler: "module.handler",
      code: lambda.Code.fromInline("def handler(e,c): pass"),
    });

    const template = Template.fromStack(stack);
    const functions = template.findResources("AWS::Lambda::Function");
    const fn = Object.values(functions)[0] as { Properties: { Tags?: Array<{ Key: string; Value: string }> } };
    const tags: Array<{ Key: string; Value: string }> = fn.Properties.Tags ?? [];
    const managedTag = tags.find((t) => t.Key === "golden-path:managed");
    expect(managedTag?.Value).toBe("true");
  });

  test("defaults to Python 3.12 runtime", () => {
    const stack = makeStack("svc-sandbox");
    new PlatformFunction(stack, "Fn", {
      handler: "module.handler",
      code: lambda.Code.fromInline("def handler(e,c): pass"),
    });
    Template.fromStack(stack).hasResourceProperties("AWS::Lambda::Function", {
      Runtime: "python3.12",
    });
  });

  test("accepts runtime override", () => {
    const stack = makeStack("svc-sandbox");
    new PlatformFunction(stack, "LegacyFn", {
      handler: "module.handler",
      code: lambda.Code.fromInline("def handler(e,c): pass"),
      runtime: lambda.Runtime.PYTHON_3_9,
    });
    Template.fromStack(stack).hasResourceProperties("AWS::Lambda::Function", {
      Runtime: "python3.9",
    });
  });

  test("enables X-Ray tracing", () => {
    const stack = makeStack("svc-sandbox");
    new PlatformFunction(stack, "Fn", {
      handler: "module.handler",
      code: lambda.Code.fromInline("def handler(e,c): pass"),
    });
    Template.fromStack(stack).hasResourceProperties("AWS::Lambda::Function", {
      TracingConfig: { Mode: "Active" },
    });
  });

  test("exposes the underlying Lambda via .lambda property", () => {
    const stack = makeStack("svc-sandbox");
    const svc = new PlatformFunction(stack, "Fn", {
      handler: "module.handler",
      code: lambda.Code.fromInline("def handler(e,c): pass"),
    });
    expect(svc.lambda).toBeInstanceOf(lambda.Function);
  });
});
