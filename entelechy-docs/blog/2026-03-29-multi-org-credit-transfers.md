---
title: "What's New in Entelechy Cloud: Multi-Org Support and Credit Transfers"
authors: [entelechy]
date: 2026-03-29T12:00
tags: [entelechy-cloud, release, billing, organizations]
description: "Entelechy Cloud now supports multiple organizations per account and direct credit transfers between orgs — both available today."
image: /img/blog/entelechy-cloud-multi-org.png
hide_table_of_contents: true
---

![What's New in Entelechy Cloud: Multi-Org Support and Credit Transfers](/img/blog/entelechy-cloud-multi-org.png)

Two new features are live in [Entelechy Cloud](https://ui.mindmods.org/signup): multiple organizations per account and credit transfers between organizations you own.

<!-- truncate -->

## TL;DR

- **Multiple organizations** — create separate orgs for production and development, or for distinct projects, and switch between them instantly from the top nav
- **Credit transfers** — move credits between orgs you own directly from the Billing page; no support ticket required
- **Owner-only transfers** — only users who own both the source and destination organization can initiate a transfer
- **Available now** — in all Entelechy Cloud accounts

## Multiple Organizations

You can now create multiple organizations from the organization switcher in the top navigation bar. This is useful for:

- **Separating environments** — keep production and development memory banks in separate orgs with separate API keys, so a development agent can never affect production data
- **Distinct projects** — run completely separate Entelechy setups for different clients, codebases, or teams without any cross-contamination of memory banks or billing

To create a new organization, click your org name in the top navigation bar and select **New Organization**. Switching between organizations is instant — the dashboard, memory banks, API keys, and billing page all update to reflect the selected org.

## Credit Transfers Between Organizations

Owners can now transfer credits between organizations they own directly from the Billing page — no need to contact support.

Key details:

- **Atomic transfers** — credits move instantly; both organizations' balances update at the same time, with no intermediate state
- **Full transaction history** — the source organization records a `transfer_out` entry and the destination organization records a `transfer_in` entry, both visible on each org's billing page
- **Confirmation step** — a confirmation dialog shows the amount and destination organization before any funds move
- **Owner-only** — only users who own both the source and destination organization can initiate a transfer; Admins and Members cannot

To transfer credits, go to **Billing** in the source organization and select **Transfer Credits**.

[Learn more about credit transfers →](https://docs.mindmods.org/whats-new/)

## Get Started

Both features are available now in all [Entelechy Cloud](https://ui.mindmods.org/signup) accounts. Create a new organization from the org switcher, or head to your Billing page to transfer credits between existing organizations.
