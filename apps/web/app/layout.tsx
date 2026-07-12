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

const themeInitScript = `
  (function() {
    try {
      var stored = localStorage.getItem("gmai-theme");
      var theme = stored || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
      document.documentElement.setAttribute("data-theme", theme);
    } catch (e) {}
  })();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body suppressHydrationWarning>
        {children}
        <AgentChatWidget />
      </body>
    </html>
  );
}
