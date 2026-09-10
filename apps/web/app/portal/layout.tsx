import type { Metadata, Viewport } from "next";
import "./portal-v2.css";

export const metadata: Metadata = {
  title: "GMAI | Private Client Workspace",
  description: "A secure, expiring view of your mobility case progress and document status.",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    title: "GMAI Portal",
    statusBarStyle: "default",
  },
  icons: {
    icon: "/icon.svg",
    apple: "/icon.svg",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#4338ca",
};

const swRegistrationScript = `
  (function() {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js", { scope: "/portal" })
        .then(function(reg) { console.log("GMAI portal SW registered", reg.scope); })
        .catch(function(err) { console.warn("GMAI portal SW registration failed", err); });
    }
  })();
`;

export default function PortalLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <script suppressHydrationWarning dangerouslySetInnerHTML={{ __html: swRegistrationScript }} />
      {children}
    </>
  );
}
