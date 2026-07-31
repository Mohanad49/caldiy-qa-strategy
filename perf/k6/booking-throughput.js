import exec from "k6/execution";
import http from "k6/http";
import { Counter, Rate, Trend } from "k6/metrics";

import {
  apiUrl,
  bookingPayload,
  cancelBooking,
  getSlots,
  headers,
  runId,
  successData
} from "./common.js";

const bookingDuration = new Trend("booking_request_duration", true);
const bookingErrors = new Rate("booking_errors");
const cleanupErrors = new Counter("booking_cleanup_errors");

export const options = {
  scenarios: {
    booking_throughput: {
      executor: "shared-iterations",
      vus: 10,
      iterations: 50,
      maxDuration: "2m",
      gracefulStop: "5s"
    }
  },
  thresholds: {
    booking_errors: ["rate<0.01"],
    booking_cleanup_errors: ["count==0"]
  },
  summaryTrendStats: ["avg", "min", "med", "max", "p(90)", "p(95)", "p(99)"]
};

export function setup() {
  const slots = getSlots(14);
  if (slots.length < 50) {
    throw new Error(`booking throughput requires 50 unique slots; found ${slots.length}`);
  }
  return { slots: slots.slice(0, 50) };
}

export default function (data) {
  cleanupErrors.add(0);
  const index = exec.scenario.iterationInTest;
  const identity = `${runId}-booking-${index}`;
  const response = http.post(`${apiUrl}/v2/bookings`, bookingPayload(data.slots[index], identity), {
    headers: headers("2024-08-13"),
    tags: { operation: "booking-throughput" }
  });
  const booking = successData(response);
  const valid = response.status === 201 && typeof booking?.uid === "string";
  bookingDuration.add(response.timings.duration);
  bookingErrors.add(!valid);

  if (valid) {
    const cleanup = cancelBooking(booking.uid);
    cleanupErrors.add(cleanup.status !== 200);
  }
}
