import { expect, test } from "../browser/fixtures.js";
import { FixtureManager, firstEventType } from "../browser/fixture-manager.js";
import { AvailabilityPage } from "../browser/pages/availability-page.js";
import { EventTypesPage } from "../browser/pages/event-types-page.js";

test("authenticated owner creates an isolated event type through the UI", async ({
  page,
  fixtureManager
}, testInfo) => {
  const title = `QA UI Event ${testInfo.workerIndex} ${Date.now()}`;
  const eventTypeId = await new EventTypesPage(page).create(title);
  fixtureManager.track(FixtureManager.manifestForEventType(testInfo.testId, eventTypeId));

  await page.goto("/event-types");
  await expect(page.getByText(title, { exact: true })).toBeVisible();
});

test("authenticated owner changes an API-created availability schedule through the UI", async ({
  page,
  fixtureManager
}) => {
  const manifest = await fixtureManager.create({ timeZone: "UTC" });
  const scheduleId = manifest.resources.scheduleIds[0];
  if (scheduleId === undefined) throw new Error("Fixture has no schedule ID");

  await new AvailabilityPage(page).toggleSundayAndSave(scheduleId);
  await expect(page.getByTestId("availablity-title")).toBeVisible();
  expect(firstEventType(manifest).bookingPath).toContain("/owner1/");
});
