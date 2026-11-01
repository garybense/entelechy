import { NextRequest, NextResponse } from "next/server";
import { dataplaneBankUrl, getDataplaneHeaders } from "@/lib/entelechy-client";

/** Policy history for a bank (bootstrap and distill), newest first. */
export async function GET(request: NextRequest) {
  try {
    const bankId = request.nextUrl.searchParams.get("bank_id");
    if (!bankId) {
      return NextResponse.json({ error: "bank_id is required" }, { status: 400 });
    }
    const limit = request.nextUrl.searchParams.get("limit") || "50";
    const response = await fetch(
      dataplaneBankUrl(bankId, `/policies?limit=${encodeURIComponent(limit)}`),
      { headers: getDataplaneHeaders(), cache: "no-store" }
    );
    const body = await response.json().catch(() => ({}));
    return NextResponse.json(body, { status: response.status });
  } catch (error) {
    console.error("Error listing policies:", error);
    return NextResponse.json({ error: "Failed to list policies" }, { status: 500 });
  }
}
