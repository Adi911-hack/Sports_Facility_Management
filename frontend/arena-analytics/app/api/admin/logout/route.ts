
import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  const origin = request.headers.get("origin");

  if (origin && origin !== request.nextUrl.origin) {
    return new NextResponse("Forbidden", {
      status: 403,
    });
  }

  const response = NextResponse.redirect(
    new URL("/login", request.url),
    303
  );

  response.cookies.set("arena_admin_token", "", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });

  return response;
}
