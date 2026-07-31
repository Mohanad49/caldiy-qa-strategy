import { expect, type Page } from "@playwright/test";

export class AvailabilityPage {
  constructor(private readonly page: Page) {}

  async toggleSundayAndSave(scheduleId: number): Promise<void> {
    await this.page.goto(`/availability/${scheduleId}`);
    await expect(this.page.locator("#availability-form")).toBeVisible();
    const sunday = this.page.getByTestId("Sunday-switch").first();
    const before = await sunday.getAttribute("data-state");
    await sunday.click();
    const responsePromise = this.page.waitForResponse(
      (response) => response.url().includes("/api/trpc/availability/schedule.update")
    );
    await this.page.locator('[form="availability-form"][type="submit"]').click();
    const response = await responsePromise;
    expect(response.status(), await response.text()).toBe(200);
    await this.page.reload();
    await expect(this.page.getByTestId("Sunday-switch").first()).not.toHaveAttribute("data-state", before ?? "");
  }
}
