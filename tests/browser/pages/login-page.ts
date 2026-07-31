import { expect, type Page } from "@playwright/test";

export class LoginPage {
  constructor(private readonly page: Page) {}

  async login(email: string, password: string): Promise<void> {
    await this.page.goto("/auth/login");
    const form = this.page.getByTestId("login-form");
    await expect(form).toBeVisible();
    await form.locator("#email").fill(email);
    await form.locator("#password").fill(password);
    const response = this.page.waitForResponse(/\/api\/auth\/callback\/credentials/);
    await form.locator('[type="submit"]').click();
    const loginResponse = await response;
    expect(loginResponse.ok()).toBeTruthy();
    await expect(this.page).not.toHaveURL(/\/auth\/login/);
  }
}
