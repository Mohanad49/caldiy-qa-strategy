import { defineConfig, devices } from "@playwright/test";

const webPort = process.env.CALDIY_WEB_PORT ?? "3000";
const baseURL = process.env.CALDIY_WEB_URL ?? `http://localhost:${webPort}`;
const authState = "test-results/auth/owner1-acme.json";

export default defineConfig({
  testDir: ".",
  outputDir: "test-results/playwright/artifacts",
  fullyParallel: true,
  forbidOnly: true,
  retries: 0,
  workers: process.env.CI ? 4 : 2,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [
    ["list"],
    ["junit", { outputFile: process.env.PLAYWRIGHT_JUNIT_OUTPUT ?? "test-results/playwright/junit.xml" }],
    ["allure-playwright", { resultsDir: "allure-results/playwright", detail: true }]
  ],
  use: {
    baseURL,
    locale: "en-US",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure"
  },
  snapshotPathTemplate: "{testDir}/__screenshots__/{platform}/{testFilePath}/{arg}{ext}",
  projects: [
    {
      name: "auth-setup",
      testMatch: /tests\/browser\/auth\.setup\.ts/,
      use: { ...devices["Desktop Chrome"] }
    },
    {
      name: "chromium-e2e",
      testMatch: /tests\/e2e\/.*\.spec\.ts/,
      dependencies: ["auth-setup"],
      use: { ...devices["Desktop Chrome"], storageState: authState }
    },
    {
      name: "firefox-lifecycle",
      testMatch: /tests\/e2e\/.*\.spec\.ts/,
      grep: /@firefox/,
      dependencies: ["auth-setup"],
      use: { ...devices["Desktop Firefox"], storageState: authState }
    },
    {
      name: "chromium-timezones",
      testMatch: /tests\/timezones\/.*\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] }
    },
    {
      name: "chromium-a11y",
      testMatch: /tests\/a11y\/.*\.spec\.ts/,
      use: {
        ...devices["Desktop Chrome"],
        colorScheme: "light",
        contextOptions: { reducedMotion: "reduce" }
      }
    },
    {
      name: "chromium-visual",
      testMatch: /tests\/visual\/.*\.spec\.ts/,
      use: { ...devices["Desktop Chrome"], colorScheme: "light" }
    }
  ]
});
