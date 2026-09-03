import Link from "next/link";
import type { ReactNode } from "react";

type OwnerNavLabel =
  | "Home"
  | "Organization"
  | "Missions"
  | "Intelligence"
  | "Evidence"
  | "Decisions"
  | "History";

const ownerNavigation: Array<{
  label: OwnerNavLabel;
  glyph: string;
  href: string | null;
  enabled: boolean;
}> = [
  { label: "Home", glyph: "H", href: "/cockpit/v2", enabled: true },
  { label: "Organization", glyph: "O", href: "/cockpit/v2/organization", enabled: true },
  { label: "Missions", glyph: "M", href: null, enabled: false },
  { label: "Intelligence", glyph: "I", href: null, enabled: false },
  { label: "Evidence", glyph: "E", href: null, enabled: false },
  { label: "Decisions", glyph: "D", href: null, enabled: false },
  { label: "History", glyph: "T", href: null, enabled: false },
];

export function V2Shell({
  children,
  backendOnline,
  activeItem = "Home",
}: {
  children: ReactNode;
  backendOnline: boolean;
  activeItem?: OwnerNavLabel;
}) {
  return (
    <div className="aios-v2-root">
      <a className="aios-v2-skip-link" href="#aios-v2-main">Skip to main content</a>

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
            {ownerNavigation.map((item) => {
              const active = item.label === activeItem;
              if (item.enabled && item.href) {
                return (
                  <Link
                    className={"aios-v2-nav-item" + (active ? " active" : "")}
                    href={item.href}
                    key={item.label}
                    aria-current={active ? "page" : undefined}
                  >
                    <span className="aios-v2-nav-glyph" aria-hidden="true">{item.glyph}</span>
                    <span>{item.label}</span>
                  </Link>
                );
              }

              return (
                <span className="aios-v2-nav-item" aria-disabled="true" key={item.label}>
                  <span className="aios-v2-nav-glyph" aria-hidden="true">{item.glyph}</span>
                  <span>{item.label}</span>
                </span>
              );
            })}
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
              <span>AIOS V2</span>
            </div>
            <button className="aios-v2-command" type="button" disabled aria-label="Command palette is not connected in this V2 slice">
              Search / Command
            </button>
          </div>

          {children}
        </main>
      </div>
    </div>
  );
}
