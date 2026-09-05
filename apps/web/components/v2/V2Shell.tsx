import Link from "next/link";
import type { ReactNode } from "react";

import { ownerNavigation, type OwnerNavLabel } from "../../lib/v2/navigation";
import { V2Icon } from "./V2Icon";

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
                    title={item.description}
                  >
                    <span className="aios-v2-nav-glyph" aria-hidden="true">
                      <V2Icon name={item.icon} width={18} height={18} />
                    </span>
                    <span>{item.label}</span>
                  </Link>
                );
              }

              return (
                <span
                  className="aios-v2-nav-item"
                  aria-disabled="true"
                  key={item.label}
                  title={item.description}
                >
                  <span className="aios-v2-nav-glyph" aria-hidden="true">
                    <V2Icon name={item.icon} width={18} height={18} />
                  </span>
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
            <button
              className="aios-v2-command"
              type="button"
              disabled
              aria-label="Command palette is not connected in this V2 slice"
            >
              <V2Icon name="search" width={16} height={16} />
              <span>Search / Command</span>
            </button>
          </div>

          {children}
        </main>
      </div>
    </div>
  );
}
