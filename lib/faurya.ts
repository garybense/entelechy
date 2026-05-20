import { getFauryaClient, initFaurya } from "faurya";

let initialized = false;

export async function initFauryaClient() {
  if (initialized) return;
  if (typeof window === "undefined") return;

  installFauryaGlobal();

  const websiteId = process.env.FAURYA_SITE_ID;
  const domain = process.env.FAURYA_DOMAIN;

  if (!websiteId) {
    if (process.env.NODE_ENV !== "production") {
      console.warn("[Faurya] Missing FAURYA_SITE_ID. Add it to your env file.");
    }
    return;
  }

  initialized = true;

  await initFaurya({
    websiteId,
    domain,
    allowLocalhost: process.env.NODE_ENV !== "production",
  });

  flushQueuedFauryaEvents();
}

type FauryaEventMetadata = Record<string, unknown>;
type FauryaQueuedEvent = ArrayLike<unknown>;
type FauryaGlobal = ((eventName: string, metadata?: FauryaEventMetadata) => void) & {
  q?: FauryaQueuedEvent[];
};
type FauryaWindow = Window & { faurya?: FauryaGlobal };

export function trackFauryaEvent(eventName: string, metadata?: FauryaEventMetadata) {
  if (typeof window === "undefined") return;

  const client = getActiveFauryaClient();
  if (!client) {
    enqueueFauryaEvent(eventName, metadata);
    return;
  }

  if (metadata && Object.keys(metadata).length > 0) {
    client.trackGoal(eventName, metadata);
    return;
  }

  client.trackGoal(eventName);
}

function getActiveFauryaClient() {
  try {
    return getFauryaClient();
  } catch {
    return undefined;
  }
}

function installFauryaGlobal() {
  const target = window as FauryaWindow;
  const existingQueue = target.faurya?.q ?? [];
  const faurya = ((eventName: string, metadata?: FauryaEventMetadata) => {
    trackFauryaEvent(eventName, metadata);
  }) as FauryaGlobal;

  faurya.q = existingQueue;
  target.faurya = faurya;
}

function enqueueFauryaEvent(eventName: string, metadata?: FauryaEventMetadata) {
  const target = window as FauryaWindow;
  const faurya = target.faurya ?? (((queuedEventName: string, queuedMetadata?: FauryaEventMetadata) => {
    enqueueFauryaEvent(queuedEventName, queuedMetadata);
  }) as FauryaGlobal);

  faurya.q = faurya.q ?? [];
  faurya.q.push([eventName, metadata]);
  target.faurya = faurya;
}

function flushQueuedFauryaEvents() {
  const target = window as FauryaWindow;
  const faurya = target.faurya;
  if (!faurya) return;

  const queue = faurya.q ?? [];
  faurya.q = [];

  for (const queuedEvent of queue) {
    const eventName = queuedEvent[0];
    const metadata = queuedEvent[1];
    if (typeof eventName !== "string") continue;
    trackFauryaEvent(eventName, isFauryaEventMetadata(metadata) ? metadata : undefined);
  }
}

function isFauryaEventMetadata(value: unknown): value is FauryaEventMetadata {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
