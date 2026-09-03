import Link from "next/link";
import type { ReactNode } from "react";

const ownerNavigation = [
  { label: "Home", glyph: "H", href: "/cockpit/v2", enabled: true },
  { label: "Organization", glyph: "O", href: null, enabled: false },
  { label: "Missions", glyph: "M", href: null, enabled: false },
  { label: "Intelligence", glyph: "I", href: null, enabled: false },
  { label: "Evidence", glyph: "E", href: null, enabled: false },
  { label: "Decisions", glyph: "D", href: null, enabled: false },
  { label: "History", glyph: "T", href: null, enabled: false },
] as const;

export function V2Shell({
  children,
  backendOnline,
}: {
  children: ReactNode;
  backendOnline: boolean;
}) {
  return (
    <div className="aios-v2-root">
      <div className="aios-v2-shell">
        <aside className="aios-v2-rail" aria-label="AIOS V2 Owner navigation">
          <div className="aios-v2-brand">
            <div className="aios-v2-brand-mark" aria-hidden="true">AI</div>
            <div className="aios-v2-brand-copy">
              <strong>AIOS</strong>
              <span>Living Organization OS</span>
            </div>
          </div>

          <nav className="aios-v2-nav" aria-label="Owner">
            {ownerNavigation.map((item) => (
              item.enabled && item.href ? (
                <Link className="aios-v2-nav-item active" href={item.href} key={item.label} aria-current="page">
                  <span className="aios-v2-nav-glyph" aria-hidden="true">{item.glyph}</span>
                  <span>{item.label}</span>
                </Link>
              ) : (
                <span className="aios-v2-nav-item" aria-disabled="true" key={item.label}>
                  <span className="aios-v2-nav-glyph" aria-hidden="true">{item.glyph}</span>
                  <span>{item.label}</span>
                </span>
              )
            ))}
          </nav>

          <div className="aios-v2-rail-footer">
            <div className="aios-v2-health" data-state={backendOnline ? "online" : "unknown"}>
              <span className="aios-v2-health-dot" aria-hidden="true" />
              <span>{backendOnline ? "Backend online" : "Backend status unavailable"}</span>
            </div>
          </div>
        </aside>

        <main className="aios-v2-main" id="aios-v2-main">
          <div className="aios-v2-topline">
            <div className="aios-v2-topline-context">
              <strong>Owner</strong>
              <span>V2 foundation preview</span>
            </div>
            <button className="aios-v2-command" type="button" disabled aria-label="Command palette is not connected in the foundation slice">
              Search / Command
            </button>
          </div>

          {children}
        </main>
      </div>
    </div>
  );
}
