# Faurya Usage Guide

This project has Faurya browser initialization installed. Pageviews are captured automatically after `initFauryaClient()` runs.

Setup file: `lib/faurya.ts`

## Track Custom Goals

Use `trackFauryaEvent()` when a visitor completes an important action such as signing up, subscribing, or starting checkout.

```ts
import { trackFauryaEvent } from "./lib/faurya";

trackFauryaEvent("signup");

trackFauryaEvent("initiate_checkout", {
  product_id: "prod_123",
  plan_type: "pro",
  currency: "USD",
});
```

You can also call the browser global after Faurya is installed:

```ts
window.faurya?.("signup");
window.faurya?.("initiate_checkout", { product_id: "prod_123" });
```

## Goal Names

Use lowercase goal names with letters, numbers, underscores, or hyphens. Keep names short and descriptive, for example `signup`, `newsletter_subscribe`, or `initiate_checkout`.

## Metadata

Pass an optional object for custom parameters. Use lowercase property names with numbers, underscores, or hyphens. Keep values small and avoid sensitive data unless your own privacy policy allows it.

## What The CLI Added

- `initFauryaClient()` initializes the browser SDK once.
- `trackFauryaEvent()` sends manual custom goal events.
- `window.faurya()` is bridged to `trackFauryaEvent()` for script-style usage.
- Events called before initialization are queued and flushed after Faurya starts.

## Server API Helpers

Server API helper file: `lib/faurya-api.ts`

These helpers are for backend/server code only. The CLI adds `FAURYA_API_KEY=` to your env file when this option is selected. Keep that key on the server and do not expose it to client bundles.

### Create a custom goal

```ts
import { createFauryaGoal } from "./lib/faurya-api";

await createFauryaGoal(
  fauryaVisitorId,
  "newsletter_signup",
  {
    plan_type: "pro",
    source: "pricing_page",
  },
);
```

Required arguments: `fauryaVisitorId` and goal `name`. The metadata object is optional. The API key is read from `FAURYA_API_KEY`.

### Create a payment

```ts
import { createFauryaPayment } from "./lib/faurya-api";

await createFauryaPayment(
  29.99,
  "USD",
  "payment_456",
  {
    fauryaVisitorId,
    email: "customer@example.com",
    name: "Customer Name",
  },
);
```

Required arguments: `amount`, `currency`, and `transactionId`. Visitor ID and customer fields are optional, but visitor ID is recommended for attribution. The API key is read from `FAURYA_API_KEY`.
