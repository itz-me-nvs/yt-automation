"use client";

import { useEffect, useState, useCallback, use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Play,
  Loader2,
  Scissors,
  BarChart3,
  FileText,
  Music,
  Smile,
  Zap,
  Clock,
  Star,
  AlertCircle,
  RefreshCw,
  Palette,
  Sparkles,
  RotateCw,
} from "lucide-react";
import {
  getVideo,
  startAnalysis,
  getAnalysisProgress,
  getAnalysisResults,
  getTemplateSuggestions,
  listTemplates,
  regenerateShort,
  type Video,
  type AnalysisResult,
  type AnalysisProgress,
  type Short,
  type Highlight,
  type Template,
  type TemplateSuggestion,
} from "@/lib/api";
import {
  formatDuration,
  formatFileSize,
  formatDate,
  getStatusColor,
  getCategoryColor,
  cn,
} from "@/lib/utils";

type Tab = "overview" | "highlights" | "transcript" | "emotions" | "shorts" | "energy";

export default function VideoDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [video, setVideo] = useState<Video | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [shorts, setShorts] = useState<Short[]>([]);
  const [progress, setProgress] = useState<AnalysisProgress | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const v = await getVideo(id);
      setVideo(v);

      if (v.status === "completed") {
        try {
          const results = await getAnalysisResults(id);
          setAnalysis(results.analysis);
          setShorts(results.shorts);
        } catch {
          // No analysis results yet
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load video");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Poll progress while analyzing
  useEffect(() => {
    if (!analyzing) return;
    const interval = setInterval(async () => {
      try {
        const p = await getAnalysisProgress(id);
        setProgress(p);
        if (p.stage === "completed") {
          setAnalyzing(false);
          fetchData();
        } else if (p.stage === "error") {
          setAnalyzing(false);
          setError(p.message);
        }
      } catch {
        // Ignore polling errors
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [analyzing, id, fetchData]);

  const handleStartAnalysis = async () => {
    setAnalyzing(true);
    setError(null);
    try {
      await startAnalysis(id);
    } catch (e) {
      setAnalyzing(false);
      setError(e instanceof Error ? e.message : "Failed to start analysis");
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-red-600 border-t-transparent" />
      </div>
    );
  }

  if (error && !video) {
    return (
      <div className="p-8">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6">
          <p className="text-red-700">{error}</p>
          <Link href="/videos" className="mt-2 inline-block text-sm text-red-600 underline">
            Back to videos
          </Link>
        </div>
      </div>
    );
  }

  if (!video) return null;

  const tabs: { key: Tab; label: string; icon: React.ReactNode; count?: number }[] = [
    { key: "overview", label: "Overview", icon: <BarChart3 className="h-4 w-4" /> },
    {
      key: "highlights",
      label: "Highlights",
      icon: <Star className="h-4 w-4" />,
      count: analysis?.highlights.length,
    },
    { key: "transcript", label: "Transcript", icon: <FileText className="h-4 w-4" /> },
    {
      key: "emotions",
      label: "Emotions",
      icon: <Smile className="h-4 w-4" />,
      count: analysis?.emotions.length,
    },
    { key: "energy", label: "Audio Energy", icon: <Music className="h-4 w-4" /> },
    {
      key: "shorts",
      label: "Shorts",
      icon: <Scissors className="h-4 w-4" />,
      count: shorts.length,
    },
  ];

  return (
    <div className="p-8">
      {/* Back button */}
      <Link
        href="/videos"
        className="mb-4 inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
      >
        <ArrowLeft className="h-4 w-4" /> Back to videos
      </Link>

      {/* Video Header */}
      <div className="mb-6 rounded-xl border border-gray-200 bg-white p-6">
        <div className="flex items-start gap-6">
          <div className="flex h-24 w-40 flex-shrink-0 items-center justify-center rounded-lg bg-gray-100">
            <Play className="h-10 w-10 text-gray-400" />
          </div>
          <div className="flex-1">
            <h1 className="text-xl font-bold text-gray-900">{video.title}</h1>
            <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-gray-500">
              <span className={`rounded-full px-3 py-0.5 text-xs font-medium ${getStatusColor(video.status)}`}>
                {video.status.replace("_", " ")}
              </span>
              {video.duration && (
                <span className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {formatDuration(video.duration)}
                </span>
              )}
              {video.resolution && <span>{video.resolution}</span>}
              {video.file_size && <span>{formatFileSize(video.file_size)}</span>}
              <span>{formatDate(video.created_at)}</span>
            </div>
            {video.source_url && (
              <p className="mt-1 truncate text-xs text-gray-400">{video.source_url}</p>
            )}
          </div>

          {/* Action Button */}
          <div>
            {video.status === "pending" && !analyzing && (
              <button
                onClick={handleStartAnalysis}
                className="flex items-center gap-2 rounded-lg bg-red-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-red-700"
              >
                <Zap className="h-4 w-4" />
                Analyze Video
              </button>
            )}
            {video.status === "completed" && (
              <button
                onClick={handleStartAnalysis}
                className="flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                <RefreshCw className="h-4 w-4" />
                Re-analyze
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Analysis Progress */}
      {analyzing && progress && (
        <div className="mb-6 rounded-xl border border-purple-200 bg-purple-50 p-6">
          <div className="flex items-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin text-purple-600" />
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-purple-900">
                  {progress.stage.replace("_", " ").toUpperCase()}
                </p>
                <span className="text-sm text-purple-600">
                  {(progress.progress * 100).toFixed(0)}%
                </span>
              </div>
              <p className="mt-0.5 text-xs text-purple-700">{progress.message}</p>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-purple-200">
                <div
                  className="h-full rounded-full bg-purple-600 transition-all"
                  style={{ width: `${progress.progress * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      {analysis && (
        <>
          <div className="mb-6 flex gap-1 overflow-x-auto border-b border-gray-200">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={cn(
                  "flex items-center gap-2 whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition-colors",
                  activeTab === tab.key
                    ? "border-red-600 text-red-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                )}
              >
                {tab.icon}
                {tab.label}
                {tab.count !== undefined && tab.count > 0 && (
                  <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs">
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          {activeTab === "overview" && <OverviewTab analysis={analysis} shorts={shorts} />}
          {activeTab === "highlights" && <HighlightsTab highlights={analysis.highlights} />}
          {activeTab === "transcript" && <TranscriptTab transcript={analysis.transcript} />}
          {activeTab === "emotions" && <EmotionsTab emotions={analysis.emotions} />}
          {activeTab === "energy" && <EnergyTab energy={analysis.audio_energy} />}
          {activeTab === "shorts" && <ShortsTab shorts={shorts} videoId={id} />}
        </>
      )}

      {/* No analysis yet */}
      {!analysis && !analyzing && video.status === "pending" && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-gray-200 bg-white py-16">
          <Zap className="mb-4 h-16 w-16 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-900">Ready for Analysis</h3>
          <p className="mt-1 max-w-sm text-center text-sm text-gray-500">
            Click &quot;Analyze Video&quot; to run the ML pipeline. This will transcribe the audio,
            detect scenes, analyze emotions, and generate shorts.
          </p>
          <button
            onClick={handleStartAnalysis}
            className="mt-6 flex items-center gap-2 rounded-lg bg-red-600 px-6 py-3 text-sm font-medium text-white hover:bg-red-700"
          >
            <Zap className="h-4 w-4" />
            Start Analysis
          </button>
        </div>
      )}
    </div>
  );
}

// ── Tab Components ──────────────────────────────────────────────────

function OverviewTab({
  analysis,
  shorts,
}: {
  analysis: AnalysisResult;
  shorts: Short[];
}) {
  return (
    <div className="space-y-6">
      {/* Summary */}
      {analysis.summary && (
        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <h3 className="mb-2 text-sm font-semibold text-gray-900">AI Summary</h3>
          <p className="text-sm leading-relaxed text-gray-600">{analysis.summary}</p>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MiniStat label="Scenes Detected" value={analysis.scenes.length} />
        <MiniStat label="Highlights Found" value={analysis.highlights.length} />
        <MiniStat label="Emotion Segments" value={analysis.emotions.length} />
        <MiniStat label="Shorts Generated" value={shorts.length} />
      </div>

      {/* Categories */}
      {analysis.categories && (
        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <h3 className="mb-3 text-sm font-semibold text-gray-900">Content Classification</h3>
          <div className="space-y-2">
            {analysis.categories.primary && (
              <p className="text-sm text-gray-600">
                <span className="font-medium">Primary Category:</span>{" "}
                <span className="capitalize">{analysis.categories.primary}</span>
              </p>
            )}
            {analysis.categories.content_type && (
              <p className="text-sm text-gray-600">
                <span className="font-medium">Content Type:</span>{" "}
                <span className="capitalize">{analysis.categories.content_type}</span>
              </p>
            )}
            {analysis.categories.tags && analysis.categories.tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {analysis.categories.tags.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Top Highlights Preview */}
      {analysis.highlights.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <h3 className="mb-3 text-sm font-semibold text-gray-900">
            Top Highlights (by score)
          </h3>
          <div className="space-y-2">
            {analysis.highlights.slice(0, 5).map((h, i) => (
              <HighlightCard key={i} highlight={h} rank={i + 1} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function HighlightsTab({ highlights }: { highlights: Highlight[] }) {
  if (highlights.length === 0) {
    return (
      <div className="py-12 text-center text-sm text-gray-500">
        No highlights detected
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {highlights.map((h, i) => (
        <HighlightCard key={i} highlight={h} rank={i + 1} />
      ))}
    </div>
  );
}

function HighlightCard({ highlight, rank }: { highlight: Highlight; rank: number }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-red-100 text-xs font-bold text-red-700">
            {rank}
          </span>
          <div>
            <h4 className="text-sm font-semibold text-gray-900">{highlight.title}</h4>
            <p className="mt-0.5 text-xs text-gray-500">{highlight.description}</p>
            <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
              <span>
                {formatDuration(highlight.start_time)} - {formatDuration(highlight.end_time)}
              </span>
              <span>{formatDuration(highlight.duration)}</span>
              <span className={`rounded-full px-2 py-0.5 font-medium ${getCategoryColor(highlight.category)}`}>
                {highlight.category}
              </span>
            </div>
            {highlight.reasons && highlight.reasons.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {highlight.reasons.map((r, i) => (
                  <span key={i} className="rounded bg-gray-50 px-2 py-0.5 text-[11px] text-gray-500">
                    {r}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
        <div className="text-right">
          <div className="text-lg font-bold text-gray-900">
            {(highlight.score * 100).toFixed(0)}%
          </div>
          <div className="text-[10px] text-gray-400">score</div>
        </div>
      </div>
    </div>
  );
}

function TranscriptTab({ transcript }: { transcript: string | null }) {
  if (!transcript) {
    return (
      <div className="py-12 text-center text-sm text-gray-500">
        No transcript available
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6">
      <h3 className="mb-3 text-sm font-semibold text-gray-900">Full Transcript</h3>
      <div className="max-h-96 overflow-y-auto whitespace-pre-wrap text-sm leading-relaxed text-gray-600">
        {transcript}
      </div>
    </div>
  );
}

function EmotionsTab({ emotions }: { emotions: AnalysisResult["emotions"] }) {
  if (emotions.length === 0) {
    return (
      <div className="py-12 text-center text-sm text-gray-500">
        No emotion data available
      </div>
    );
  }

  const emotionColors: Record<string, string> = {
    happy: "bg-yellow-100 text-yellow-800 border-yellow-200",
    sad: "bg-blue-100 text-blue-800 border-blue-200",
    excited: "bg-red-100 text-red-800 border-red-200",
    angry: "bg-orange-100 text-orange-800 border-orange-200",
    surprised: "bg-purple-100 text-purple-800 border-purple-200",
    neutral: "bg-gray-100 text-gray-800 border-gray-200",
  };

  return (
    <div className="space-y-2">
      {emotions.map((e, i) => (
        <div
          key={i}
          className={cn(
            "rounded-lg border p-3",
            emotionColors[e.emotion] || emotionColors.neutral
          )}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium capitalize">{e.emotion}</span>
              <span className="text-xs opacity-60">
                {formatDuration(e.start_time)} - {formatDuration(e.end_time)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-16 overflow-hidden rounded-full bg-black/10">
                <div
                  className="h-full rounded-full bg-current opacity-60"
                  style={{ width: `${e.intensity * 100}%` }}
                />
              </div>
              <span className="text-xs font-medium">{(e.intensity * 100).toFixed(0)}%</span>
            </div>
          </div>
          {e.text && <p className="mt-1 text-xs opacity-80">{e.text}</p>}
        </div>
      ))}
    </div>
  );
}

function EnergyTab({ energy }: { energy: AnalysisResult["audio_energy"] }) {
  if (energy.length === 0) {
    return (
      <div className="py-12 text-center text-sm text-gray-500">
        No audio energy data available
      </div>
    );
  }

  const maxEnergy = Math.max(...energy.map((e) => e.energy), 0.01);

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6">
      <h3 className="mb-4 text-sm font-semibold text-gray-900">Audio Energy Timeline</h3>
      <div className="relative h-48 w-full overflow-hidden rounded-lg bg-gray-50">
        <svg
          viewBox={`0 0 ${energy.length} 100`}
          className="h-full w-full"
          preserveAspectRatio="none"
        >
          {/* Energy bars */}
          {energy.map((point, i) => {
            const height = (point.energy / maxEnergy) * 100;
            return (
              <rect
                key={i}
                x={i}
                y={100 - height}
                width={1}
                height={height}
                fill={point.is_peak ? "#dc2626" : "#6b7280"}
                opacity={point.is_peak ? 0.8 : 0.3}
              />
            );
          })}
        </svg>
      </div>
      <div className="mt-2 flex justify-between text-xs text-gray-400">
        <span>{formatDuration(energy[0]?.time ?? 0)}</span>
        <span className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-red-500" /> Peak energy
          <span className="inline-block h-2 w-2 rounded-full bg-gray-400" /> Normal
        </span>
        <span>{formatDuration(energy[energy.length - 1]?.time ?? 0)}</span>
      </div>
    </div>
  );
}

function ShortsTab({ shorts, videoId }: { shorts: Short[]; videoId: string }) {
  const [regenerating, setRegenerating] = useState<string | null>(null);
  const [allShorts, setAllShorts] = useState(shorts);
  const [editingShort, setEditingShort] = useState<string | null>(null);
  const [editTemplate, setEditTemplate] = useState("");
  const [editMainText, setEditMainText] = useState("");
  const [editSubText, setEditSubText] = useState("");
  const [templates, setTemplates] = useState<Template[]>([]);

  useEffect(() => {
    listTemplates().then(setTemplates).catch(() => {});
  }, []);

  useEffect(() => {
    setAllShorts(shorts);
  }, [shorts]);

  const handleRegenerate = async (short: Short, index: number) => {
    if (!editTemplate) return;
    setRegenerating(short.id);
    try {
      const newShort = await regenerateShort({
        video_id: videoId,
        highlight_index: index,
        template_id: editTemplate,
        main_text: editMainText || "Watch This",
        sub_text: editSubText,
      });
      setAllShorts((prev) => [...prev, newShort]);
      setEditingShort(null);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Regeneration failed");
    } finally {
      setRegenerating(null);
    }
  };

  if (allShorts.length === 0) {
    return (
      <div className="py-12 text-center text-sm text-gray-500">
        No shorts generated yet
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {allShorts.map((short, i) => (
        <div
          key={short.id}
          className="overflow-hidden rounded-xl border border-gray-200 bg-white"
        >
          {/* Preview area */}
          <div className="relative flex aspect-[9/16] max-h-64 items-center justify-center bg-gradient-to-b from-gray-800 to-gray-900">
            <Scissors className="h-10 w-10 text-gray-600" />
            {/* Template overlay preview */}
            {short.template_id && short.template_variables && (
              <div className="absolute inset-0 flex flex-col items-center justify-center p-4">
                <p className="text-center text-lg font-bold text-white drop-shadow-lg">
                  {short.template_variables.main_text}
                </p>
                {short.template_variables.sub_text && (
                  <p className="mt-1 text-center text-xs text-white/80 drop-shadow">
                    {short.template_variables.sub_text}
                  </p>
                )}
              </div>
            )}
            {/* Template badge */}
            {short.template_id && (
              <div className="absolute top-2 right-2 flex items-center gap-1 rounded-full bg-black/60 px-2 py-0.5">
                <Palette className="h-3 w-3 text-purple-400" />
                <span className="text-[10px] text-white">{short.template_id}</span>
              </div>
            )}
          </div>

          <div className="p-4">
            <h4 className="text-sm font-semibold text-gray-900">{short.title}</h4>
            <p className="mt-1 line-clamp-2 text-xs text-gray-500">{short.description}</p>

            <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
              <span>{formatDuration(short.duration)}</span>
              {short.category && (
                <span className={`rounded-full px-2 py-0.5 font-medium ${getCategoryColor(short.category)}`}>
                  {short.category}
                </span>
              )}
              <span className="font-semibold text-gray-900">
                {(short.score * 100).toFixed(0)}%
              </span>
            </div>

            {/* Regenerate with different template */}
            {editingShort === short.id ? (
              <div className="mt-3 space-y-2 border-t border-gray-100 pt-3">
                <select
                  value={editTemplate}
                  onChange={(e) => setEditTemplate(e.target.value)}
                  className="w-full rounded border border-gray-300 px-2 py-1.5 text-xs focus:border-red-500 focus:outline-none"
                >
                  <option value="">Select template...</option>
                  {templates.map((t) => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </select>
                <input
                  type="text"
                  value={editMainText}
                  onChange={(e) => setEditMainText(e.target.value)}
                  placeholder="Main text (e.g. Ronaldo Aura)"
                  className="w-full rounded border border-gray-300 px-2 py-1.5 text-xs focus:border-red-500 focus:outline-none"
                />
                <input
                  type="text"
                  value={editSubText}
                  onChange={(e) => setEditSubText(e.target.value)}
                  placeholder="Sub text (optional)"
                  className="w-full rounded border border-gray-300 px-2 py-1.5 text-xs focus:border-red-500 focus:outline-none"
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => handleRegenerate(short, i)}
                    disabled={!editTemplate || regenerating === short.id}
                    className="flex flex-1 items-center justify-center gap-1 rounded bg-red-600 px-2 py-1.5 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
                  >
                    {regenerating === short.id ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Sparkles className="h-3 w-3" />
                    )}
                    Generate
                  </button>
                  <button
                    onClick={() => setEditingShort(null)}
                    className="rounded border border-gray-300 px-2 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => {
                  setEditingShort(short.id);
                  setEditTemplate(short.template_id || "");
                  setEditMainText(short.template_variables?.main_text || "");
                  setEditSubText(short.template_variables?.sub_text || "");
                }}
                className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-lg border border-gray-200 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
              >
                <RotateCw className="h-3 w-3" />
                Change Template
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 text-center">
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  );
}
