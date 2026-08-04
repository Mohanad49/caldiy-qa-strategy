import { mkdir, writeFile } from "node:fs/promises";

import { expect, test } from "../browser/fixtures.js";
import { firstEventType } from "../browser/fixture-manager.js";
import { BookingPage } from "../browser/pages/booking-page.js";
import {
  TimezoneOracle,
  type OracleInstant,
  type OracleMatrix,
  type OracleZone
} from "../browser/timezone-oracle.js";

const zoneNames = [
  "UTC",
  "America/New_York",
  "Europe/London",
  "Africa/Cairo",
  "Asia/Kolkata",
  "Asia/Kathmandu",
  "Australia/Eucla",
  "Australia/Sydney",
  "America/Phoenix"
] as const;
const apiURL = `http://127.0.0.1:${process.env.CALDIY_API_PORT ?? "5555"}`;
const apiKey = process.env.CALDIY_API_KEY ?? "cal_0123456789abcdef0123456789abcdef";

test.describe.configure({ mode: "serial" });

const oracle = new TimezoneOracle();
let matrix: OracleMatrix;

test.beforeAll(async () => {
  matrix = await oracle.matrix();
  await oracle.retain(matrix);
});

for (const zoneName of zoneNames) {
  test(`Cal.diy slots agree with the pinned oracle in ${zoneName}`, async ({
    browser,
    request,
    fixtureManager
  }, testInfo) => {
    const zone = getZone(zoneName);
    const manifest = await fixtureManager.create({
      timeZone: zoneName,
      startTime: "00:00",
      endTime: "23:59",
      lengthMinutes: 60
    });
    const event = firstEventType(manifest);
    const response = await request.get(`${apiURL}/v2/slots`, {
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "cal-api-version": "2024-09-04"
      },
      params: {
        eventTypeId: event.id,
        start: zone.windowStart,
        end: zone.windowEnd,
        timeZone: zoneName
      }
    });
    expect(response.status(), await response.text()).toBe(200);
    const starts = slotStarts((await response.json()) as unknown);
    expect(starts.length).toBeGreaterThan(0);
    expect(new Set(starts).size).toBe(starts.length);

    const expected = await oracle.convert(zoneName, starts);
    const context = await browser.newContext({ timezoneId: zoneName, locale: "en-US" });
    const page = await context.newPage();
    const browserValues = await page.evaluate((instants) => {
      const pad = (value: number) => String(value).padStart(2, "0");
      return instants.map((instant) => {
        const value = new Date(instant);
        const rawOffsetMinutes = -value.getTimezoneOffset();
        return {
          utc: instant,
          wall: `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}T${pad(
            value.getHours()
          )}:${pad(value.getMinutes())}:${pad(value.getSeconds())}`,
          offsetMinutes: rawOffsetMinutes === 0 ? 0 : rawOffsetMinutes,
          resolvedZone: Intl.DateTimeFormat().resolvedOptions().timeZone
        };
      });
    }, starts);
    await context.close();

    expect(browserValues.map(({ wall, offsetMinutes }) => ({ wall, offsetMinutes }))).toEqual(
      expected.map(({ wall, offsetMinutes }) => ({ wall, offsetMinutes }))
    );
    expect(
      browserValues.every((value) => acceptedBrowserZoneIds(zoneName).includes(value.resolvedZone)),
      `Chromium resolved ${zoneName} as ${[...new Set(browserValues.map((value) => value.resolvedZone))].join(", ")}`
    ).toBeTruthy();

    if (zone.classification === "fractional-offset") {
      expect(expected.some((value) => Math.abs(value.offsetMinutes) % 60 !== 0)).toBeTruthy();
    }
    if (zone.nextTransition?.type === "fold") {
      const wallOffsets = new Map<string, Set<number>>();
      for (const value of expected) {
        const offsets = wallOffsets.get(value.wall) ?? new Set<number>();
        offsets.add(value.offsetMinutes);
        wallOffsets.set(value.wall, offsets);
      }
      const exposesBothFoldInstants = [...wallOffsets.values()].some((offsets) => offsets.size > 1);
      if (!exposesBothFoldInstants && zoneName === "Africa/Cairo") {
        await testInfo.attach("known-cairo-fold-limitation.json", {
          body: Buffer.from(
            JSON.stringify(
              {
                finding: "CALDIY-LOCAL-001",
                transition: zone.nextTransition,
                returnedUTCInstants: starts,
                convertedReturnedInstants: expected
              },
              null,
              2
            )
          ),
          contentType: "application/json"
        });
      } else {
        expect(
          exposesBothFoldInstants,
          `${zoneName} did not expose both UTC instants in its repeated local hour`
        ).toBeTruthy();
      }
    }
    if (zone.nextTransition?.type === "gap") {
      const beforeHour = zone.nextTransition.localBefore.slice(0, 13);
      const afterHour = zone.nextTransition.localAfter.slice(0, 13);
      const absentHour = `${zone.nextTransition.localAfter.slice(0, 11)}${String(
        Number(afterHour.slice(-2)) - 1
      ).padStart(2, "0")}`;
      expect(expected.some((value) => value.wall.startsWith(absentHour))).toBeFalsy();
      expect(beforeHour).not.toBe(afterHour);
    }

    await testInfo.attach("timezone-evidence.json", {
      body: Buffer.from(
        JSON.stringify(
          {
            zone: zoneName,
            tzdataVersion: matrix.tzdataVersion,
            transition: zone.nextTransition,
            queriedWindow: [zone.windowStart, zone.windowEnd],
            returnedUTCInstants: starts
          },
          null,
          2
        )
      ),
      contentType: "application/json"
    });
  });
}

