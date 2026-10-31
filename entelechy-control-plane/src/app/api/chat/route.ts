import { NextResponse } from "next/server";
import { dataplaneBankUrl, getDataplaneHeaders } from "@/lib/entelechy-client";

interface Stage {
  durationMs: number;
  payload: unknown;
  error?: string;
}

/** Call the dataplane and time it. Never invents a result: failures come back as `error`. */
async function call(url: string, body: unknown): Promise<Stage> {
  const start = Date.now();
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: getDataplaneHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
    });
    const text = await res.text();
    let payload: unknown = text;
    try {
      payload = JSON.parse(text);
    } catch {
      // keep the raw text
    }
    const durationMs = Date.now() - start;
    if (!res.ok) {
      return { durationMs, payload, error: `HTTP ${res.status}: ${text.slice(0, 500)}` };
    }
    return { durationMs, payload };
  } catch (e: any) {
    return { durationMs: Date.now() - start, payload: null, error: e?.message || "request failed" };
  }
}

export async function POST(req: Request) {
  try {
    const { messages, bankId } = await req.json();

    if (!bankId) {
      return NextResponse.json({ error: "bankId is required" }, { status: 400 });
    }

    const userPrompt: string = messages?.[messages.length - 1]?.content || "";
    if (!userPrompt) {
      return NextResponse.json({ error: "a user message is required" }, { status: 400 });
    }

    // 1. Session bootstrap: recall plus policy for this query.
    const bootstrap = await call(dataplaneBankUrl(bankId, "/sessions/bootstrap"), {
      svt: "CST-simulator",
      context: userPrompt,
    });
    const injectedPrompt =
      !bootstrap.error && (bootstrap.payload as any)?.injected_prompt
        ? String((bootstrap.payload as any).injected_prompt)
        : "";

    // 2. Reflect: the real answer from the bank's memories and the configured LLM.
    const reflect = await call(dataplaneBankUrl(bankId, "/reflect"), {
      query: userPrompt,
      max_tokens: 500,
    });
    const content: string = !reflect.error ? String((reflect.payload as any)?.text ?? "") : "";

    // 3. Retain the exchange, only when there was a real answer.
    let retain: Stage | null = null;
    if (content) {
      retain = await call(dataplaneBankUrl(bankId, "/memories"), {
        async: true,
        items: [
          {
            content: `User asked: "${userPrompt}". Assistant responded: "${content}".`,
            context: "chat_simulator",
          },
        ],
      });
    }

    const pipeline = {
      bootstrap: { ...bootstrap, injectedPrompt },
      response: reflect,
      retain_async: retain,
    };

    if (reflect.error || !content) {
      return NextResponse.json(
        { error: reflect.error || "reflect returned no text", pipeline },
        { status: 502 }
      );
    }
    return NextResponse.json({ content, pipeline });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
