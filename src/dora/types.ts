export type EventType =
  | "pr_opened"
  | "pr_merged"
  | "deployment_started"
  | "deployment_succeeded"
  | "deployment_failed"
  | "incident_opened"
  | "incident_resolved";

export type Environment = "sandbox" | "staging" | "production";

export type Outcome = "success" | "failure";

export interface DoraEvent {
  readonly version: "1.0";
  readonly eventType: EventType;
  readonly service: string;
  readonly workId?: string;
  readonly environment?: Environment;
  readonly actor: string;
  readonly sha?: string;
  readonly timestamp: string;
  readonly outcome?: Outcome;
  readonly durationMs?: number;
  readonly metadata?: Record<string, unknown>;
}