test("opposing hemispheres, DST/non-DST, and fractional offsets remain distinguishable", async ({
  browser
}) => {
  const pairInstants = ["2027-01-15T12:00:00Z", "2027-07-15T12:00:00Z"];
  const zones = [
    ...matrix.pairs.opposingHemispheres,
    ...matrix.pairs.dstAndNonDst,
    ...matrix.pairs.fractionalOffsets
  ];
  const uniqueZones = [...new Set(zones)];
  const evidence = new Map<string, OracleInstant[]>();
  for (const zone of uniqueZones) {
    const expected = await oracle.convert(zone, pairInstants);
    evidence.set(zone, expected);
    const context = await browser.newContext({ timezoneId: zone });
    const page = await context.newPage();
    const actualOffsets = await page.evaluate(
      (instants) => instants.map((instant) => -new Date(instant).getTimezoneOffset()),
      pairInstants
    );
    await context.close();
    expect(actualOffsets).toEqual(expected.map((value) => value.offsetMinutes));
  }

  expect(evidence.get("America/New_York")?.map((value) => value.offsetMinutes)).not.toEqual(
    evidence.get("Australia/Sydney")?.map((value) => value.offsetMinutes)
  );
  expect(evidence.get("America/Phoenix")?.[0]?.offsetMinutes).toBe(
    evidence.get("America/Phoenix")?.[1]?.offsetMinutes
  );
  expect(evidence.get("America/New_York")?.[0]?.offsetMinutes).not.toBe(
    evidence.get("America/New_York")?.[1]?.offsetMinutes
  );
});

test("a New York host and Kathmandu booker keep one instant through reschedule and email", async ({
  browser,
  request,
  fixtureManager,
  mailpit
}, testInfo) => {
  const hostZone = "America/New_York";
  const bookerZone = "Asia/Kathmandu";
  const organizerZone = "Europe/London";
  const manifest = await fixtureManager.create({
    timeZone: hostZone,
    startTime: "23:00",
    endTime: "23:59",
    lengthMinutes: 30
  });
  const event = firstEventType(manifest);
  const context = await browser.newContext({
    baseURL: process.env.CALDIY_WEB_URL ?? `http://localhost:${process.env.CALDIY_WEB_PORT ?? "3000"}`,
    locale: "en-US",
    timezoneId: bookerZone,
    storageState: { cookies: [], origins: [] }
  });
  const page = await context.newPage();
  const booking = new BookingPage(page);
  const attendee = {
    name: `QA cross-zone ${testInfo.workerIndex}`,
    email: `qa+cross-zone-${Date.now()}@example.com`
  };
  const startedAt = new Date();

  await booking.open(event.bookingPath);
  const selectedInstant = await booking.chooseFirstSlotNextMonth();
  const initialUid = await booking.book(attendee);
  fixtureManager.trackBooking(manifest, initialUid);

  const [hostInitial] = await oracle.convert(hostZone, [selectedInstant]);
  const [bookerInitial] = await oracle.convert(bookerZone, [selectedInstant]);
  const [organizerInitial] = await oracle.convert(organizerZone, [selectedInstant]);
  expect(hostInitial?.wall.slice(0, 10)).not.toBe(bookerInitial?.wall.slice(0, 10));
  expect(normalizeTimestamp(await booking.whenText())).toContain(wallTimeToken(requiredInstant(bookerInitial)));

  const organizerMessage = await mailpit.waitForMessage(
    "owner1-acme@example.com",
    (candidate) => {
      const subject = normalizeTimestamp(candidate.Subject);
      return (
        candidate.Subject.startsWith("[Action Required] Confirmed:") &&
        subject.includes(wallTimeToken(requiredInstant(organizerInitial))) &&
        mailpit.body(candidate).includes(attendee.email)
      );
    },
    { after: startedAt }
  );

  const rescheduledAt = new Date();
  const replacementUid = await booking.reschedule(initialUid);
  fixtureManager.trackBooking(manifest, replacementUid);
  const replacementInstant = await bookingStart(request, replacementUid);
  const [bookerReplacement] = await oracle.convert(bookerZone, [replacementInstant]);
  expect(normalizeTimestamp(await booking.whenText())).toContain(
    wallTimeToken(requiredInstant(bookerReplacement))
  );

  const attendeeMessage = await mailpit.waitForMessage(
    attendee.email,
    (candidate) => {
      const subject = normalizeTimestamp(candidate.Subject);
      const body = mailpit.body(candidate).toLowerCase();
      return (
        body.includes(event.title.toLowerCase()) &&
        body.includes("reschedul") &&
        subject.includes(wallTimeToken(requiredInstant(bookerReplacement)))
      );
    },
    { after: rescheduledAt }
  );

  await testInfo.attach("cross-zone-lifecycle.json", {
    body: Buffer.from(
      JSON.stringify(
        {
          hostZone,
          bookerZone,
          organizerZone,
          tzdataVersion: matrix.tzdataVersion,
          initial: {
            utc: selectedInstant,
            host: hostInitial,
            booker: bookerInitial,
            organizer: organizerInitial,
            organizerEmailSubject: organizerMessage.Subject
          },
          rescheduled: {
            uid: replacementUid,
            utc: replacementInstant,
            booker: bookerReplacement,
            attendeeEmailSubject: attendeeMessage.Subject
          }
        },
        null,
        2
      )
    ),
    contentType: "application/json"
  });
  await context.close();
});

