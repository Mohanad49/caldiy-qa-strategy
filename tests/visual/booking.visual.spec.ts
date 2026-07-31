import { expect, test } from "../browser/fixtures.js";
import { firstEventType } from "../browser/fixture-manager.js";
import { BookingPage } from "../browser/pages/booking-page.js";

test.describe("desktop booking visual", () => {
  test.use({ viewport: { width: 1440, height: 900 }, timezoneId: "UTC" });

  test("public booking page at 1440x900", async ({ page, fixtureManager }) => {
    const event = firstEventType(await fixtureManager.create());
    await new BookingPage(page).open(event.bookingPath);
    await expect(page.getByTestId("day").first()).toBeVisible();
    await expect(page).toHaveScreenshot("public-booking-1440x900.png", {
      animations: "disabled",
      mask: dynamicCalendarRegions(page)
    });
  });
});

test.describe("mobile booking visual", () => {
  test.use({ viewport: { width: 390, height: 844 }, timezoneId: "UTC", isMobile: true });

  test("public booking page at 390x844", async ({ page, fixtureManager }) => {
    const event = firstEventType(await fixtureManager.create());
    await new BookingPage(page).open(event.bookingPath);
    await expect(page.getByTestId("day").first()).toBeVisible();
    await expect(page).toHaveScreenshot("public-booking-390x844.png", {
      animations: "disabled",
      mask: dynamicCalendarRegions(page)
    });
  });
});

function dynamicCalendarRegions(page: import("@playwright/test").Page): import("@playwright/test").Locator[] {
  return [
    page.getByTestId("selected-month-label"),
    page.getByTestId("day"),
    page.getByTestId("time"),
    page.getByTestId("booker-container").locator("header > span")
  ];
}
