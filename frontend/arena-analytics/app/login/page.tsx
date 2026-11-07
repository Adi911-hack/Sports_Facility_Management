
import { Suspense } from "react";

async function LoginForm({
  searchParams,
}: {
  searchParams: Promise<{
    error?: string;
  }>;
}) {
  const params = await searchParams;

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#080f1d] px-5 text-white">
      <div className="w-full max-w-md rounded-2xl border border-[#27364b] bg-[#111d30] p-9 shadow-2xl">
        <div className="mb-9">
          <p className="text-sm font-black tracking-[0.3em] text-blue-400">
            ARENA.
          </p>

          <p className="mt-4 text-xs font-bold tracking-[0.15em] text-blue-400">
            ADMIN ACCESS
          </p>

          <h1 className="mt-3 text-3xl font-extrabold">
            Welcome back.
          </h1>

          <p className="mt-3 text-sm leading-6 text-slate-400">
            Sign in with your existing ARENA administrator
            account to access live analytics.
          </p>
        </div>

        {params.error === "credentials" && (
          <div
            role="alert"
            className="mb-5 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300"
          >
            Invalid admin credentials.
          </div>
        )}

        {params.error === "server" && (
          <div
            role="alert"
            className="mb-5 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-200"
          >
            Flask login service is unavailable. Check that
            the backend is running.
          </div>
        )}

        <form
          action="/api/admin/login"
          method="POST"
          className="space-y-5"
        >
          <div>
            <label
              htmlFor="email"
              className="mb-2 block text-sm font-semibold"
            >
              Admin Email
            </label>

            <input
              id="email"
              type="email"
              name="email"
              autoComplete="username"
              placeholder="admin@arena.test"
              maxLength={150}
              required
              className="w-full rounded-lg border border-[#304158] bg-[#0b1526] px-4 py-3 text-white outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-2 block text-sm font-semibold"
            >
              Password
            </label>

            <input
              id="password"
              type="password"
              name="password"
              autoComplete="current-password"
              required
              className="w-full rounded-lg border border-[#304158] bg-[#0b1526] px-4 py-3 text-white outline-none focus:border-blue-500"
            />
          </div>

          <button
            type="submit"
            className="w-full rounded-lg bg-blue-600 px-5 py-3 font-bold text-white hover:bg-blue-700"
          >
            Access Analytics →
          </button>
        </form>

        <p className="mt-7 text-center text-xs text-slate-500">
          Authorized ARENA administrators only
        </p>
      </div>
    </main>
  );
}

export default function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  return (
    <Suspense
      fallback={
        <main className="flex min-h-screen items-center justify-center bg-[#080f1d] text-white">
          Loading ARENA Admin Login...
        </main>
      }
    >
      <LoginForm searchParams={searchParams} />
    </Suspense>
  );
}
