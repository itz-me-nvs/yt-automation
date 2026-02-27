export function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return "0:00";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function formatFileSize(bytes: number | null | undefined): string {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  let size = bytes;
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024;
    i++;
  }
  return `${size.toFixed(1)} ${units[i]}`;
}

export function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800",
    downloading: "bg-blue-100 text-blue-800",
    analyzing: "bg-purple-100 text-purple-800",
    generating_shorts: "bg-indigo-100 text-indigo-800",
    completed: "bg-green-100 text-green-800",
    failed: "bg-red-100 text-red-800",
  };
  return colors[status] || "bg-gray-100 text-gray-800";
}

export function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    funny: "bg-amber-100 text-amber-800",
    exciting: "bg-red-100 text-red-800",
    emotional: "bg-blue-100 text-blue-800",
    music: "bg-purple-100 text-purple-800",
    dramatic: "bg-orange-100 text-orange-800",
    informative: "bg-cyan-100 text-cyan-800",
    general: "bg-gray-100 text-gray-800",
  };
  return colors[category] || "bg-gray-100 text-gray-800";
}

export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(" ");
}
