import { AxeBuilder } from "@axe-core/playwright";
import { mkdir, writeFile } from "node:fs/promises";

import { expect, test } from "../browser/fixtures.js";
import { firstEventType } from "../browser/fixture-manager.js";
import { BookingPage } from "../browser/pages/booking-page.js";

test("public booking page has no serious or critical axe violations", async ({
  page,
  fixtureManager
}, testInfo) => {
  const event = firstEventType(await fixtureManager.create());
  await new BookingPage(page).open(event.bookingPath);
  await expect(page.getByTestId("day").first()).toBeVisible();
  await assertNoBlockingViolations(page, "public-booking", testInfo);
});

test("guest details step has no serious or critical axe violations", async ({
  page,
  fixtureManager
}, testInfo) => {
  const event = firstEventType(await fixtureManager.create());
  const booking = new BookingPage(page);
  await booking.open(event.bookingPath);
  await booking.chooseFirstSlotNextMonth();
  await expect(page.getByTestId("confirm-book-button")).toBeVisible();
  await assertNoBlockingViolations(page, "guest-details", testInfo);
});

test("cancellation panel has no serious or critical axe violations", async ({
  page,
  fixtureManager
}, testInfo) => {
  const manifest = await fixtureManager.create();
  const event = firstEventType(manifest);
  const booking = new BookingPage(page);
  await booking.open(event.bookingPath);
  await booking.chooseFirstSlotNextMonth();
  const uid = await booking.book({
    name: "QA Accessibility",
    email: `qa+a11y-${Date.now()}@example.com`
  });
  fixtureManager.trackBooking(manifest, uid);
  await page.getByTestId("cancel").click();
  await expect(page.getByTestId("confirm_cancel")).toBeVisible();
  await expect(page).toHaveTitle(/.+/);
  await assertNoBlockingViolations(page, "cancellation-panel", testInfo);
});

async function assertNoBlockingViolations(
  page: import("@playwright/test").Page,
  surface: string,
  testInfo: import("@playwright/test").TestInfo
): Promise<void> {
  await page.waitForLoadState("networkidle");
  await page.evaluate(async () => document.fonts.ready);
  const results = await new AxeBuilder({ page }).analyze();
  const blocking = results.violations.filter(
    (violation) => violation.impact === "serious" || violation.impact === "critical"
  );
  const findingByRule: Record<string, string> = {
    "button-name": "CALDIY-LOCAL-002",
    "color-contrast": "CALDIY-LOCAL-003",
    "link-in-text-block": "CALDIY-LOCAL-004"
  };
  const evidence = {
    surface,
    url: page.url(),
    scannedAt: new Date().toISOString(),
    findingIds: [...new Set(blocking.map((violation) => findingByRule[violation.id]).filter(Boolean))],
    seriousOrCritical: blocking
  };
  await mkdir("test-results/a11y", { recursive: true });
  await writeFile(`test-results/a11y/${surface}.json`, `${JSON.stringify(evidence, null, 2)}\n`);
  await testInfo.attach(`${surface}-axe.json`, {
    body: Buffer.from(JSON.stringify(evidence, null, 2)),
    contentType: "application/json"
  });
  expect(
    blocking.map((violation) => ({
      id: violation.id,
      impact: violation.impact,
      nodeCount: violation.nodes.length
    })),
    `${surface} has evidence-backed serious/critical axe violations`
  ).toEqual([]);
}
