import * as cdk from "aws-cdk-lib";
import * as apigwv2 from "aws-cdk-lib/aws-apigatewayv2";
import * as apigwv2_integrations from "aws-cdk-lib/aws-apigatewayv2-integrations";
import * as lambda from "aws-cdk-lib/aws-lambda";
import { Construct } from "constructs";

export interface RouteDefinition {
  readonly path: string;
  readonly method: apigwv2.HttpMethod;
  readonly handler: lambda.IFunction;
  readonly authorizer?: apigwv2.IHttpRouteAuthorizer;
}

/**
 * Platform-managed HTTP API Gateway with opinionated defaults:
 * - Consistent `{stackName}-api` naming
 * - CORS enabled with sane defaults for internal services
 * - CfnOutput for the API URL, exported as `{stackName}-api-url`
 */
export class PlatformHttpGateway extends Construct {
  readonly api: apigwv2.HttpApi;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    const stackName = cdk.Stack.of(this).stackName;

    this.api = new apigwv2.HttpApi(this, "Api", {
      apiName: `${stackName}-api`,
      createDefaultStage: true,
      corsPreflight: {
        allowMethods: [apigwv2.CorsHttpMethod.ANY],
        allowOrigins: ["*"],
        allowHeaders: ["Authorization", "Content-Type"],
      },
    });

    new cdk.CfnOutput(this, "ApiUrl", {
      value: this.api.apiEndpoint,
      description: "HTTP API Gateway endpoint URL",
      exportName: `${stackName}-api-url`,
    });
  }

  addRoute(route: RouteDefinition): void {
    const integrationId = `${route.method}${route.path.replace(/[^a-zA-Z0-9]/g, "")}`;
    this.api.addRoutes({
      path: route.path,
      methods: [route.method],
      integration: new apigwv2_integrations.HttpLambdaIntegration(
        `${integrationId}Integration`,
        route.handler,
      ),
      authorizer: route.authorizer,
    });
  }
}
