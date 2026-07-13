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

const extensionCleanupScript = `
  (function() {
    function strip() {
      document.querySelectorAll('[bis_skin_checked]').forEach(function(el) {
        el.removeAttribute('bis_skin_checked');
      });
    }
    strip();
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', strip);
    }
    if (typeof MutationObserver !== 'undefined') {
      new MutationObserver(function(mutations) {
        var run = false;
        mutations.forEach(function(m) {
          if (m.type === 'attributes' && m.attributeName === 'bis_skin_checked') {
            m.target.removeAttribute('bis_skin_checked');
          } else if (m.type === 'childList') {
            run = true;
          }
        });
        if (run) strip();
      }).observe(document.documentElement, {
        attributes: true,
        subtree: true,
        attributeFilter: ['bis_skin_checked'],
        childList: true
      });
    }
  })();
`;

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
        <script suppressHydrationWarning dangerouslySetInnerHTML={{ __html: extensionCleanupScript }} />
        <script suppressHydrationWarning dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body suppressHydrationWarning>
        {children}
        <AgentChatWidget />
      </body>
    </html>
  );
}
