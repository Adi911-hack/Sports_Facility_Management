
import { NextRequest, NextResponse } from "next/server";

const FLASK_URL =
  process.env.FLASK_API_URL ?? "http://127.0.0.1:5000";

export async function POST(request: NextRequest) {
  // Reject cross-origin form submissions.
  const origin = request.headers.get("origin");

  if (origin && origin !== request.nextUrl.origin) {
    return new NextResponse("Forbidden", {
      status: 403,
    });
  }

  const form = await request.formData();

  const email = form.get("email");
  const password = form.get("password");

  if (
    typeof email !== "string" ||
    typeof password !== "string" ||
    email.length > 150 ||
    password.length > 128 ||
    !email.trim() ||
    !password
  ) {
    return NextResponse.redirect(
      new URL("/login?error=credentials", request.url),
      303
    );
  }

  try {
    const response = await fetch(
      `${FLASK_URL}/api/analytics/login`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email.trim(),
          password,
        }),
        cache: "no-store",
        signal: AbortSignal.timeout(8000),
      }
    );

    if (response.status === 401) {
      return NextResponse.redirect(
        new URL("/login?error=credentials", request.url),
        303
      );
    }

    if (!response.ok) {
      throw new Error("Flask login unavailable");
    }

    const data = await response.json();

    if (
      data.success !== true ||
      typeof data.token !== "string" ||
      !data.token
    ) {
      throw new Error("Invalid Flask login response");
    }

    const result = NextResponse.redirect(
      new URL("/", request.url),
      303
    );

    result.cookies.set("arena_admin_token", data.token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: 30 * 60,
    });

    return result;
  } catch {
    return NextResponse.redirect(
      new URL("/login?error=server", request.url),
      303
    );
  }
}
