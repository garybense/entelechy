import { NextRequest, NextResponse } from "next/server";
import { DATAPLANE_URL, getDataplaneHeaders } from "@/lib/entelechy-client";

/**
 * Server-side proxy from the admin UI to the dataplane's /ext/admin API.
 * The browser never sees the admin key: this route adds it. Access to this route
 * is already guarded by the Control Plane login (src/proxy.ts).
 */
async function forward(request: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  const target = `${DATAPLANE_URL}/ext/admin/${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`;
  const hasBody = !["GET", "HEAD", "DELETE"].includes(request.method);
  try {
    const res = await fetch(target, {
      method: request.method,
      headers: getDataplaneHeaders(hasBody ? { "Content-Type": "application/json" } : undefined),
      body: hasBody ? await request.text() : undefined,
      cache: "no-store",
    });
    if (res.status === 204) return new NextResponse(null, { status: 204 });
    return new NextResponse(await res.text(), {
      status: res.status,
      headers: { "Content-Type": res.headers.get("content-type") || "application/json" },
    });
  } catch (error) {
    console.error("Admin proxy error:", error);
    return NextResponse.json({ detail: "Admin API unreachable" }, { status: 502 });
  }
}

export const GET = forward;
export const POST = forward;
export const PATCH = forward;
export const PUT = forward;
export const DELETE = forward;
