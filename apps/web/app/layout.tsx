import type { Metadata, Viewport } from "next";
import "./globals.css";
import { AgentChatWidget } from "../components/AgentChatWidget";

export const metadata: Metadata = {
  title: "Global Mobility AIOS | Operations Workspace",
  description:
    "A calm operator workspace for global mobility leads, truth checks, document review, and human-controlled AI workflows.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#f7f5ef",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        {children}
        <AgentChatWidget />
      </body>
    </html>
  );
}
