"use client";

export function Topbar({
  title,
  kicker,
  loadStatus,
  onRefresh,
}: {
  title: string;
  kicker: string;
  loadStatus: "idle" | "loading" | "ready" | "partial" | "offline";
  onRefresh: () => void;
}) {
  return (
    <header className="topbar">
      <div>
        <span className="page-kicker">{kicker}</span>
        <h1>{title}</h1>
      </div>
      <div className="topbar-actions">
        <button className="button secondary" type="button" onClick={onRefresh} disabled={loadStatus === "loading"}>
          {loadStatus === "loading" ? (
            <span className="button-spinner" aria-hidden="true" />
          ) : (
            "Refresh"
          )}
        </button>
      </div>
    </header>
  );
}
