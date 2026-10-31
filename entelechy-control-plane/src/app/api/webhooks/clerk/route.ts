import { Webhook } from "svix";
import { headers } from "next/headers";
import { WebhookEvent } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";
import { dataplaneBankUrl, getDataplaneHeaders } from "@/lib/entelechy-client";

export async function POST(req: Request) {
  const WEBHOOK_SECRET = process.env.CLERK_WEBHOOK_SECRET;

  if (!WEBHOOK_SECRET) {
    // If not configured, just return success during dev/sim
    console.log("No CLERK_WEBHOOK_SECRET found, skipping verification");
  }

  // Get the body
  const payload = await req.json();
  const body = JSON.stringify(payload);

  let evt: WebhookEvent;

  if (WEBHOOK_SECRET) {
    const headerPayload = await headers();
    const svix_id = headerPayload.get("svix-id");
    const svix_timestamp = headerPayload.get("svix-timestamp");
    const svix_signature = headerPayload.get("svix-signature");

    if (!svix_id || !svix_timestamp || !svix_signature) {
      return new Response("Error occured -- no svix headers", {
        status: 400,
      });
    }
    const wh = new Webhook(WEBHOOK_SECRET);
    try {
      evt = wh.verify(body, {
        "svix-id": svix_id,
        "svix-timestamp": svix_timestamp,
        "svix-signature": svix_signature,
      }) as WebhookEvent;
    } catch (err) {
      console.error("Error verifying webhook:", err);
      return new Response("Error occured", {
        status: 400,
      });
    }
  } else {
    // Mocking verification for dev if no secret
    evt = payload as WebhookEvent;
  }

  const { id } = evt.data;
  const eventType = evt.type;

  // Auto-provision a memory bank when a user signs up!
  if (eventType === "user.created") {
    const userId = evt.data.id;
    console.log(`Clerk Webhook: User Created! Auto-provisioning bank for user: ${userId}`);

    try {
      const res = await fetch(dataplaneBankUrl(userId), {
        method: "PUT",
        headers: getDataplaneHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          name: `Personal Bank`,
        }),
      });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${(await res.text()).slice(0, 300)}`);
      }
      console.log(`Successfully provisioned bank: ${userId}`);
    } catch (e) {
      console.error(`Failed to provision bank for ${userId}`, e);
    }
  }

  return NextResponse.json({ success: true });
}
