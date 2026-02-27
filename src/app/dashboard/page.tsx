"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Video,
  Scissors,
  Clock,
  TrendingUp,
  Play,
  ArrowRight,
  AlertCircle,
} from "lucide-react";
import { getChannelStats, type ChannelStats } from "@/lib/api";
import { formatDuration, formatDate, getStatusColor, getCategoryColor } from "@/lib/utils";

export default function DashboardPage() {
  const [stats, setStats] = useState<ChannelStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getChannelStats()
      .then(setStats)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-red-600 border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-6">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-amber-600" />
            <div>
              <h3 className="font-medium text-amber-800">Backend not connected</h3>
              <p className="mt-1 text-sm text-amber-600">
                Make sure the Python backend is running on port 8000.
                Run: <code className="rounded bg-amber-100 px-1.5 py-0.5">cd backend && python run.py</code>
              </p>
            </div>
          </div>
        </div>

        {/* Still show dashboard structure */}
        <DashboardSkeleton />
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Overview of your YouTube automation pipeline
        </p>
      </div>

      {/* Stats Cards */}
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={<Video className="h-5 w-5 text-blue-600" />}
          label="Videos Processed"
          value={stats?.channel.total_videos ?? 0}
          bgColor="bg-blue-50"
        />
        <StatCard
          icon={<Scissors className="h-5 w-5 text-red-600" />}
          label="Shorts Generated"
          value={stats?.channel.total_shorts ?? 0}
          bgColor="bg-red-50"
        />
        <StatCard
          icon={<Clock className="h-5 w-5 text-green-600" />}
          label="Video Duration"
          value={formatDuration(stats?.total_video_duration)}
          bgColor="bg-green-50"
        />
        <StatCard
          icon={<TrendingUp className="h-5 w-5 text-purple-600" />}
          label="Shorts Duration"
          value={formatDuration(stats?.total_shorts_duration)}
          bgColor="bg-purple-50"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Recent Videos */}
        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Recent Videos</h2>
            <Link
              href="/videos"
              className="flex items-center gap-1 text-sm text-red-600 hover:text-red-700"
            >
              View all <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          {stats?.recent_videos && stats.recent_videos.length > 0 ? (
            <div className="space-y-3">
              {stats.recent_videos.map((video) => (
                <Link
                  key={video.id}
                  href={`/videos/${video.id}`}
                  className="flex items-center justify-between rounded-lg border border-gray-100 p-3 transition-colors hover:bg-gray-50"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100">
                      <Play className="h-4 w-4 text-gray-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {video.title}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatDate(video.created_at)}
                      </p>
                    </div>
                  </div>
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${getStatusColor(video.status)}`}
                  >
                    {video.status}
                  </span>
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState
              message="No videos yet"
              action={{ label: "Upload a video", href: "/upload" }}
            />
          )}
        </div>

        {/* Recent Shorts */}
        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Recent Shorts</h2>
          </div>
          {stats?.recent_shorts && stats.recent_shorts.length > 0 ? (
            <div className="space-y-3">
              {stats.recent_shorts.slice(0, 5).map((short) => (
                <div
                  key={short.id}
                  className="flex items-center justify-between rounded-lg border border-gray-100 p-3"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-50">
                      <Scissors className="h-4 w-4 text-red-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {short.title}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatDuration(short.duration)} &middot; From: {short.video_title}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {short.category && (
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${getCategoryColor(short.category)}`}
                      >
                        {short.category}
                      </span>
                    )}
                    <span className="text-xs font-medium text-gray-600">
                      {(short.score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              message="No shorts generated yet"
              action={{ label: "Upload & analyze a video", href: "/upload" }}
            />
          )}
        </div>
      </div>

      {/* Category Distribution */}
      {stats?.category_counts && Object.keys(stats.category_counts).length > 0 && (
        <div className="mt-6 rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">
            Shorts by Category
          </h2>
          <div className="flex flex-wrap gap-3">
            {Object.entries(stats.category_counts).map(([category, count]) => (
              <div
                key={category}
                className={`rounded-lg px-4 py-2 ${getCategoryColor(category)}`}
              >
                <span className="text-sm font-medium capitalize">{category}</span>
                <span className="ml-2 text-lg font-bold">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  bgColor,
}: {
  icon: React.ReactNode;
  label: string;
  value: number | string;
  bgColor: string;
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5">
      <div className="flex items-center gap-3">
        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${bgColor}`}>
          {icon}
        </div>
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
}

function EmptyState({
  message,
  action,
}: {
  message: string;
  action: { label: string; href: string };
}) {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <p className="text-sm text-gray-500">{message}</p>
      <Link
        href={action.href}
        className="mt-3 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
      >
        {action.label}
      </Link>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="mt-8">
      <h1 className="mb-8 text-2xl font-bold text-gray-900">Dashboard</h1>
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 animate-pulse rounded-xl border border-gray-200 bg-gray-100" />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="h-64 animate-pulse rounded-xl border border-gray-200 bg-gray-100" />
        <div className="h-64 animate-pulse rounded-xl border border-gray-200 bg-gray-100" />
      </div>
    </div>
  );
}
