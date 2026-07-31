import { expect, type Page } from "@playwright/test";

import { dismissTimezonePrompt } from "../timezone-prompt.js";

export class EventTypesPage {
  constructor(private readonly page: Page) {}

  async create(title: string): Promise<number> {
    await this.page.goto("/event-types");
    await expect(this.page.getByTestId("event-types")).toBeVisible();
    await dismissTimezonePrompt(this.page);
    await this.page.getByTestId("new-event-type").click();
    const personalProfile = this.page.getByTestId("option-0");
    if (await personalProfile.isVisible().catch(() => false)) await personalProfile.click();
    await this.page.locator('[name="title"]').fill(title);
    await this.page.locator('[name="length"]').fill("25");
    await this.page.locator('[type="submit"]').click();
    await this.page.waitForURL((url) => /\/event-types\/\d+/.test(url.pathname));
    await expect(this.page.getByTestId("event-title")).toBeVisible();
    const id = Number(new URL(this.page.url()).pathname.split("/").filter(Boolean).at(-1));
    if (!Number.isInteger(id)) throw new Error(`Could not read event-type ID from ${this.page.url()}`);
    return id;
  }
}
