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
  // Calendar cells and available-slot counts depend on the server's real date.
  // Mask their fixed grid sections as units so changing child counts cannot
  // move mask boundaries while the surrounding responsive shell stays tested.
  const booker = page.getByTestId("booker-container");
  return [
    booker.locator(':scope > [class*="[grid-area:main]"]'),
    booker.locator(':scope > [class*="[grid-area:timeslots]"]')
  ];
}
