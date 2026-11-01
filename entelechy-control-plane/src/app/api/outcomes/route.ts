import { NextRequest, NextResponse } from "next/server";
import { dataplaneBankUrl, getDataplaneHeaders } from "@/lib/entelechy-client";

/**
 * Write back the outcome of acting on a bootstrap policy.
 * Body: { bank_id, outcome: "success" | "failure", session_id?, policy?, score?, note? }
 */
export async function POST(request: NextRequest) {
  try {
    const { bank_id: bankId, ...payload } = await request.json();
    if (!bankId) {
      return NextResponse.json({ error: "bank_id is required" }, { status: 400 });
    }
    const response = await fetch(dataplaneBankUrl(bankId, "/outcomes"), {
      method: "POST",
      headers: getDataplaneHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    });
    const body = await response.json().catch(() => ({}));
    return NextResponse.json(body, { status: response.status });
  } catch (error) {
    console.error("Error writing outcome:", error);
    return NextResponse.json({ error: "Failed to write outcome" }, { status: 500 });
  }
}
