import { expect, test } from "../browser/fixtures.js";
import { firstEventType } from "../browser/fixture-manager.js";
import { BookingPage } from "../browser/pages/booking-page.js";

const monthNames = /January|February|March|April|May|June|July|August|September|October|November|December/;

test("@firefox guest booking is confirmed and correlated to the local organizer notification", async ({
  guestPage,
  fixtureManager,
  mailpit
}, testInfo) => {
  const manifest = await fixtureManager.create(lifecycleWindow(testInfo.project.name, "booking"));
  const event = firstEventType(manifest);
  const attendee = attendeeFor(testInfo.project.name, testInfo.workerIndex);
  const booking = new BookingPage(guestPage);
  const startedAt = new Date();

  await booking.open(event.bookingPath);
  await booking.chooseFirstSlotNextMonth();
  const uid = await booking.book(attendee);
  fixtureManager.trackBooking(manifest, uid);
  const when = await booking.whenText();
  const month = when.match(monthNames)?.[0];
  expect(month, `No month name found in confirmation timestamp: ${when}`).toBeDefined();

  const message = await mailpit.waitForMessage(
    "owner1-acme@example.com",
    (candidate) => {
      const body = mailpit.body(candidate);
      return (
        candidate.Subject.startsWith("[Action Required] Confirmed:") &&
        body.includes(event.title) &&
        body.includes(attendee.email) &&
        body.includes(month ?? "__missing_month__")
      );
    },
    { after: startedAt }
  );
  expect(mailpit.body(message)).toContain(attendee.email);
});

test("@firefox attendee reschedules and receives a correlated lifecycle notification", async ({
  guestPage,
  fixtureManager,
  mailpit
}, testInfo) => {
  const manifest = await fixtureManager.create(lifecycleWindow(testInfo.project.name, "reschedule"));
  const event = firstEventType(manifest);
  const attendee = attendeeFor(`${testInfo.project.name}-reschedule`, testInfo.workerIndex);
  const booking = new BookingPage(guestPage);

  await booking.open(event.bookingPath);
  await booking.chooseFirstSlotNextMonth();
  const originalUid = await booking.book(attendee);
  fixtureManager.trackBooking(manifest, originalUid);
  const actionAt = new Date();
  const newUid = await booking.reschedule(originalUid);
  fixtureManager.trackBooking(manifest, newUid);
  expect(newUid).not.toBe(originalUid);

  const message = await mailpit.waitForMessage(
    attendee.email,
    (candidate) => {
      const body = mailpit.body(candidate).toLowerCase();
      return body.includes(event.title.toLowerCase()) && body.includes("reschedul");
    },
    { after: actionAt }
  );
  expect(mailpit.body(message).toLowerCase()).toContain("reschedul");
});

test("@firefox attendee cancels and receives a correlated lifecycle notification", async ({
  guestPage,
  fixtureManager,
  mailpit
}, testInfo) => {
  const manifest = await fixtureManager.create(lifecycleWindow(testInfo.project.name, "cancel"));
  const event = firstEventType(manifest);
  const attendee = attendeeFor(`${testInfo.project.name}-cancel`, testInfo.workerIndex);
  const booking = new BookingPage(guestPage);

  await booking.open(event.bookingPath);
  await booking.chooseFirstSlotNextMonth();
  const uid = await booking.book(attendee);
  fixtureManager.trackBooking(manifest, uid);
  const actionAt = new Date();
  await booking.cancel("Phase 3 cancellation journey");

  const message = await mailpit.waitForMessage(
    attendee.email,
    (candidate) => {
      const body = mailpit.body(candidate).toLowerCase();
      return body.includes(event.title.toLowerCase()) && body.includes("cancel");
    },
    { after: actionAt }
  );
  expect(mailpit.body(message)).toContain("Phase 3 cancellation journey");
});

function attendeeFor(purpose: string, workerIndex: number): { name: string; email: string } {
  const token = `${purpose}-${workerIndex}-${Date.now()}`.toLowerCase().replace(/[^a-z0-9-]+/g, "-");
  return { name: `QA ${token}`, email: `qa+${token}@example.com` };
}

function lifecycleWindow(
  projectName: string,
  journey: "booking" | "reschedule" | "cancel"
): { startTime: string; endTime: string } {
  const browser = projectName.startsWith("firefox") ? "firefox" : "chromium";
  const windows = {
    chromium: {
      booking: { startTime: "09:00", endTime: "10:00" },
      reschedule: { startTime: "10:00", endTime: "12:00" },
      cancel: { startTime: "12:00", endTime: "13:00" }
    },
    firefox: {
      booking: { startTime: "13:00", endTime: "14:00" },
      reschedule: { startTime: "14:00", endTime: "16:00" },
      cancel: { startTime: "16:00", endTime: "17:00" }
    }
  } as const;
  return windows[browser][journey];
}
