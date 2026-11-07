import { Suspense } from "react";
import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

const FLASK_URL =
  process.env.FLASK_API_URL ?? "http://127.0.0.1:5000";

type SportData = {
  sport_name: string;
  booking_count: number;
};

type FacilityData = {
  facility_id: number;
  facility_name: string;
  booking_count: number;
};

type AnalyticsData = {
  success: boolean;
  admin_name: string;
  overview: {
    total_students: number;
    total_facilities: number;
    total_bookings: number;
    confirmed_bookings: number;
    total_tournaments: number;
    total_reviews: number;
    average_rating: number | null;
  };
  popular_sports: SportData[];
  facility_usage: FacilityData[];
  feedback_status: {
    OPEN: number;
    IN_PROGRESS: number;
    RESOLVED: number;
  };
};

async function getAnalytics(): Promise<
  AnalyticsData | null
> {
  const cookieStore = await cookies();

  const token = cookieStore.get(
    "arena_admin_token"
  )?.value;

  if (!token) {
    redirect("/login");
  }

  let response: Response;

  try {
    response = await fetch(
      `${FLASK_URL}/api/analytics/summary`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        cache: "no-store",
        signal: AbortSignal.timeout(10000),
      }
    );
  } catch {
    return null;
  }

  if (response.status === 401 || response.status === 403) {
    redirect("/login");
  }

  if (!response.ok) {
    return null;
  }

  try {
    const data: AnalyticsData = await response.json();

    return data.success ? data : null;
  } catch {
    return null;
  }
}

function MetricCard({
  label,
  value,
  detail,
  icon,
}: {
  label: string;
  value: string | number;
  detail: string;
  icon: string;
}) {
  return (
    <article className="rounded-2xl border border-[#27364b] bg-[#111d30] p-6">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-slate-400">{label}</p>
        <span className="text-2xl">{icon}</span>
      </div>

      <p className="mt-5 text-4xl font-extrabold text-white">
        {value}
      </p>

      <p className="mt-3 text-xs text-slate-500">
        {detail}
      </p>
    </article>
  );
}

