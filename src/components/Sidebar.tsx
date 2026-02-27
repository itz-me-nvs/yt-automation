"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Upload,
  Video,
  User,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/upload", label: "Upload / Add Video", icon: Upload },
  { href: "/videos", label: "My Videos", icon: Video },
  { href: "/account", label: "Account", icon: User },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-gray-200 bg-white">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 border-b border-gray-200 px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-600">
          <Zap className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-gray-900">YT Automation</h1>
          <p className="text-[10px] text-gray-500 -mt-1">AI-Powered Shorts Creator</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-red-50 text-red-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <Icon className={cn("h-5 w-5", isActive ? "text-red-600" : "text-gray-400")} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* ML Status Footer */}
      <div className="border-t border-gray-200 p-4">
        <div className="rounded-lg bg-gray-50 p-3">
          <p className="text-xs font-medium text-gray-600">ML Pipeline</p>
          <div className="mt-1 space-y-1">
            <StatusDot label="Whisper (STT)" />
            <StatusDot label="CLIP (Vision)" />
            <StatusDot label="Ollama (LLM)" />
            <StatusDot label="librosa (Audio)" />
          </div>
        </div>
      </div>
    </aside>
  );
}

function StatusDot({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className="h-1.5 w-1.5 rounded-full bg-green-500" />
      <span className="text-[11px] text-gray-500">{label}</span>
    </div>
  );
}
