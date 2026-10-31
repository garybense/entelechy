import { timingSafeEqual } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";

/**
 * Optional HTTP Basic auth for the whole Control Plane.
 *
 * Enabled when ENTELECHY_CP_BASIC_AUTH_PASSWORD is set. The user name defaults
 * to "admin" (override with ENTELECHY_CP_BASIC_AUTH_USER). /api/health stays
 * open so platform healthchecks keep working. The dataplane API paths proxied by
 * next.config.ts (/v1, /mcp, /docs, /openapi.json, /version) skip Basic auth and
 * rely on ENTELECHY_API_TENANT_API_KEY instead. When the password is unset the
 * Control Plane behaves as before.
 */
function safeEqual(a: string, b: string): boolean {
  const ab = Buffer.from(a);
  const bb = Buffer.from(b);
  return ab.length === bb.length && timingSafeEqual(ab, bb);
}

/**
 * MCP connectors that cannot send an Authorization header (e.g. claude.ai custom
 * connectors) can use /mcp/<ENTELECHY_CP_MCP_URL_TOKEN>. The token in the URL is
 * the credential; the Control Plane forwards the request to the API's /mcp with
 * the dataplane API key attached. Plain /mcp keeps requiring the Bearer key.
 */
function mcpUrlToken(request: NextRequest): NextResponse | null {
  const { pathname, search } = request.nextUrl;
  if (pathname !== "/mcp" && !pathname.startsWith("/mcp/")) return null;

  const token = process.env.ENTELECHY_CP_MCP_URL_TOKEN;
  const apiKey = process.env.ENTELECHY_CP_DATAPLANE_API_KEY;
  const segments = pathname.split("/"); // ["", "mcp", "<token>", ...rest]
  if (!token || !apiKey || segments.length < 3 || !safeEqual(segments[2], token)) {
    return NextResponse.next(); // fall through to the API's own Bearer auth
  }

  const rest = segments.slice(3).join("/");
  const api = process.env.ENTELECHY_CP_DATAPLANE_API_URL || "http://localhost:8888";
  const headers = new Headers(request.headers);
  headers.set("authorization", `Bearer ${apiKey}`);
  return NextResponse.rewrite(new URL(`/mcp${rest ? `/${rest}` : ""}${search}`, api), {
    request: { headers },
  });
}

export function proxy(request: NextRequest) {
  const mcp = mcpUrlToken(request);
  if (mcp) return mcp;

  const password = process.env.ENTELECHY_CP_BASIC_AUTH_PASSWORD;
  if (!password) return NextResponse.next();

  const user = process.env.ENTELECHY_CP_BASIC_AUTH_USER || "admin";
  const header = request.headers.get("authorization") || "";

  if (header.startsWith("Basic ")) {
    const decoded = Buffer.from(header.slice(6), "base64").toString();
    const idx = decoded.indexOf(":");
    if (idx >= 0 && safeEqual(decoded.slice(0, idx), user) && safeEqual(decoded.slice(idx + 1), password)) {
      return NextResponse.next();
    }
  }

  return new NextResponse("Authentication required", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="Entelechy Control Plane", charset="UTF-8"' },
  });
}

export const config = {
  matcher: ["/((?!api/health|v1/|openapi.json|docs|version|_next/static|_next/image|favicon.ico).*)"],
};
