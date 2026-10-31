import { timingSafeEqual } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";

/**
 * Optional HTTP Basic auth for the whole Control Plane.
 *
 * Enabled when ENTELECHY_CP_BASIC_AUTH_PASSWORD is set. The user name defaults
 * to "admin" (override with ENTELECHY_CP_BASIC_AUTH_USER). /api/health stays
 * open so platform healthchecks keep working. When the password is unset the
 * Control Plane behaves as before.
 */
function safeEqual(a: string, b: string): boolean {
  const ab = Buffer.from(a);
  const bb = Buffer.from(b);
  return ab.length === bb.length && timingSafeEqual(ab, bb);
}

export function proxy(request: NextRequest) {
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
  matcher: ["/((?!api/health|_next/static|_next/image|favicon.ico).*)"],
};