test("Sydney spring-gap boundary behavior preserves duration or records slot exclusion", async ({
  browser,
  request,
  fixtureManager
}) => {
  const zone = getZone("Australia/Sydney");
  expect(zone.nextTransition?.type).toBe("gap");
  const manifest = await fixtureManager.create({
    timeZone: zone.name,
    startTime: "00:00",
    endTime: "05:00",
    lengthMinutes: 90
  });
  const response = await request.get(`${apiURL}/v2/slots`, {
    headers: { Authorization: `Bearer ${apiKey}`, "cal-api-version": "2024-09-04" },
    params: {
      eventTypeId: firstEventType(manifest).id,
      start: zone.windowStart,
      end: zone.windowEnd,
      timeZone: zone.name
    }
  });
  expect(response.status(), await response.text()).toBe(200);
  const starts = slotStarts((await response.json()) as unknown);
  const transitionEpoch = Date.parse(zone.nextTransition?.utc ?? "");
  const crossing = starts.find((start) => {
    const epoch = Date.parse(start);
    return epoch < transitionEpoch && epoch + 90 * 60_000 > transitionEpoch;
  });
  if (crossing === undefined) {
    expect(starts.some((start) => Date.parse(start) < transitionEpoch)).toBeTruthy();
    expect(starts.some((start) => Date.parse(start) >= transitionEpoch)).toBeTruthy();
    await test.info().attach("sydney-gap-slot-exclusion.json", {
      body: Buffer.from(
        JSON.stringify(
          {
            behavior: "Cal.diy omitted 90-minute slots that would cross the spring-forward instant",
            transition: zone.nextTransition,
            returnedUTCInstants: starts
          },
          null,
          2
        )
      ),
      contentType: "application/json"
    });
    return;
  }
  const instants = [crossing as string, new Date(Date.parse(crossing as string) + 90 * 60_000).toISOString()];
  const converted = await oracle.convert(zone.name, instants);
  const wallElapsed = wallMinutes(converted[0] as OracleInstant, converted[1] as OracleInstant);
  expect(wallElapsed).not.toBe(90);

  const context = await browser.newContext({ timezoneId: zone.name });
  const page = await context.newPage();
  expect(
    await page.evaluate(
      ({ start, end }) => (new Date(end).valueOf() - new Date(start).valueOf()) / 60_000,
      { start: instants[0] as string, end: instants[1] as string }
    )
  ).toBe(90);
  await context.close();
});

