"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Video,
  Play,
  Trash2,
  Clock,
  HardDrive,
  Monitor,
  Youtube,
  Upload,
  AlertCircle,
} from "lucide-react";
import { listVideos, deleteVideo, type Video as VideoType } from "@/lib/api";
import {
  formatDuration,
  formatFileSize,
  formatDate,
  getStatusColor,
} from "@/lib/utils";

export default function VideosPage() {
  const [videos, setVideos] = useState<VideoType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchVideos = () => {
    setLoading(true);
    listVideos()
      .then(setVideos)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchVideos();
  }, []);

  const handleDelete = async (id: string, title: string) => {
    if (!confirm(`Delete "${title}"? This will remove the video and all associated analysis data.`)) {
      return;
    }
    try {
      await deleteVideo(id);
      setVideos((prev) => prev.filter((v) => v.id !== id));
    } catch (e) {
      alert(e instanceof Error ? e.message : "Delete failed");
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Videos</h1>
          <p className="mt-1 text-sm text-gray-500">
            {videos.length} video{videos.length !== 1 ? "s" : ""} in your library
          </p>
        </div>
        <Link
          href="/upload"
          className="flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-red-700"
        >
          <Upload className="h-4 w-4" />
          Add Video
        </Link>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-24 animate-pulse rounded-xl border border-gray-200 bg-gray-100"
            />
          ))}
        </div>
      ) : error ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-6">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-amber-600" />
            <p className="text-sm text-amber-700">
              Could not connect to backend: {error}
            </p>
          </div>
        </div>
      ) : videos.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-gray-200 bg-white py-16">
          <Video className="mb-4 h-16 w-16 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-900">No videos yet</h3>
          <p className="mt-1 text-sm text-gray-500">
            Upload a video or paste a YouTube link to get started
          </p>
          <Link
            href="/upload"
            className="mt-4 rounded-lg bg-red-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-red-700"
          >
            Add Your First Video
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {videos.map((video) => (
            <div
              key={video.id}
              className="flex items-center gap-4 rounded-xl border border-gray-200 bg-white p-4 transition-shadow hover:shadow-sm"
            >
              {/* Thumbnail */}
              <Link
                href={`/videos/${video.id}`}
                className="flex h-20 w-32 flex-shrink-0 items-center justify-center rounded-lg bg-gray-100"
              >
                <Play className="h-8 w-8 text-gray-400" />
              </Link>

              {/* Info */}
              <div className="min-w-0 flex-1">
                <Link href={`/videos/${video.id}`}>
                  <h3 className="truncate text-sm font-semibold text-gray-900 hover:text-red-600">
                    {video.title}
                  </h3>
                </Link>
                <div className="mt-1.5 flex flex-wrap items-center gap-3 text-xs text-gray-500">
                  <span className="flex items-center gap-1">
                    {video.source_type === "youtube" ? (
                      <Youtube className="h-3.5 w-3.5 text-red-500" />
                    ) : (
                      <Upload className="h-3.5 w-3.5" />
                    )}
                    {video.source_type === "youtube" ? "YouTube" : "Upload"}
                  </span>
                  {video.duration && (
                    <span className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5" />
                      {formatDuration(video.duration)}
                    </span>
                  )}
                  {video.resolution && (
                    <span className="flex items-center gap-1">
                      <Monitor className="h-3.5 w-3.5" />
                      {video.resolution}
                    </span>
                  )}
                  {video.file_size && (
                    <span className="flex items-center gap-1">
                      <HardDrive className="h-3.5 w-3.5" />
                      {formatFileSize(video.file_size)}
                    </span>
                  )}
                  <span className="text-gray-400">
                    {formatDate(video.created_at)}
                  </span>
                </div>
                {video.error_message && (
                  <p className="mt-1 text-xs text-red-500">{video.error_message}</p>
                )}
              </div>

              {/* Status & Actions */}
              <div className="flex items-center gap-3">
                <span
                  className={`whitespace-nowrap rounded-full px-3 py-1 text-xs font-medium ${getStatusColor(video.status)}`}
                >
                  {video.status.replace("_", " ")}
                </span>
                <button
                  onClick={() => handleDelete(video.id, video.title)}
                  className="rounded-lg p-2 text-gray-400 transition-colors hover:bg-red-50 hover:text-red-600"
                  title="Delete video"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
