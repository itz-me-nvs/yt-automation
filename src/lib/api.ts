const API_BASE = "/api/py";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

// ── Videos ─────────────────────────────────────────────────────────

export interface Video {
  id: string;
  title: string;
  source_type: "upload" | "youtube";
  source_url: string | null;
  duration: number | null;
  resolution: string | null;
  file_size: number | null;
  thumbnail_path: string | null;
  status: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface VideoUploadResponse {
  id: string;
  title: string;
  status: string;
  message: string;
}

export async function listVideos(): Promise<Video[]> {
  return request<Video[]>("/videos/");
}

export async function getVideo(id: string): Promise<Video> {
  return request<Video>(`/videos/${id}`);
}

export async function uploadVideo(file: File, title?: string): Promise<VideoUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (title) formData.append("title", title);

  const res = await fetch(`${API_BASE}/videos/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

export async function addYoutubeVideo(url: string, title?: string): Promise<VideoUploadResponse> {
  return request<VideoUploadResponse>("/videos/youtube", {
    method: "POST",
    body: JSON.stringify({ url, title }),
  });
}

export async function deleteVideo(id: string): Promise<void> {
  await request(`/videos/${id}`, { method: "DELETE" });
}

// ── Analysis ───────────────────────────────────────────────────────

export interface AnalysisProgress {
  stage: string;
  progress: number;
  message: string;
}

export interface Scene {
  index: number;
  start_time: number;
  end_time: number;
  duration: number;
  description: string;
  confidence: number;
  visual_category?: string;
}

export interface Highlight {
  start_time: number;
  end_time: number;
  duration: number;
  category: string;
  title: string;
  description: string;
  score: number;
  reasons: string[];
  source?: string;
}

export interface EmotionSegment {
  start_time: number;
  end_time: number;
  emotion: string;
  intensity: number;
  text: string;
}

export interface AudioEnergyPoint {
  time: number;
  energy: number;
  is_peak: boolean;
}

export interface AnalysisResult {
  id: string;
  video_id: string;
  transcript: string | null;
  scenes: Scene[];
  highlights: Highlight[];
  emotions: EmotionSegment[];
  categories: {
    primary?: string;
    tags?: string[];
    content_type?: string;
  };
  summary: string | null;
  audio_energy: AudioEnergyPoint[];
  created_at: string;
}

export interface Short {
  id: string;
  video_id: string;
  title: string;
  description: string | null;
  start_time: number;
  end_time: number;
  duration: number;
  category: string | null;
  score: number;
  file_path: string | null;
  thumbnail_path: string | null;
  status: string;
  created_at: string;
}

export interface AnalysisResults {
  analysis: AnalysisResult;
  shorts: Short[];
}

export async function startAnalysis(videoId: string): Promise<{ message: string; video_id: string }> {
  return request(`/analysis/${videoId}/start`, { method: "POST" });
}

export async function getAnalysisProgress(videoId: string): Promise<AnalysisProgress> {
  return request<AnalysisProgress>(`/analysis/${videoId}/progress`);
}

export async function getAnalysisResults(videoId: string): Promise<AnalysisResults> {
  return request<AnalysisResults>(`/analysis/${videoId}/results`);
}

export async function getShorts(videoId: string): Promise<Short[]> {
  return request<Short[]>(`/analysis/${videoId}/shorts`);
}

// ── Channel ────────────────────────────────────────────────────────

export interface ChannelInfo {
  id: string;
  channel_name: string | null;
  channel_url: string | null;
  total_videos_processed: number;
  total_shorts_generated: number;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ChannelStats {
  channel: {
    name: string;
    total_videos: number;
    total_shorts: number;
  };
  video_status_counts: Record<string, number>;
  category_counts: Record<string, number>;
  recent_videos: Array<{
    id: string;
    title: string;
    status: string;
    created_at: string;
  }>;
  recent_shorts: Array<{
    id: string;
    title: string;
    category: string;
    score: number;
    duration: number;
    status: string;
    created_at: string;
    video_title: string;
  }>;
  total_video_duration: number;
  total_shorts_duration: number;
}

export async function getChannelInfo(): Promise<ChannelInfo> {
  return request<ChannelInfo>("/channel/");
}

export async function updateChannelInfo(data: {
  channel_name?: string;
  channel_url?: string;
  settings?: Record<string, unknown>;
}): Promise<ChannelInfo> {
  return request<ChannelInfo>("/channel/", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function getChannelStats(): Promise<ChannelStats> {
  return request<ChannelStats>("/channel/stats");
}

// ── Health ──────────────────────────────────────────────────────────

export async function checkHealth(): Promise<{ status: string }> {
  return request<{ status: string }>("/health");
}
