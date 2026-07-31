import { World, setDefaultTimeout, setWorldConstructor, type IWorldOptions } from "@cucumber/cucumber";
import { chromium, type Browser, type BrowserContext, type Page } from "@playwright/test";

import { FixtureManager, type EventTypeFixture, type FixtureManifest } from "../../browser/fixture-manager.ts";
import { MailpitClient } from "../../browser/mailpit-client.ts";
import { BookingPage } from "../../browser/pages/booking-page.ts";

export class LifecycleWorld extends World {
  browser?: Browser;
  context?: BrowserContext;
  page?: Page;
  bookingPage?: BookingPage;
  fixtureManager?: FixtureManager;
  manifest?: FixtureManifest;
  event?: EventTypeFixture;
  attendee?: { name: string; email: string };
  bookingUid?: string;
  replacementUid?: string;
  actionAt?: Date;
  readonly mailpit = new MailpitClient();

  constructor(options: IWorldOptions) {
    super(options);
  }

  async start(scenarioName: string): Promise<void> {
    const identity = `bdd-${scenarioName}`.toLowerCase().replace(/[^a-z0-9-]+/g, "-").slice(0, 60);
    this.fixtureManager = new FixtureManager(identity);
    this.browser = await chromium.launch();
    this.context = await this.browser.newContext({
      baseURL: process.env.CALDIY_WEB_URL ?? `http://localhost:${process.env.CALDIY_WEB_PORT ?? "3000"}`,
      locale: "en-US",
      storageState: { cookies: [], origins: [] }
    });
    this.page = await this.context.newPage();
    this.bookingPage = new BookingPage(this.page);
    const token = `${identity}-${Date.now()}`;
    this.attendee = { name: `QA ${token}`, email: `qa+${token}@example.com` };
  }

  async stop(): Promise<void> {
    const failures: Error[] = [];
    if (this.fixtureManager !== undefined) {
      try {
        await this.fixtureManager.cleanup();
      } catch (error) {
        failures.push(error instanceof Error ? error : new Error(String(error)));
      }
    }
    await this.context?.close();
    await this.browser?.close();
    if (failures.length > 0) throw new AggregateError(failures, "BDD fixture cleanup failed");
  }

  required<T>(value: T | undefined, label: string): T {
    if (value === undefined) throw new Error(`BDD world is missing ${label}`);
    return value;
  }
}

setDefaultTimeout(60_000);
setWorldConstructor(LifecycleWorld);
