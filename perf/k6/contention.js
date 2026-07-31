import exec from "k6/execution";
import http from "k6/http";
import { Counter, Gauge, Trend } from "k6/metrics";
import { sleep } from "k6";

import {
  apiUrl,
  bookingPayload,
  cancelBooking,
  eventTypeId,
  getSlots,
  headers,
  runId,
  successData
} from "./common.js";

const successes = new Counter("contention_successes");
const conflicts = new Counter("contention_conflicts");
const unexpected = new Counter("contention_unexpected_responses");
const persisted = new Gauge("contention_persisted_bookings");
const persistenceErrors = new Counter("contention_persistence_errors");
const cleanupErrors = new Counter("contention_cleanup_errors");
const requestDuration = new Trend("contention_request_duration", true);

export const options = {
  scenarios: {
    contention: {
      executor: "per-vu-iterations",
      vus: 20,
      iterations: 1,
      maxDuration: "30s",
      gracefulStop: "5s"
    }
  },
  thresholds: {
    contention_successes: ["count==1"],
    contention_conflicts: ["count==19"],
    contention_unexpected_responses: ["count==0"],
    contention_persisted_bookings: ["value==1"],
    contention_persistence_errors: ["count==0"],
    contention_cleanup_errors: ["count==0"]
  },
  summaryTrendStats: ["avg", "min", "med", "max", "p(90)", "p(95)", "p(99)"]
};

export function setup() {
  return {
    slot: getSlots(7)[0],
    targetEpochMs: Date.now() + 5000,
    identityPrefix: `${runId}-contention-`
  };
}

export default function (data) {
  successes.add(0);
  conflicts.add(0);
  unexpected.add(0);
  const remainingSeconds = (data.targetEpochMs - Date.now()) / 1000;
  if (remainingSeconds > 0) sleep(remainingSeconds);

  const identity = `${data.identityPrefix}${exec.vu.idInTest}`;
  const response = http.post(`${apiUrl}/v2/bookings`, bookingPayload(data.slot, identity), {
    headers: headers("2024-08-13"),
    tags: { operation: "booking-contention" }
  });
  requestDuration.add(response.timings.duration);
  if (response.status === 201 && typeof successData(response)?.uid === "string") {
    successes.add(1);
  } else if (response.status === 400 || response.status === 409) {
    conflicts.add(1);
  } else {
    unexpected.add(1);
  }
}

export function teardown(data) {
  persistenceErrors.add(0);
  cleanupErrors.add(0);
  const response = http.get(`${apiUrl}/v2/bookings`, {
    headers: headers("2024-08-13"),
    tags: { operation: "contention-persistence-verification" }
  });
  if (response.status !== 200 || response.json("status") !== "success") {
    persistenceErrors.add(1);
    persisted.add(0);
    return;
  }

  const bookings = response.json("data") || [];
  const slotEpoch = Date.parse(data.slot);
  const matching = bookings.filter((booking) => {
    const bookingEventTypeId = booking.eventTypeId ?? booking.eventType?.id;
    const sameEvent = bookingEventTypeId === eventTypeId();
    const sameStart = Date.parse(booking.start) === slotEpoch;
    const hasRunAttendee = (booking.attendees || []).some((attendee) =>
      String(attendee.email || "").includes(`qa+${data.identityPrefix}`)
    );
    return sameEvent && sameStart && (hasRunAttendee || bookingEventTypeId === eventTypeId());
  });
  persisted.add(matching.length);

  for (const booking of matching) {
    if (typeof booking.uid !== "string") {
      cleanupErrors.add(1);
      continue;
    }
    const cleanup = cancelBooking(booking.uid);
    cleanupErrors.add(cleanup.status !== 200 && cleanup.status !== 400);
  }
}
