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
  // Desktop uses main/timeslots grid areas. Mobile moves the calendar beneath
  // meta and time choices into main, so select the nearest stable calendar
  // wrapper there without masking event metadata.
  const booker = page.getByTestId("booker-container");
  const responsiveCalendar = booker
    .locator(':scope > [class*="[grid-area:meta]"]')
    .getByTestId("selected-month-label")
    .locator(
      "xpath=ancestor::div[contains(concat(' ', normalize-space(@class), ' '), ' mt-auto ')][1]"
    );
  return [
    responsiveCalendar,
    booker.locator(':scope > [class*="[grid-area:main]"]'),
    booker.locator(':scope > [class*="[grid-area:timeslots]"]')
  ];
}
