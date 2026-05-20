type FauryaGoalMetadata = Record<string, string>;

export interface FauryaGoalResponse {
  status: "success";
  data: Array<{
    message: string;
    eventId: string;
  }>;
}

export interface FauryaPaymentOptions {
  fauryaVisitorId?: string;
  email?: string;
  name?: string;
  customerId?: string;
  renewal?: boolean;
  refunded?: boolean;
  timestamp?: string;
}

export interface FauryaPaymentResponse {
  message: string;
  transaction_id: string;
}

const FAURYA_API_URL = "https://faurya.com/api/v1";
type FauryaServerProcess = { env?: Record<string, string | undefined> };

export async function createFauryaGoal(
  fauryaVisitorId: string,
  name: string,
  metadata?: FauryaGoalMetadata,
): Promise<FauryaGoalResponse> {
  return postFauryaApi<FauryaGoalResponse>("/goals", {
    faurya_visitor_id: fauryaVisitorId,
    name,
    ...(metadata ? { metadata } : {}),
  });
}

export async function createFauryaPayment(
  amount: number,
  currency: string,
  transactionId: string,
  options: FauryaPaymentOptions = {},
): Promise<FauryaPaymentResponse> {
  return postFauryaApi<FauryaPaymentResponse>("/payments", {
    amount,
    currency,
    transaction_id: transactionId,
    ...(options.fauryaVisitorId ? { faurya_visitor_id: options.fauryaVisitorId } : {}),
    ...(options.email ? { email: options.email } : {}),
    ...(options.name ? { name: options.name } : {}),
    ...(options.customerId ? { customer_id: options.customerId } : {}),
    ...(typeof options.renewal === "boolean" ? { renewal: options.renewal } : {}),
    ...(typeof options.refunded === "boolean" ? { refunded: options.refunded } : {}),
    ...(options.timestamp ? { timestamp: options.timestamp } : {}),
  });
}

async function postFauryaApi<TResponse>(
  path: string,
  body: Record<string, unknown>,
): Promise<TResponse> {
  const apiKey = getFauryaApiKey();

  const response = await fetch(`${FAURYA_API_URL}${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  const responseBody = await response.text();
  const parsed = responseBody ? parseFauryaApiResponse(responseBody) : undefined;

  if (!response.ok) {
    throw new Error(
      `[Faurya] API request failed with ${response.status}: ${responseBody || response.statusText}`,
    );
  }

  return parsed as TResponse;
}

function getFauryaApiKey(): string {
  const processEnv = (globalThis as typeof globalThis & { process?: FauryaServerProcess }).process?.env;
  const apiKey = processEnv?.FAURYA_API_KEY;

  if (!apiKey) {
    throw new Error("[Faurya] Missing FAURYA_API_KEY. Add it to your server env file.");
  }

  return apiKey;
}

function parseFauryaApiResponse(responseBody: string): unknown {
  try {
    return JSON.parse(responseBody);
  } catch {
    return responseBody;
  }
}
