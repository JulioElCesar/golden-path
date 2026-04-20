import { appendFileSync } from "fs";
import type { DoraEvent, EventType, Environment, Outcome } from "./types";

export interface EmitOptions {
  readonly eventType: EventType;
  readonly service: string;
  readonly actor: string;
  readonly workId?: string;
  readonly environment?: Environment;
  readonly sha?: string;
  readonly outcome?: Outcome;
  readonly durationMs?: number;
  readonly metadata?: Record<string, unknown>;
}

export class DoraEmitter {
  private readonly outputPath: string;

  constructor(outputPath = "dora-events.jsonl") {
    this.outputPath = outputPath;
  }

  emit(options: EmitOptions): DoraEvent {
    const event: DoraEvent = {
      version: "1.0",
      timestamp: new Date().toISOString(),
      ...options,
    };

    appendFileSync(this.outputPath, JSON.stringify(event) + "\n");
    this.writeStepSummary(event);

    return event;
  }

  private writeStepSummary(event: DoraEvent): void {
    const summaryPath = process.env.GITHUB_STEP_SUMMARY;
    if (!summaryPath) return;

    const statusEmoji = event.outcome === "failure" ? "❌" : "✅";
    const summary = [
      `### ${statusEmoji} DORA — ${event.eventType}`,
      `| Field | Value |`,
      `|-------|-------|`,
      `| Service | \`${event.service}\` |`,
      event.workId ? `| Work ID | \`${event.workId}\` |` : null,
      event.environment ? `| Environment | \`${event.environment}\` |` : null,
      `| Actor | ${event.actor} |`,
      `| Outcome | ${event.outcome ?? "—"} |`,
      event.durationMs ? `| Duration | ${(event.durationMs / 1000).toFixed(1)}s |` : null,
    ]
      .filter(Boolean)
      .join("\n");

    appendFileSync(summaryPath, summary + "\n\n");
  }
}
