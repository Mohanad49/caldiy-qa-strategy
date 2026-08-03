import { expect, type Page } from "@playwright/test";

export interface Attendee {
  name: string;
  email: string;
}

export class BookingPage {
  constructor(private readonly page: Page) {}

  async open(path: string): Promise<void> {
    await this.page.setExtraHTTPHeaders({
      "x-cal-client-id": "caldiy-qa-local",
      "x-cal-force-slug": "acme"
    });
    const statuses: number[] = [];
    const deadline = Date.now() + 15_000;

    while (true) {
      const response = await this.page.goto(path, { waitUntil: "domcontentloaded" });
      const status = response?.status() ?? 0;
      statuses.push(status);
      if (status === 200) break;
      if (status !== 404 || Date.now() >= deadline) {
        throw new Error(
          `Booking route ${path} did not become ready; HTTP statuses: ${statuses.join(", ")}`
        );
      }
      await this.page.waitForTimeout(500);
    }

    await expect(this.page.getByTestId("booker-container")).toBeVisible();
  }

  async chooseFirstSlotNextMonth(): Promise<void> {
    await this.page.getByTestId("incrementMonth").click();
    const day = this.page.locator('[data-testid="day"][data-disabled="false"]').first();
    await expect(day).toBeVisible();
    await day.click();
    const time = this.page.getByTestId("time").first();
    await expect(time).toBeVisible();
    await time.click();
  }

  async book(attendee: Attendee): Promise<string> {
    await this.page.locator('[name="name"]').fill(attendee.name);
    await this.page.locator('[name="email"]').fill(attendee.email);
    const responsePromise = this.page.waitForResponse(
      (response) => response.url().includes("/api/book/event") && response.request().method() === "POST"
    );
    await this.page.getByTestId("confirm-book-button").click();
    const response = await responsePromise;
    expect(response.status(), await response.text()).toBe(200);
    await expect(this.page.getByTestId("success-page")).toBeVisible();
    return this.bookingUid();
  }

  async reschedule(uid: string): Promise<string> {
    await this.page.goto(`/reschedule/${uid}`);
    await this.chooseFirstSlotNextMonth();
    const responsePromise = this.page.waitForResponse(
      (response) => response.url().includes("/api/book/event") && response.request().method() === "POST"
    );
    await this.page.getByTestId("confirm-reschedule-button").click();
    const response = await responsePromise;
    expect(response.status(), await response.text()).toBe(200);
    await expect(this.page.getByTestId("success-page")).toBeVisible();
    return this.bookingUid();
  }

  async cancel(reason: string): Promise<void> {
    await this.page.getByTestId("cancel").click();
    await this.page.getByTestId("cancel_reason").fill(reason);
    const responsePromise = this.page.waitForResponse(
      (response) => response.url().endsWith("/api/cancel") && response.request().method() === "POST"
    );
    await this.page.getByTestId("confirm_cancel").click();
    const response = await responsePromise;
    expect(response.ok(), await response.text()).toBeTruthy();
    await expect(this.page.getByTestId("cancelled-headline")).toBeVisible();
  }

  async whenText(): Promise<string> {
    const when = this.page.getByText("When", { exact: true }).first();
    const value = when.locator("xpath=following-sibling::*[1]");
    return (await value.innerText()).replace(/\s+/g, " ").trim();
  }

  private bookingUid(): string {
    const segments = new URL(this.page.url()).pathname.split("/").filter(Boolean);
    const uid = segments.at(-1);
    if (uid === undefined || uid === "booking") throw new Error(`Could not read booking UID from ${this.page.url()}`);
    return uid;
  }
}