function HorizontalBars({
  title,
  items,
}: {
  title: string;
  items: { label: string; count: number }[];
}) {
  const max = Math.max(
    1,
    ...items.map((item) => item.count)
  );

  return (
    <section className="rounded-2xl border border-[#27364b] bg-[#111d30] p-6">
      <h2 className="text-xl font-bold">{title}</h2>

      {items.length === 0 ? (
        <p className="mt-5 text-sm text-slate-400">
          No records available.
        </p>
      ) : (
        <div className="mt-7 space-y-6">
          {items.map((item) => (
            <div key={item.label}>
              <div className="mb-2 flex justify-between gap-3 text-sm">
                <span className="text-slate-300">
                  {item.label}
                </span>
                <span className="font-semibold text-white">
                  {item.count}
                </span>
              </div>

              <div className="h-2.5 overflow-hidden rounded-full bg-[#0b1526]">
                <div
                  className="h-full rounded-full bg-blue-500"
                  style={{
                    width: `${
                      (item.count / max) * 100
                    }%`,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

async function AnalyticsContent() {
  const analytics = await getAnalytics();

  if (!analytics) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#080f1d] px-6 text-white">
        <div className="max-w-md rounded-2xl border border-[#27364b] bg-[#111d30] p-8">
          <p className="text-sm font-bold text-blue-400">
            ARENA ANALYTICS
          </p>

          <h1 className="mt-4 text-2xl font-bold">
            Data temporarily unavailable
          </h1>

          <p className="mt-3 text-sm leading-6 text-slate-400">
            Check that Flask, MySQL and MongoDB
            are running. No placeholder values
            are being shown.
          </p>


<Link
  href="/"
  className="mt-6 inline-block rounded-lg bg-blue-600 px-4 py-3 text-sm font-bold"
>
  Retry
</Link>

        </div>
      </main>
    );
  }

  const {
    overview,
    popular_sports,
    facility_usage,
    feedback_status,
  } = analytics;

  const metrics = [
    {
      label: "Total Bookings",
      value: overview.total_bookings,
      icon: "📅",
      detail: "All booking records in MySQL",
    },
    {
      label: "Registered Students",
      value: overview.total_students,
      icon: "👥",
      detail: "Student accounts in MySQL",
    },
    {
      label: "Sports Facilities",
      value: overview.total_facilities,
      icon: "🏟️",
      detail: "Campus facilities",
    },
    {
      label: "Facility Reviews",
      value: overview.total_reviews,
      icon: "⭐",
      detail: "Reviews stored in MongoDB",
    },
  ];

  return (
    <main className="min-h-screen bg-[#080f1d] text-white">
      {/* HEADER */}
      <header className="border-b border-[#27364b] bg-[#0d1728]">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-600 text-xl font-black">
              A
            </div>

            <div>
              <h1 className="text-2xl font-black">
                ARENA
                <span className="text-blue-500">.</span>
              </h1>

              <p className="text-xs text-slate-400">
                Admin Analytics
              </p>
            </div>
          </div>

          <form
            action="/api/admin/logout"
            method="POST"
          >
            <button
              type="submit"
              className="rounded-lg border border-[#475569] px-4 py-2 text-sm font-semibold hover:bg-[#1e293b]"
            >
              Log Out
            </button>
          </form>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <div className="mx-auto max-w-7xl px-6 py-12">
        <div className="mb-10">
          <p className="text-sm font-bold tracking-[0.2em] text-blue-400">
            ARENA MANAGEMENT
          </p>

          <h2 className="mt-3 text-4xl font-extrabold md:text-5xl">
            Admin Analytics
          </h2>

          <p className="mt-4 text-slate-400">
            Welcome, {analytics.admin_name}.
            Here&apos;s your live campus sports overview.
          </p>
        </div>

        {/* LIVE METRICS */}
        <section className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric) => (
            <MetricCard
              key={metric.label}
              {...metric}
            />
          ))}
        </section>

        {/* SECONDARY METRICS */}
        <section className="mt-6 grid gap-5 sm:grid-cols-3">
          <MetricCard
            label="Confirmed Bookings"
            value={overview.confirmed_bookings}
            detail="Currently confirmed reservations"
            icon="✅"
          />

          <MetricCard
            label="Tournaments"
            value={overview.total_tournaments}
            detail="Tournament records in MySQL"
            icon="🏆"
          />

          <MetricCard
            label="Average Review Rating"
            value={
              overview.average_rating === null
                ? "No ratings"
                : `${overview.average_rating}/5`
            }
            detail="MongoDB review aggregation"
            icon="🌟"
          />
        </section>

        {/* MYSQL CHARTS */}
        <div className="mt-12">
          <h2 className="text-2xl font-bold">
            MySQL Booking Analytics
          </h2>

          <p className="mt-2 text-sm text-slate-400">
            Booking counts grouped by sport and facility.
          </p>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <HorizontalBars
            title="Popular Sports"
            items={popular_sports.map((item) => ({
              label: item.sport_name,
              count: item.booking_count,
            }))}
          />

          <HorizontalBars
            title="Facility Booking Counts"
            items={facility_usage.map((item) => ({
              label: item.facility_name,
              count: item.booking_count,
            }))}
          />
        </div>

        {/* MONGODB CHART */}
        <div className="mt-12">
          <h2 className="text-2xl font-bold">
            MongoDB Feedback Analytics
          </h2>

          <p className="mt-2 text-sm text-slate-400">
            Maintenance and review status distribution.
          </p>
        </div>

        <div className="mt-6">
          <HorizontalBars
            title="Feedback Status"
            items={[
              {
                label: "Open",
                count: feedback_status.OPEN,
              },
              {
                label: "In Progress",
                count: feedback_status.IN_PROGRESS,
              },
              {
                label: "Resolved",
                count: feedback_status.RESOLVED,
              },
            ]}
          />
        </div>

        <footer className="mt-16 border-t border-[#27364b] pt-7 text-center text-sm text-slate-500">
          ARENA — Sports Facility Management System
          <p className="mt-2">
            Next.js + Flask + MySQL + MongoDB
          </p>
        </footer>
      </div>
    </main>
  );
}

export default function Home() {
  return (
    <Suspense
      fallback={
        <main className="flex min-h-screen items-center justify-center bg-[#080f1d] px-6 text-white">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-blue-400">
              ARENA.
            </h1>
            <p className="mt-4 text-slate-400">
              Loading your analytics dashboard...
            </p>
          </div>
        </main>
      }
    >
      <AnalyticsContent />
    </Suspense>
  );
}
