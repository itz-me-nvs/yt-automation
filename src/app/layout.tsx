import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "YT Automation - AI-Powered Shorts Creator",
  description:
    "Analyze videos with local ML models and automatically generate YouTube Shorts from the best moments.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased bg-gray-50 font-sans">
        <Sidebar />
        <main className="ml-64 min-h-screen">{children}</main>
      </body>
    </html>
  );
}
