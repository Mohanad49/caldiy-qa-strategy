import { expect, test } from "../browser/fixtures.js";
import { firstEventType } from "../browser/fixture-manager.js";
import { BookingPage } from "../browser/pages/booking-page.js";

test.describe("desktop booking visual", () => {
  test.use({ viewport: { width: 1440, height: 900 }, timezoneId: "UTC" });

  test("public booking page at 1440x900", async ({ page, fixtureManager }) => {
    const event = firstEventType(await fixtureManager.create());
    await new BookingPage(page).open(event.bookingPath);
    await prepareVisualState(page);
    await expect(page).toHaveScreenshot("public-booking-1440x900.png", {
      animations: "disabled",
      mask: await dynamicCalendarRegions(page, "desktop")
    });
  });
});

test.describe("mobile booking visual", () => {
  test.use({ viewport: { width: 390, height: 844 }, timezoneId: "UTC", isMobile: true });

  test("public booking page at 390x844", async ({ page, fixtureManager }) => {
    const event = firstEventType(await fixtureManager.create());
    await new BookingPage(page).open(event.bookingPath);
    await prepareVisualState(page);
    await expect(page).toHaveScreenshot("public-booking-390x844.png", {
      animations: "disabled",
      mask: await dynamicCalendarRegions(page, "mobile")
    });
  });
});

async function dynamicCalendarRegions(
  page: import("@playwright/test").Page,
  layout: "desktop" | "mobile"
): Promise<import("@playwright/test").Locator[]> {
  // Calendar cells and available-slot counts depend on the server's real date.
  // Desktop uses main/timeslots grid areas. Mobile moves the calendar into the
  // metadata column, while its below-the-fold slot grid must not be allowed to
  // expand a mask over the viewport. Validate every mask box before capture so
  // a responsive-layout change cannot turn this into a full-page magenta pass.
  const booker = page.getByTestId("booker-container");
  const responsiveCalendar = booker
    .locator(':scope > [class*="[grid-area:meta]"]')
    .getByTestId("selected-month-label")
    .locator(
      "xpath=ancestor::div[contains(concat(' ', normalize-space(@class), ' '), ' mt-auto ')][1]"
    )
    .locator(":scope > div");
  const masks =
    layout === "mobile"
      ? [responsiveCalendar]
      : [
          booker.locator(':scope > [class*="[grid-area:main]"]'),
          booker.locator(':scope > [class*="[grid-area:timeslots]"]')
        ];

  const viewport = page.viewportSize();
  const metadataBox = await page.getByTestId("event-meta").boundingBox();
  if (!viewport || !metadataBox) {
    throw new Error("Visual mask guard could not resolve the viewport or event metadata box");
  }

  let maskedArea = 0;
  for (const [index, mask] of masks.entries()) {
    if ((await mask.count()) !== 1) {
      throw new Error(`Visual mask ${layout}[${index}] must resolve to exactly one element`);
    }
    const box = await mask.boundingBox();
    if (!box) {
      throw new Error(`Visual mask ${layout}[${index}] has no visible bounding box`);
    }
    const metadataCenter = {
      x: metadataBox.x + metadataBox.width / 2,
      y: metadataBox.y + metadataBox.height / 2
    };
    if (
      metadataCenter.x >= box.x &&
      metadataCenter.x <= box.x + box.width &&
      metadataCenter.y >= box.y &&
      metadataCenter.y <= box.y + box.height
    ) {
      throw new Error(`Visual mask ${layout}[${index}] covers the event metadata center`);
    }
    maskedArea += box.width * box.height;
  }

  const viewportArea = viewport.width * viewport.height;
  if (maskedArea / viewportArea >= 0.75) {
    throw new Error(`Visual masks cover too much of the ${layout} viewport`);
  }
  return masks;
}

async function prepareVisualState(page: import("@playwright/test").Page): Promise<void> {
  await expect(page.getByTestId("day").first()).toBeVisible();
  await expect(page.getByTestId("time").first()).toBeVisible();
  await expect(page.getByTestId("event-meta").locator(":scope > div").first()).toHaveCSS("opacity", "1");
  await page.addStyleTag({
    content:
      "*, *::before, *::after { animation-duration: 0s !important; transition-duration: 0s !important; }"
  });
}