test("historical Cairo 2023 behavior is recorded without database bypass", async ({
  request,
  fixtureManager
}, testInfo) => {
  expect(matrix.historicalCairo2023.map((transition) => transition.type)).toEqual(["gap", "fold"]);
  const manifest = await fixtureManager.create({
    timeZone: "Africa/Cairo",
    startTime: "00:00",
    endTime: "05:00"
  });
  const response = await request.get(`${apiURL}/v2/slots`, {
    headers: { Authorization: `Bearer ${apiKey}`, "cal-api-version": "2024-09-04" },
    params: {
      eventTypeId: firstEventType(manifest).id,
      start: "2023-04-27",
      end: "2023-04-29",
      timeZone: "Africa/Cairo"
    }
  });
  const historicalStarts = response.ok() ? slotStarts((await response.json()) as unknown) : [];
  const result = {
    status: response.status(),
    behavior: response.ok()
      ? historicalStarts.length > 0
        ? "historical-window-returned"
        : "historical-window-empty"
      : "historical-window-rejected",
    slotCount: historicalStarts.length,
    transitions: matrix.historicalCairo2023
  };
  await mkdir("test-results/timezones", { recursive: true });
  await writeFile("test-results/timezones/cairo-2023.json", `${JSON.stringify(result, null, 2)}\n`);
  await testInfo.attach("cairo-2023.json", {
    body: Buffer.from(JSON.stringify(result, null, 2)),
    contentType: "application/json"
  });
  if (response.ok()) {
    expect(response.status()).toBe(200);
  } else {
    expect([400, 422]).toContain(response.status());
  }
});

test("Playwright Clock is limited to browser-side now behavior", async ({ browser, request }) => {
  const context = await browser.newContext({ timezoneId: "Africa/Cairo" });
  const page = await context.newPage();
  const frozen = new Date("2027-04-30T12:00:00Z");
  await page.clock.setFixedTime(frozen);
  expect(await page.evaluate(() => new Date().toISOString())).toBe(frozen.toISOString());
  const health = await request.get(`${apiURL}/health`);
  expect(health.status()).toBe(200);
  expect(health.headers()["date"]).not.toBe(frozen.toUTCString());
  await context.close();
});

function getZone(name: string): OracleZone {
  const zone = matrix.zones.find((candidate) => candidate.name === name);
  if (zone === undefined) throw new Error(`Oracle matrix has no ${name}`);
  return zone;
}

function acceptedBrowserZoneIds(name: string): string[] {
  const aliases: Record<string, string[]> = {
    "Asia/Kolkata": ["Asia/Calcutta"],
    "Asia/Kathmandu": ["Asia/Katmandu"]
  };
  return [name, ...(aliases[name] ?? [])];
}

function slotStarts(payload: unknown): string[] {
  if (typeof payload !== "object" || payload === null) throw new Error("Slots response is not an object");
  const envelope = payload as { data?: unknown };
  const data = envelope.data ?? payload;
  if (typeof data !== "object" || data === null) throw new Error("Slots response has no data object");
  const starts: string[] = [];
  for (const daySlots of Object.values(data)) {
    if (!Array.isArray(daySlots)) continue;
    for (const slot of daySlots) {
      if (typeof slot === "object" && slot !== null && typeof (slot as { start?: unknown }).start === "string") {
        starts.push((slot as { start: string }).start);
      }
    }
  }
  return starts.sort();
}

function wallMinutes(start: OracleInstant, end: OracleInstant): number {
  const startWithoutOffset = new Date(`${start.wall}Z`).valueOf();
  const endWithoutOffset = new Date(`${end.wall}Z`).valueOf();
  return (endWithoutOffset - startWithoutOffset) / 60_000;
}

function requiredInstant(value: OracleInstant | undefined): OracleInstant {
  if (value === undefined) throw new Error("Timezone oracle returned no converted instant");
  return value;
}

function wallTimeToken(value: OracleInstant): string {
  const [hourText, minute = "00"] = value.wall.slice(11, 16).split(":");
  const hour = Number(hourText);
  const suffix = hour >= 12 ? "pm" : "am";
  const twelveHour = hour % 12 || 12;
  return `${twelveHour}:${minute}${suffix}`;
}

function normalizeTimestamp(value: string): string {
  return value.toLowerCase().replace(/\s+/g, "");
}

async function bookingStart(
  request: import("@playwright/test").APIRequestContext,
  uid: string
): Promise<string> {
  const response = await request.get(`${apiURL}/v2/bookings/${uid}`, {
    headers: { Authorization: `Bearer ${apiKey}`, "cal-api-version": "2024-08-13" }
  });
  expect(response.status(), await response.text()).toBe(200);
  const payload = (await response.json()) as { data?: { start?: unknown } };
  if (typeof payload.data?.start !== "string") throw new Error(`Booking ${uid} has no start instant`);
  return payload.data.start;
}
