import { dump } from "js-yaml";
import { mkdirSync, writeFileSync } from "fs";
import { join } from "path";
import { buildPrPipeline, type PrPipelineConfig } from "./pr-pipeline";
import { buildIntegrationPipeline } from "./integration-pipeline";

const HEADER = [
  "# ============================================================",
  "# AUTO-GENERATED — do not edit manually.",
  "# Regenerate with: npm run generate-workflows",
  "# ============================================================",
  "",
].join("\n");

/**
 * Generate pr-pipeline.yml and integration-pipeline.yml into outDir.
 * Defaults to <cwd>/.github/workflows.
 */
export function generateWorkflows(config: PrPipelineConfig, outDir?: string): void {
  const dir = outDir ?? join(process.cwd(), ".github", "workflows");
  mkdirSync(dir, { recursive: true });

  const write = (filename: string, workflow: object) => {
    writeFileSync(join(dir, filename), HEADER + dump(workflow, { lineWidth: 120, noRefs: true }));
    console.log(`✓ ${filename}`);
  };

  write("pr-pipeline.yml", buildPrPipeline(config));
  write("integration-pipeline.yml", buildIntegrationPipeline(config));
  console.log(`\nWorkflows generated in ${dir}`);
}
