/**
 * Type-safe subset of the GitHub Actions workflow schema.
 * Inspired by github-actions-workflow-ts — covers the constructs used by the Golden Path pipelines.
 */

export type Permission = "read" | "write" | "none";

export interface WorkflowTriggerFilter {
  readonly branches?: string[];
  readonly "branches-ignore"?: string[];
  readonly paths?: string[];
  readonly types?: string[];
}

export interface WorkflowDispatchInput {
  readonly description?: string;
  readonly required?: boolean;
  readonly default?: string;
  readonly type?: "string" | "choice" | "boolean" | "environment";
  readonly options?: string[];
}

export interface Step {
  readonly id?: string;
  readonly name?: string;
  readonly uses?: string;
  readonly run?: string;
  readonly with?: Record<string, string | number | boolean>;
  readonly env?: Record<string, string>;
  readonly if?: string;
  readonly "continue-on-error"?: boolean;
  readonly "timeout-minutes"?: number;
}

export interface Job {
  readonly name?: string;
  readonly "runs-on": string | string[];
  readonly needs?: string | string[];
  readonly if?: string;
  readonly env?: Record<string, string>;
  readonly steps: Step[];
  readonly outputs?: Record<string, string>;
  readonly permissions?: Record<string, Permission>;
  readonly environment?: string | { name: string; url?: string };
  readonly "timeout-minutes"?: number;
  readonly strategy?: {
    readonly matrix?: Record<string, unknown>;
    readonly "fail-fast"?: boolean;
  };
}

export interface Workflow {
  readonly name: string;
  readonly on: {
    readonly push?: WorkflowTriggerFilter;
    readonly pull_request?: WorkflowTriggerFilter;
    readonly workflow_dispatch?: { readonly inputs?: Record<string, WorkflowDispatchInput> };
    readonly schedule?: ReadonlyArray<{ readonly cron: string }>;
  };
  readonly env?: Record<string, string>;
  readonly permissions?: Record<string, Permission>;
  readonly jobs: Record<string, Job>;
}
