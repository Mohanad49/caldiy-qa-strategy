import { mkdir } from "node:fs/promises";
import { dirname } from "node:path";

import { test as setup } from "@playwright/test";

import { LoginPage } from "./pages/login-page.js";
import { dismissTimezonePrompt } from "./timezone-prompt.js";

const authState = "test-results/auth/owner1-acme.json";

setup("authenticate official Acme owner fixture", async ({ page }) => {
  await page.context().addCookies([
    {
      url: process.env.CALDIY_WEB_URL ?? "http://localhost:3000",
      name: "calcom-timezone-dialog",
      value: "1"
    }
  ]);
  await new LoginPage(page).login("owner1-acme@example.com", "owner1-acme");
  await dismissTimezonePrompt(page);
  await mkdir(dirname(authState), { recursive: true });
  await page.context().storageState({ path: authState });
});
