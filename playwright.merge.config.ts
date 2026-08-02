import { defineConfig } from "@playwright/test";

export default defineConfig({
  reporter: [
    ["json", { outputFile: "test-results/e2e/playwright.json" }],
    ["junit", { outputFile: "test-results/e2e/junit.xml" }],
    ["allure-playwright", { resultsDir: "allure-results/playwright-e2e", detail: true }]
  ]
});
