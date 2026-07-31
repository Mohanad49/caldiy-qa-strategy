import { expect, type Page } from "@playwright/test";

export async function dismissTimezonePrompt(page: Page): Promise<void> {
  const dialog = page.getByRole("dialog", { name: "Want to update your timezone?" });
  try {
    await dialog.waitFor({ state: "visible", timeout: 5_000 });
  } catch (error) {
    if (error instanceof Error && error.name === "TimeoutError") return;
    throw error;
  }
  await dialog.getByRole("button", { name: "Don't update" }).click();
  await expect(dialog).toBeHidden();
}
