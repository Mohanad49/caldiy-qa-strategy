import { Given, Then, When } from "@cucumber/cucumber";
import { expect } from "@playwright/test";

import { firstEventType } from "../../browser/fixture-manager.ts";
import { LifecycleWorld } from "../support/world.ts";

Given("an isolated Cal.diy event is available", async function (this: LifecycleWorld) {
  const manager = this.required(this.fixtureManager, "fixture manager");
  this.manifest = await manager.create();
  this.event = firstEventType(this.manifest);
});

Given("a confirmed guest booking exists", async function (this: LifecycleWorld) {
  const manager = this.required(this.fixtureManager, "fixture manager");
  this.manifest = await manager.create();
  this.event = firstEventType(this.manifest);
  const bookingPage = this.required(this.bookingPage, "booking page");
  const attendee = this.required(this.attendee, "attendee");
  await bookingPage.open(this.event.bookingPath);
  await bookingPage.chooseFirstSlotNextMonth();
  this.bookingUid = await bookingPage.book(attendee);
  manager.trackBooking(this.manifest, this.bookingUid);
});

When("a guest books the event", async function (this: LifecycleWorld) {
  const event = this.required(this.event, "event");
  const bookingPage = this.required(this.bookingPage, "booking page");
  const attendee = this.required(this.attendee, "attendee");
  const manifest = this.required(this.manifest, "manifest");
  const manager = this.required(this.fixtureManager, "fixture manager");
  this.actionAt = new Date();
  await bookingPage.open(event.bookingPath);
  await bookingPage.chooseFirstSlotNextMonth();
  this.bookingUid = await bookingPage.book(attendee);
  manager.trackBooking(manifest, this.bookingUid);
});

When("the guest reschedules the booking", async function (this: LifecycleWorld) {
  const bookingPage = this.required(this.bookingPage, "booking page");
  const originalUid = this.required(this.bookingUid, "booking UID");
  const manifest = this.required(this.manifest, "manifest");
  const manager = this.required(this.fixtureManager, "fixture manager");
  this.actionAt = new Date();
  this.replacementUid = await bookingPage.reschedule(originalUid);
  manager.trackBooking(manifest, this.replacementUid);
});

When("the guest cancels the booking", async function (this: LifecycleWorld) {
  const bookingPage = this.required(this.bookingPage, "booking page");
  this.actionAt = new Date();
  await bookingPage.cancel("Phase 3 BDD cancellation");
});

Then("the booking confirmation is shown", async function (this: LifecycleWorld) {
  await expect(this.required(this.page, "page").getByTestId("success-page")).toBeVisible();
  expect(this.required(this.bookingUid, "booking UID")).not.toHaveLength(0);
});

Then("the replacement booking confirmation is shown", async function (this: LifecycleWorld) {
  await expect(this.required(this.page, "page").getByTestId("success-page")).toBeVisible();
  expect(this.required(this.replacementUid, "replacement UID")).not.toBe(
    this.required(this.bookingUid, "booking UID")
  );
});

Then("the cancellation confirmation is shown", async function (this: LifecycleWorld) {
  await expect(this.required(this.page, "page").getByTestId("cancelled-headline")).toBeVisible();
});

Then("a correlated confirmation email is delivered", async function (this: LifecycleWorld) {
  await expectCorrelatedEmail(this, "confirm");
});

Then("a correlated rescheduling email is delivered", async function (this: LifecycleWorld) {
  await expectCorrelatedEmail(this, "reschedul");
});

Then("a correlated cancellation email is delivered", async function (this: LifecycleWorld) {
  await expectCorrelatedEmail(this, "cancel");
});

async function expectCorrelatedEmail(world: LifecycleWorld, lifecycleText: string): Promise<void> {
  const attendee = world.required(world.attendee, "attendee");
  const event = world.required(world.event, "event");
  const actionAt = world.required(world.actionAt, "action timestamp");
  const isInitialConfirmation = lifecycleText === "confirm";
  const message = await world.mailpit.waitForMessage(
    isInitialConfirmation ? "owner1-acme@example.com" : attendee.email,
    (candidate) => {
      const body = world.mailpit.body(candidate).toLowerCase();
      return (
        body.includes(event.title.toLowerCase()) &&
        body.includes(attendee.email) &&
        body.includes(lifecycleText)
      );
    },
    { after: actionAt }
  );
  expect(world.mailpit.body(message).toLowerCase()).toContain(lifecycleText);
}
