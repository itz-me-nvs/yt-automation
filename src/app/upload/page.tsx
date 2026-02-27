"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Upload,
  Link2,
  FileVideo,
  X,
  Loader2,
  CheckCircle2,
} from "lucide-react";
import { uploadVideo, addYoutubeVideo } from "@/lib/api";
import { cn } from "@/lib/utils";

type Tab = "upload" | "youtube";

export default function UploadPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>("upload");
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState<{ id: string; message: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  // File upload state
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);

  // YouTube state
  const [ytUrl, setYtUrl] = useState("");
  const [ytTitle, setYtTitle] = useState("");

  const handleFileDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type.startsWith("video/")) {
      setFile(droppedFile);
      setError(null);
    } else {
      setError("Please drop a video file");
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
    }
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const result = await uploadVideo(file);
      setSuccess({ id: result.id, message: result.message });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleYoutubeSubmit = async () => {
    if (!ytUrl.trim()) return;
    setUploading(true);
    setError(null);
    try {
      const result = await addYoutubeVideo(ytUrl, ytTitle || undefined);
      setSuccess({ id: result.id, message: result.message });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add YouTube video");
    } finally {
      setUploading(false);
    }
  };

  if (success) {
    return (
      <div className="flex min-h-screen items-center justify-center p-8">
        <div className="w-full max-w-md rounded-xl border border-gray-200 bg-white p-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
            <CheckCircle2 className="h-8 w-8 text-green-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-900">Video Added!</h2>
          <p className="mt-2 text-sm text-gray-500">{success.message}</p>
          <div className="mt-6 flex gap-3">
            <button
              onClick={() => router.push(`/videos/${success.id}`)}
              className="flex-1 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-red-700"
            >
              View & Analyze
            </button>
            <button
              onClick={() => {
                setSuccess(null);
                setFile(null);
                setYtUrl("");
                setYtTitle("");
              }}
              className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Add Another
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Add Video</h1>
        <p className="mt-1 text-sm text-gray-500">
          Upload a video file or paste a YouTube link to start analysis
        </p>
      </div>

      <div className="mx-auto max-w-2xl">
        {/* Tabs */}
        <div className="mb-6 flex rounded-lg border border-gray-200 bg-gray-50 p-1">
          <button
            onClick={() => setActiveTab("upload")}
            className={cn(
              "flex flex-1 items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium transition-colors",
              activeTab === "upload"
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            )}
          >
            <Upload className="h-4 w-4" />
            Upload File
          </button>
          <button
            onClick={() => setActiveTab("youtube")}
            className={cn(
              "flex flex-1 items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium transition-colors",
              activeTab === "youtube"
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            )}
          >
            <Link2 className="h-4 w-4" />
            YouTube Link
          </button>
        </div>

        {/* Upload Tab */}
        {activeTab === "upload" && (
          <div className="rounded-xl border border-gray-200 bg-white p-6">
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleFileDrop}
              className={cn(
                "flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors",
                dragOver
                  ? "border-red-400 bg-red-50"
                  : file
                    ? "border-green-300 bg-green-50"
                    : "border-gray-300 hover:border-gray-400"
              )}
            >
              {file ? (
                <>
                  <FileVideo className="mb-3 h-12 w-12 text-green-600" />
                  <p className="text-sm font-medium text-gray-900">{file.name}</p>
                  <p className="text-xs text-gray-500">
                    {(file.size / 1024 / 1024).toFixed(1)} MB
                  </p>
                  <button
                    onClick={() => setFile(null)}
                    className="mt-3 flex items-center gap-1 text-sm text-red-600 hover:text-red-700"
                  >
                    <X className="h-4 w-4" /> Remove
                  </button>
                </>
              ) : (
                <>
                  <Upload className="mb-3 h-12 w-12 text-gray-400" />
                  <p className="text-sm font-medium text-gray-700">
                    Drop your video here or click to browse
                  </p>
                  <p className="mt-1 text-xs text-gray-500">
                    Supports MP4, MOV, AVI, MKV, WebM
                  </p>
                  <input
                    type="file"
                    accept="video/*"
                    onChange={handleFileSelect}
                    className="absolute inset-0 cursor-pointer opacity-0"
                    style={{ position: "relative" }}
                  />
                  <label className="mt-4 cursor-pointer rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200">
                    Browse Files
                    <input
                      type="file"
                      accept="video/*"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                  </label>
                </>
              )}
            </div>

            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-red-600 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4" />
                  Upload Video
                </>
              )}
            </button>
          </div>
        )}

        {/* YouTube Tab */}
        {activeTab === "youtube" && (
          <div className="rounded-xl border border-gray-200 bg-white p-6">
            <div className="space-y-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  YouTube URL
                </label>
                <input
                  type="url"
                  value={ytUrl}
                  onChange={(e) => setYtUrl(e.target.value)}
                  placeholder="https://www.youtube.com/watch?v=..."
                  className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  Title (optional)
                </label>
                <input
                  type="text"
                  value={ytTitle}
                  onChange={(e) => setYtTitle(e.target.value)}
                  placeholder="Give it a name for easy reference"
                  className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
                />
              </div>
            </div>

            <button
              onClick={handleYoutubeSubmit}
              disabled={!ytUrl.trim() || uploading}
              className="mt-6 flex w-full items-center justify-center gap-2 rounded-lg bg-red-600 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Link2 className="h-4 w-4" />
                  Add YouTube Video
                </>
              )}
            </button>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Info */}
        <div className="mt-6 rounded-lg border border-blue-100 bg-blue-50 p-4">
          <h3 className="text-sm font-medium text-blue-800">
            What happens after adding a video?
          </h3>
          <ol className="mt-2 space-y-1 text-sm text-blue-700">
            <li>1. Video is downloaded/saved locally</li>
            <li>2. Audio is transcribed with Whisper (local speech-to-text)</li>
            <li>3. Scenes are detected using PySceneDetect</li>
            <li>4. Audio energy is analyzed with librosa</li>
            <li>5. Frames are classified with CLIP (visual AI)</li>
            <li>6. Content is analyzed with Ollama (local LLM)</li>
            <li>7. Best moments are scored and ranked</li>
            <li>8. YouTube Shorts are auto-generated (9:16 format)</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
