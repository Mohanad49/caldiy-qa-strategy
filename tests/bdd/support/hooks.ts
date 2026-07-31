import { After, Before, Status } from "@cucumber/cucumber";

import { LifecycleWorld } from "./world.ts";

Before(async function (this: LifecycleWorld, scenario) {
  await this.start(scenario.pickle.name);
});

After(async function (this: LifecycleWorld, scenario) {
  if (scenario.result?.status === Status.FAILED && this.page !== undefined) {
    await this.attach(await this.page.screenshot({ fullPage: true }), "image/png");
  }
  await this.stop();
});
