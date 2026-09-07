"use client";

import { usePathname } from "next/navigation";
import { useState, type ComponentType } from "react";

type LoadedConsultant = ComponentType<{ initiallyOpen?: boolean }>;

function isClientFacingRoute(pathname: string) {
  return pathname.startsWith("/portal")
    || pathname.startsWith("/return")
    || pathname.startsWith("/partner-portal");
}

export function AgentChatWidgetLoader() {
  const pathname = usePathname();
  const [Consultant, setConsultant] = useState<LoadedConsultant | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  if (isClientFacingRoute(pathname)) return null;

  if (Consultant) {
    return <Consultant initiallyOpen />;
  }

  const loadConsultant = async () => {
    if (loading) return;
    setLoading(true);
    setLoadError(null);
    try {
      const module = await import("./AgentChatWidget");
      setConsultant(() => module.AgentChatWidget);
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Consultant failed to load");
      setLoading(false);
    }
  };

  const accessibleLabel = loadError
    ? "Retry loading consultant chat"
    : loading
      ? "Loading consultant chat"
      : "Open consultant chat";

  return (
    <div className="agent-chat-widget" data-consultant-load-state={loadError ? "error" : loading ? "loading" : "idle"}>
      <button
        className="agent-chat-fab"
        type="button"
        onClick={loadConsultant}
        aria-label={accessibleLabel}
        aria-busy={loading || undefined}
        disabled={loading}
        title={loadError || undefined}
      >
        <span aria-hidden="true">{loadError ? "⚠️" : loading ? "…" : "💬"}</span>
      </button>
      <span
        role="status"
        aria-live="polite"
        style={{
          position: "absolute",
          width: 1,
          height: 1,
          padding: 0,
          margin: -1,
          overflow: "hidden",
          clip: "rect(0, 0, 0, 0)",
          whiteSpace: "nowrap",
          border: 0,
        }}
      >
        {loadError ? "Consultant failed to load. Activate the button to retry." : loading ? "Loading consultant chat." : ""}
      </span>
    </div>
  );
}
