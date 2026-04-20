import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as logs from "aws-cdk-lib/aws-logs";
import { Construct } from "constructs";

export interface PlatformFunctionProps {
  readonly description?: string;
  readonly handler: string;
  readonly code: lambda.Code;
  readonly runtime?: lambda.Runtime;
  readonly environment?: Record<string, string>;
  readonly memorySize?: number;
  readonly timeout?: cdk.Duration;
  readonly logRetention?: logs.RetentionDays;
  readonly logGroup?: logs.ILogGroup;
}

/**
 * Platform-managed Lambda function with opinionated defaults:
 * - Python 3.12 runtime (override via `runtime`)
 * - 256 MB memory, 30s timeout
 * - Active X-Ray tracing
 * - Log retention: 7 days (non-prod) / 30 days (prod stacks)
 * - Mandatory platform tagging for governance and FinOps
 *
 * The internal CDK construct ID is intentionally stable ("Fn") to prevent
 * CloudFormation resource replacement on logical ID changes.
 */
export class PlatformFunction extends Construct {
  readonly lambda: lambda.Function;

  constructor(scope: Construct, id: string, props: PlatformFunctionProps) {
    super(scope, id);

    const stackName = cdk.Stack.of(this).stackName;
    const fnSlug = id
      .replace(/([A-Z])/g, (m) => `-${m.toLowerCase()}`)
      .replace(/^-/, "");
    const functionName = `${stackName}-${fnSlug}`;

    const logGroup =
      props.logGroup ??
      new logs.LogGroup(this, "LogGroup", {
        logGroupName: `/aws/lambda/${functionName}`,
        retention: props.logRetention ?? this.resolveLogRetention(stackName),
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      });

    this.lambda = new lambda.Function(this, "Fn", {
      functionName,
      description: props.description,
      runtime: props.runtime ?? lambda.Runtime.PYTHON_3_12,
      handler: props.handler,
      code: props.code,
      environment: props.environment ?? {},
      memorySize: props.memorySize ?? 256,
      timeout: props.timeout ?? cdk.Duration.seconds(30),
      logGroup,
      tracing: lambda.Tracing.ACTIVE,
    });

    cdk.Tags.of(this.lambda).add("golden-path:managed", "true");
    cdk.Tags.of(this.lambda).add("golden-path:version", "0.1.0");
  }

  private resolveLogRetention(stackName: string): logs.RetentionDays {
    if (stackName.endsWith("-prod") || stackName.endsWith("-production")) {
      return logs.RetentionDays.ONE_MONTH;
    }
    return logs.RetentionDays.ONE_WEEK;
  }
}
