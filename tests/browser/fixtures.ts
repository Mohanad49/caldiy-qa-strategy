import { test as base, expect, type Page } from "@playwright/test";

import { FixtureManager } from "./fixture-manager.js";
import { MailpitClient } from "./mailpit-client.js";

interface BrowserFixtures {
  fixtureManager: FixtureManager;
  guestPage: Page;
  mailpit: MailpitClient;
}

export const test = base.extend<BrowserFixtures>({
  fixtureManager: async ({}, use, testInfo) => {
    const identity = `pw-${testInfo.project.name}-${testInfo.testId}`
      .replace(/[^a-zA-Z0-9-]+/g, "-")
      .slice(0, 60);
    const manager = new FixtureManager(identity);
    await use(manager);
    await manager.cleanup();
  },
  guestPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      baseURL: process.env.CALDIY_WEB_URL ?? `http://localhost:${process.env.CALDIY_WEB_PORT ?? "3000"}`,
      locale: "en-US",
      storageState: { cookies: [], origins: [] }
    });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },
  mailpit: async ({}, use) => {
    await use(new MailpitClient());
  }
});

export { expect };
