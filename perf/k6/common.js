import http from "k6/http";

const manifestPath = __ENV.PERF_FIXTURE_MANIFEST;

if (!manifestPath) {
  throw new Error("PERF_FIXTURE_MANIFEST is required");
}

export const fixture = JSON.parse(open(manifestPath));
export const apiUrl = __ENV.CALDIY_API_URL || "http://localhost:5555";
export const apiKey = __ENV.CALDIY_API_KEY;
export const runId = (__ENV.QA_RUN_ID || "local-perf").replace(/[^a-zA-Z0-9-]/g, "-");

if (!apiKey) {
  throw new Error("CALDIY_API_KEY is required");
}

export function eventTypeId() {
  const value = fixture?.resources?.eventTypeIds?.[0];
  if (!Number.isInteger(value)) {
    throw new Error("fixture manifest has no integer event type ID");
  }
  return value;
}

export function headers(version) {
  return {
    Accept: "application/json",
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
    "cal-api-version": version
  };
}

export function publicHeaders(version, clientId) {
  return {
    Accept: "application/json",
    "cal-api-version": version,
    "x-cal-client-id": clientId
  };
}

export function futureDateRange(days = 14) {
  const start = new Date();
  start.setUTCDate(start.getUTCDate() + 1);
  const end = new Date(start);
  end.setUTCDate(end.getUTCDate() + days);
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10)
  };
}

export function slotsUrl(days = 14) {
  const range = futureDateRange(days);
  const query = [
    ["eventTypeId", String(eventTypeId())],
    ["start", range.start],
    ["end", range.end],
    ["timeZone", "UTC"]
  ]
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join("&");
  return `${apiUrl}/v2/slots?${query}`;
}

export function getSlots(days = 14) {
  const response = http.get(slotsUrl(days), {
    headers: headers("2024-09-04"),
    tags: { operation: "slots" }
  });
  if (response.status !== 200) {
    throw new Error(`slot discovery returned ${response.status}: ${response.body}`);
  }
  const data = response.json("data");
  const starts = [];
  for (const day of Object.keys(data || {}).sort()) {
    for (const slot of data[day] || []) {
      if (typeof slot?.start === "string") starts.push(slot.start);
    }
  }
  if (starts.length === 0) throw new Error("slot discovery returned no starts");
  return starts.sort();
}

export function bookingPayload(start, identity) {
  return JSON.stringify({
    eventTypeId: eventTypeId(),
    start,
    attendee: {
      name: `QA ${identity}`,
      email: `qa+${identity}@example.com`,
      timeZone: "UTC",
      language: "en"
    },
    metadata: { qaRun: runId, qaIdentity: identity }
  });
}

export function successData(response) {
  if (response.status < 200 || response.status >= 300) return null;
  const body = response.json();
  return body?.status === "success" ? body.data : null;
}

export function cancelBooking(uid) {
  return http.post(
    `${apiUrl}/v2/bookings/${encodeURIComponent(uid)}/cancel`,
    JSON.stringify({ cancellationReason: "Phase 4 local performance cleanup" }),
    {
      headers: headers("2024-08-13"),
      tags: { operation: "booking-cleanup" }
    }
  );
}
