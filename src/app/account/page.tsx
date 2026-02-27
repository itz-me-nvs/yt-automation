"use client";

import { useEffect, useState } from "react";
import {
  User,
  Settings,
  Save,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Youtube,
  Video,
  Scissors,
  Clock,
} from "lucide-react";
import {
  getChannelInfo,
  updateChannelInfo,
  getChannelStats,
  type ChannelInfo,
  type ChannelStats,
} from "@/lib/api";
import { formatDuration } from "@/lib/utils";

export default function AccountPage() {
  const [channelInfo, setChannelInfo] = useState<ChannelInfo | null>(null);
  const [stats, setStats] = useState<ChannelStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Form state
  const [channelName, setChannelName] = useState("");
  const [channelUrl, setChannelUrl] = useState("");
  const [shortDuration, setShortDuration] = useState(60);
  const [minScore, setMinScore] = useState(0.5);
  const [autoGenerate, setAutoGenerate] = useState(true);

  useEffect(() => {
    Promise.all([getChannelInfo(), getChannelStats()])
      .then(([info, s]) => {
        setChannelInfo(info);
        setStats(s);
        setChannelName(info.channel_name || "");
        setChannelUrl(info.channel_url || "");
        setShortDuration(
          (info.settings.default_short_duration as number) || 60
        );
        setMinScore(
          (info.settings.min_highlight_score as number) || 0.5
        );
        setAutoGenerate(
          (info.settings.auto_generate_shorts as boolean) ?? true
        );
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaveSuccess(false);
    try {
      const updated = await updateChannelInfo({
        channel_name: channelName,
        channel_url: channelUrl,
        settings: {
          default_short_duration: shortDuration,
          min_highlight_score: minScore,
          auto_generate_shorts: autoGenerate,
        },
      });
      setChannelInfo(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-red-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Account & Settings</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage your channel settings and ML pipeline configuration
        </p>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 p-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-amber-600" />
            <p className="text-sm text-amber-700">{error}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Stats Sidebar */}
        <div className="space-y-4">
          <div className="rounded-xl border border-gray-200 bg-white p-6">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
              <Youtube className="h-8 w-8 text-red-600" />
            </div>
            <h2 className="text-lg font-bold text-gray-900">
              {channelInfo?.channel_name || "My Channel"}
            </h2>
            {channelInfo?.channel_url && (
              <p className="mt-1 truncate text-sm text-gray-500">{channelInfo.channel_url}</p>
            )}
          </div>

          <div className="space-y-3">
            <StatCard
              icon={<Video className="h-5 w-5 text-blue-600" />}
              label="Videos Processed"
              value={stats?.channel.total_videos ?? 0}
            />
            <StatCard
              icon={<Scissors className="h-5 w-5 text-red-600" />}
              label="Shorts Generated"
              value={stats?.channel.total_shorts ?? 0}
            />
            <StatCard
              icon={<Clock className="h-5 w-5 text-green-600" />}
              label="Total Video Time"
              value={formatDuration(stats?.total_video_duration)}
            />
            <StatCard
              icon={<Clock className="h-5 w-5 text-purple-600" />}
              label="Total Shorts Time"
              value={formatDuration(stats?.total_shorts_duration)}
            />
          </div>
        </div>

        {/* Settings Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Channel Settings */}
          <div className="rounded-xl border border-gray-200 bg-white p-6">
            <div className="mb-4 flex items-center gap-2">
              <User className="h-5 w-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-900">Channel Details</h2>
            </div>

            <div className="space-y-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  Channel Name
                </label>
                <input
                  type="text"
                  value={channelName}
                  onChange={(e) => setChannelName(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
                  placeholder="My YouTube Channel"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  Channel URL
                </label>
                <input
                  type="url"
                  value={channelUrl}
                  onChange={(e) => setChannelUrl(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
                  placeholder="https://youtube.com/@yourchannel"
                />
              </div>
            </div>
          </div>

          {/* ML Pipeline Settings */}
          <div className="rounded-xl border border-gray-200 bg-white p-6">
            <div className="mb-4 flex items-center gap-2">
              <Settings className="h-5 w-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-900">
                ML Pipeline Configuration
              </h2>
            </div>

            <div className="space-y-5">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  Max Short Duration (seconds)
                </label>
                <input
                  type="range"
                  min={15}
                  max={60}
                  step={5}
                  value={shortDuration}
                  onChange={(e) => setShortDuration(parseInt(e.target.value))}
                  className="w-full accent-red-600"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>15s</span>
                  <span className="font-medium text-red-600">{shortDuration}s</span>
                  <span>60s</span>
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  Minimum Highlight Score
                </label>
                <input
                  type="range"
                  min={0.1}
                  max={0.9}
                  step={0.1}
                  value={minScore}
                  onChange={(e) => setMinScore(parseFloat(e.target.value))}
                  className="w-full accent-red-600"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>0.1 (more shorts)</span>
                  <span className="font-medium text-red-600">{minScore.toFixed(1)}</span>
                  <span>0.9 (fewer, better)</span>
                </div>
              </div>

              <div className="flex items-center justify-between rounded-lg border border-gray-200 p-4">
                <div>
                  <p className="text-sm font-medium text-gray-700">
                    Auto-generate Shorts
                  </p>
                  <p className="text-xs text-gray-500">
                    Automatically create short clips after analysis completes
                  </p>
                </div>
                <button
                  onClick={() => setAutoGenerate(!autoGenerate)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    autoGenerate ? "bg-red-600" : "bg-gray-300"
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      autoGenerate ? "translate-x-6" : "translate-x-1"
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* ML Tools Info */}
          <div className="rounded-xl border border-gray-200 bg-white p-6">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">
              ML Tools (Local & Free)
            </h2>
            <div className="space-y-3">
              <ToolRow
                name="OpenAI Whisper"
                description="Speech-to-text transcription"
                model="whisper-base (74M params)"
              />
              <ToolRow
                name="CLIP (ViT-B/32)"
                description="Visual frame classification"
                model="clip-vit-base-patch32"
              />
              <ToolRow
                name="Ollama + LLaMA"
                description="Content analysis & summarization"
                model="llama3.2 (local LLM)"
              />
              <ToolRow
                name="librosa"
                description="Audio energy & feature analysis"
                model="Signal processing"
              />
              <ToolRow
                name="PySceneDetect"
                description="Scene boundary detection"
                model="ContentDetector (HSV)"
              />
              <ToolRow
                name="FFmpeg"
                description="Video processing & Shorts generation"
                model="9:16 vertical format"
              />
            </div>
          </div>

          {/* Save Button */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 rounded-lg bg-red-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
            >
              {saving ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              Save Settings
            </button>
            {saveSuccess && (
              <span className="flex items-center gap-1 text-sm text-green-600">
                <CheckCircle2 className="h-4 w-4" /> Settings saved!
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: number | string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white p-4">
      {icon}
      <div>
        <p className="text-xs text-gray-500">{label}</p>
        <p className="text-lg font-bold text-gray-900">{value}</p>
      </div>
    </div>
  );
}

function ToolRow({
  name,
  description,
  model,
}: {
  name: string;
  description: string;
  model: string;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg bg-gray-50 p-3">
      <div>
        <p className="text-sm font-medium text-gray-900">{name}</p>
        <p className="text-xs text-gray-500">{description}</p>
      </div>
      <span className="rounded-full bg-white px-3 py-1 text-xs font-medium text-gray-600">
        {model}
      </span>
    </div>
  );
}
