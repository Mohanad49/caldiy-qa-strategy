import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

import { runProcess } from "./process.js";

export interface EventTypeFixture {
  id: number;
  slug: string;
  title: string;
  username: string;
  organizationSlug: string;
  bookingPath: string;
}

export interface FixtureManifest {
  schemaVersion: 1;
  runId: string;
  workerId: string;
  resources: {
    bookingUids: string[];
    eventTypeIds: number[];
    scheduleIds: number[];
    eventTypes?: EventTypeFixture[];
    schedules?: Array<{ id: number; timeZone: string }>;
  };
}

export interface FixtureOptions {
  timeZone?: string;
  startTime?: string;
  endTime?: string;
  lengthMinutes?: number;
}

const repoRoot = resolve(fileURLToPath(new URL("../..", import.meta.url)));

export class FixtureManager {
  private readonly manifests: FixtureManifest[] = [];

  constructor(private readonly identity: string) {}

  async create(options: FixtureOptions = {}): Promise<FixtureManifest> {
    const args = ["run", "--frozen", "caldiy-fixtures", "create", "--json"];
    if (options.timeZone !== undefined) args.push("--time-zone", options.timeZone);
    if (options.startTime !== undefined) args.push("--start-time", options.startTime);
    if (options.endTime !== undefined) args.push("--end-time", options.endTime);
    if (options.lengthMinutes !== undefined) args.push("--length-minutes", String(options.lengthMinutes));

    const result = await runProcess("uv", args, {
      cwd: repoRoot,
      env: {
        QA_RUN_ID: this.identity,
        UV_CACHE_DIR: resolve(repoRoot, ".cache/uv")
      }
    });
    const manifest = JSON.parse(result.stdout) as FixtureManifest;
    this.assertManifest(manifest);
    this.manifests.push(manifest);
    return manifest;
  }

  track(manifest: FixtureManifest): void {
    this.assertManifest(manifest);
    this.manifests.push(manifest);
  }

  trackBooking(manifest: FixtureManifest, uid: string): void {
    if (!uid) throw new Error("Cannot track an empty booking UID");
    if (!manifest.resources.bookingUids.includes(uid)) manifest.resources.bookingUids.push(uid);
  }

  async cleanup(): Promise<void> {
    const failures: Error[] = [];
    for (const manifest of this.manifests.reverse()) {
      try {
        await runProcess("uv", ["run", "--frozen", "caldiy-fixtures", "destroy", "--json"], {
          cwd: repoRoot,
          env: { UV_CACHE_DIR: resolve(repoRoot, ".cache/uv") },
          input: JSON.stringify(manifest)
        });
      } catch (error) {
        failures.push(error instanceof Error ? error : new Error(String(error)));
      }
    }
    if (failures.length > 0) {
      throw new AggregateError(failures, `Fixture cleanup failed for ${this.identity}`);
    }
  }

  static manifestForEventType(identity: string, eventTypeId: number): FixtureManifest {
    return {
      schemaVersion: 1,
      runId: identity,
      workerId: "playwright-ui",
      resources: {
        bookingUids: [],
        eventTypeIds: [eventTypeId],
        scheduleIds: []
      }
    };
  }

  private assertManifest(manifest: FixtureManifest): void {
    if (
      manifest.schemaVersion !== 1 ||
      !Array.isArray(manifest.resources?.bookingUids) ||
      !Array.isArray(manifest.resources?.eventTypeIds) ||
      !Array.isArray(manifest.resources?.scheduleIds)
    ) {
      throw new Error("Python fixture CLI emitted an unsupported manifest");
    }
  }
}

export function firstEventType(manifest: FixtureManifest): EventTypeFixture {
  const eventType = manifest.resources.eventTypes?.[0];
  if (eventType === undefined) throw new Error("Fixture manifest has no event-type details");
  return eventType;
}
