import { expect, test } from "../browser/fixtures.js";
import { LoginPage } from "../browser/pages/login-page.js";

test("@firefox seeded user can log in through the credential form", async ({ guestPage }) => {
  await new LoginPage(guestPage).login("owner1-acme@example.com", "owner1-acme");
  await expect(guestPage.getByTestId("dashboard-shell")).toBeVisible();
});

test("registration completes and the account is removed when public signup is enabled", async ({
  guestPage,
  mailpit
}, testInfo) => {
  const response = await guestPage.goto("/signup");
  test.skip(response?.status() === 404, "Public registration is not enabled in this runtime");

  const continueWithEmail = guestPage.getByTestId("continue-with-email-button");
  test.skip(!(await continueWithEmail.isVisible().catch(() => false)), "Public registration is disabled");
  await continueWithEmail.click();

  const token = `qa-signup-${testInfo.workerIndex}-${Date.now()}`.toLowerCase();
  const email = `${token}@example.com`;
  const password = "Phase3Password99!";
  const signupStartedAt = new Date();
  await guestPage.locator('input[name="username"]').fill(token);
  await guestPage.locator('input[name="email"]').fill(email);
  await guestPage.locator('input[name="password"]').fill(password);
  const signupResponsePromise = guestPage.waitForResponse(
    (signupResponse) =>
      signupResponse.url().includes("/api/auth/signup") && signupResponse.request().method() === "POST"
  );
  await guestPage.getByTestId("signup-submit-button").click();
  const signupResponse = await signupResponsePromise;
  expect(signupResponse.status(), await signupResponse.text()).toBe(201);
  await expect(guestPage).toHaveURL(/\/auth\/verify-email/);

  const verificationMessage = await mailpit.waitForMessage(
    email,
    (message) => message.Subject.includes("Verify your account"),
    { after: signupStartedAt }
  );
  const verificationURL = mailpit
    .body(verificationMessage)
    .match(/http:\/\/localhost:3000\/api\/auth\/verify-email\?token=[a-f0-9]+/)?.[0];
  expect(verificationURL, "Verification email did not contain a local token URL").toBeDefined();
  await guestPage.goto(verificationURL as string);
  await guestPage.context().clearCookies();
  await new LoginPage(guestPage).login(email, password);

  // A new account is held in onboarding, so the profile deletion screen is
  // unreachable. Use Cal.diy's authenticated account-deletion mutation for
  // teardown instead of leaving the registration fixture behind.
  const deleteResponse = await guestPage.request.post("/api/trpc/me/deleteMe?batch=1", {
    data: { "0": { json: { password } } }
  });
  expect(deleteResponse.ok(), await deleteResponse.text()).toBeTruthy();
  await guestPage.context().clearCookies();
});
