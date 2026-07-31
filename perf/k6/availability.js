import exec from "k6/execution";
import http from "k6/http";
import { Rate, Trend } from "k6/metrics";

import { headers, slotsUrl } from "./common.js";

const baselineMode = __ENV.PERF_BASELINE_MODE === "1";
const thresholdMs = Number(__ENV.PERF_AVAILABILITY_P95_MS || "60000");

if (!Number.isFinite(thresholdMs) || thresholdMs <= 0) {
  throw new Error("PERF_AVAILABILITY_P95_MS must be a positive number");
}

const availabilityDuration = new Trend("availability_request_duration", true);
const availabilityErrors = new Rate("availability_errors");

const thresholds = {
  availability_errors: ["rate<0.01"]
};
if (!baselineMode) {
  thresholds.availability_request_duration = [`p(95)<${thresholdMs}`];
}

export const options = {
  scenarios: {
    warmup: {
      executor: "constant-vus",
      exec: "warmup",
      vus: 2,
      duration: "10s",
      gracefulStop: "0s"
    },
    availability: {
      executor: "constant-vus",
      exec: "measureAvailability",
      vus: 20,
      duration: "60s",
      startTime: "10s",
      gracefulStop: "5s"
    }
  },
  thresholds,
  summaryTrendStats: ["avg", "min", "med", "max", "p(90)", "p(95)", "p(99)"]
};

export function warmup() {
  http.get(slotsUrl(), {
    headers: headers("2024-09-04"),
    tags: { operation: "availability-warmup" }
  });
}

export function measureAvailability() {
  const response = http.get(slotsUrl(), {
    headers: headers("2024-09-04"),
    tags: { operation: "availability-measured", scenario: exec.scenario.name }
  });
  const valid = response.status === 200 && response.json("status") === "success";
  availabilityDuration.add(response.timings.duration);
  availabilityErrors.add(!valid);
}
