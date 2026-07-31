import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { runProcess } from "./process.js";

export interface OracleInstant {
  utc: string;
  local: string;
  wall: string;
  offsetMinutes: number;
  fold: number;
}

export interface OracleTransition {
  utc: string;
  type: "gap" | "fold";
  beforeOffsetMinutes: number;
  afterOffsetMinutes: number;
  localBefore: string;
  localAfter: string;
}

export interface OracleZone {
  name: string;
  classification: "dst-transition" | "fractional-offset" | "fixed-offset";
  reference: OracleInstant;
  windowStart: string;
  windowEnd: string;
  nextTransition: OracleTransition | null;
  cases: OracleInstant[];
}

export interface OracleMatrix {
  schemaVersion: 1;
  generatedAt: string;
  tzdataVersion: string;
  oracle: string;
  zones: OracleZone[];
  pairs: {
    opposingHemispheres: [string, string];
    dstAndNonDst: [string, string];
    fractionalOffsets: [string, string, string];
  };
  historicalCairo2023: OracleTransition[];
}

const repoRoot = resolve(fileURLToPath(new URL("../..", import.meta.url)));

export class TimezoneOracle {
  async matrix(): Promise<OracleMatrix> {
    const result = await runProcess(
      "uv",
      ["run", "--frozen", "caldiy-timezone-oracle", "matrix", "--json"],
      { cwd: repoRoot, env: { UV_CACHE_DIR: resolve(repoRoot, ".cache/uv") } }
    );
    const matrix = JSON.parse(result.stdout) as OracleMatrix;
    if (matrix.schemaVersion !== 1 || matrix.tzdataVersion !== "2026.3") {
      throw new Error("Timezone oracle did not use the pinned tzdata 2026.3 package");
    }
    return matrix;
  }

  async convert(zone: string, instants: string[]): Promise<OracleInstant[]> {
    const result = await runProcess(
      "uv",
      ["run", "--frozen", "caldiy-timezone-oracle", "convert", "--json"],
      {
        cwd: repoRoot,
        env: { UV_CACHE_DIR: resolve(repoRoot, ".cache/uv") },
        input: JSON.stringify({ zone, instants })
      }
    );
    const payload = JSON.parse(result.stdout) as { tzdataVersion: string; instants: OracleInstant[] };
    if (payload.tzdataVersion !== "2026.3") throw new Error("Timezone conversion used unexpected tzdata");
    return payload.instants;
  }

  async retain(matrix: OracleMatrix): Promise<void> {
    const output = resolve(repoRoot, "test-results/timezones/oracle.json");
    await mkdir(resolve(repoRoot, "test-results/timezones"), { recursive: true });
    await writeFile(output, `${JSON.stringify(matrix, null, 2)}\n`, "utf8");
  }
}
