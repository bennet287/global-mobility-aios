"use client";

import Link from "next/link";
import { useCallback, useEffect, useState, type ReactNode } from "react";

import {
  operatorNavigation,
  type OperatorNavLabel,
} from "../../lib/v2/operator-navigation";
import { V2Icon } from "./V2Icon";
import shellStyles from "./V2Shell.module.css";
import {
  V2_THEME_STORAGE_KEY,
  V2ThemeControl,
  isV2ThemePreference,
  type V2ThemePreference,
} from "./V2ThemeControl";

export function V2OperatorShell({
  children,
  activeItem = "Work",
}: {
  children: ReactNode;
  activeItem?: OperatorNavLabel;
}) {
  const [themePreference, setThemePreference] = useState<V2ThemePreference>("system");
  const changeTheme = useCallback((next: V2ThemePreference) => {
    setThemePreference(next);
    try {
      window.localStorage.setItem(V2_THEME_STORAGE_KEY, next);
    } catch {
      // Presentation preference persistence is best-effort only.
    }
  }, []);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(V2_THEME_STORAGE_KEY);
      if (isV2ThemePreference(stored)) setThemePreference(stored);
    } catch {
      // Storage can be unavailable in hardened/private browser contexts.
    }
  }, []);

  return (
    <div className={`aios-v2-root ${shellStyles.operatorFrame}`} data-theme={themePreference} data-product-role="operator">
      <a className="aios-v2-skip-link" href="#aios-v2-operator-main">Skip to main content</a>

      <div className={`aios-v2-shell ${shellStyles.operatorShell}`}>
        <aside className={`aios-v2-rail ${shellStyles.shellRail} ${shellStyles.operatorRail}`} aria-label="AIOS V2 Professional / Operator navigation">
          <div className={`aios-v2-brand ${shellStyles.operatorBrand}`}>
            <div className={`aios-v2-brand-mark ${shellStyles.brandMark}`} aria-hidden="true">AI</div>
            <div className="aios-v2-brand-copy">
              <strong>AIOS</strong>
              <span>Professional control environment</span>
            </div>
          </div>

          <div className={shellStyles.roleSignal} aria-label="Workspace role">
            <span>Professional</span>
            <strong>Operator</strong>
            <small>Governed case work</small>
          </div>

          <nav className={`aios-v2-nav ${shellStyles.operatorNav}`} aria-label="Professional / Operator">
            <span className={shellStyles.navEyebrow} aria-hidden="true">Primary workspaces</span>
            {operatorNavigation.map((item) => {
              const active = item.label === activeItem;
              if (item.enabled && item.href) {
                return (
                  <Link
                    className={`aios-v2-nav-item ${shellStyles.navItem}${active ? " active" : ""}`}
                    href={item.href}
                    key={item.label}
                    aria-current={active ? "page" : undefined}
                    aria-label={item.label}
                    title={item.description}
                  >
                    <span className={`aios-v2-nav-glyph ${shellStyles.navGlyph}`} aria-hidden="true">
                      <V2Icon name={item.icon} width={18} height={18} />
                    </span>
                    <span className={shellStyles.navCopy}>
                      <strong>{item.label}</strong>
                      <small>{item.description}</small>
                    </span>
                  </Link>
                );
              }

              return (
                <span
                  className={`aios-v2-nav-item ${shellStyles.navItem}`}
                  aria-disabled="true"
                  aria-label={`${item.label} (contextual workspace not yet migrated)`}
                  key={item.label}
                  title={item.description}
                >
                  <span className={`aios-v2-nav-glyph ${shellStyles.navGlyph}`} aria-hidden="true">
                    <V2Icon name={item.icon} width={18} height={18} />
                  </span>
                  <span className={shellStyles.navCopy}>
                    <strong>{item.label}</strong>
                    <small>{item.description}</small>
                  </span>
                </span>
              );
            })}
          </nav>

          <div className={shellStyles.railFootnote}>
            <span>Truth posture</span>
            <strong>Evidence-aware · human-controlled</strong>
          </div>
        </aside>

        <main className={`aios-v2-main ${shellStyles.operatorMain}`} id="aios-v2-operator-main">
          <div className={`aios-v2-topline ${shellStyles.topline} ${shellStyles.operatorTopline}`}>
            <div className={`aios-v2-topline-context ${shellStyles.toplineContext}`}>
              <span>Professional control environment</span>
              <strong>{activeItem}</strong>
              <small>Current workspace · governed operational state</small>
            </div>
            <V2ThemeControl value={themePreference} onChange={changeTheme} />
          </div>

          <div className={shellStyles.operatorContent}>{children}</div>
        </main>
      </div>
    </div>
  );
}
