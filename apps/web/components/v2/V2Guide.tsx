"use client";

import { useEffect, useRef, useState } from "react";
import type { Driver } from "driver.js";
import { useV2Preferences } from "./V2Preferences";

const guidance = [
  { selector: '[data-guide="workspace-title"]', title: "Your current workspace", description: "Start with the purpose of this workspace. Loading, unavailable and stale records are labelled where they occur." },
  { selector: '[data-guide="command"]', title: "Move through AIOS", description: "Use Navigate AIOS or Control / Command K to find workspaces and records already loaded on this page. Opening a record never approves work." },
  { selector: '#aios-v2-main', title: "Inspect before acting", description: "Read the record, its evidence and its provenance. Recommendations, historical reconstructions and aggregate memory have different meanings. Board actions require an explicit review and remain governed by the server." },
];

export function V2Guide() {
  const { theme } = useV2Preferences();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const tour = useRef<Driver | null>(null);
  const generation = useRef(0);
  useEffect(() => () => { generation.current += 1; tour.current?.destroy(); }, []);
  async function start() {
    const request = ++generation.current;
    setLoading(true); setError(null);
    try {
      const { driver } = await import("driver.js");
      if (request !== generation.current) return;
      const steps = guidance.flatMap(({ selector, title, description }) => {
        const element = document.querySelector<HTMLElement>(selector);
        return element && element.getClientRects().length ? [{ element, popover: { title, description } }] : [];
      });
      if (!steps.length) { setError("Guided highlights are unavailable. The text guide remains below."); return; }
      setOpen(false);
      tour.current = driver({ steps, animate: !matchMedia("(prefers-reduced-motion: reduce)").matches,
        smoothScroll: false, disableActiveInteraction: true, allowClose: true,
        overlayClickBehavior: "close", allowKeyboardControl: true, showProgress: true,
        popoverClass: `aios-v2-guide aios-v2-guide-${theme}`,
        onDestroyed: () => { tour.current = null; trigger.current?.focus(); },
      });
      tour.current.drive();
    } catch { if (request === generation.current) setError("Guided highlights could not load. Use the text guide below."); }
    finally { if (request === generation.current) setLoading(false); }
  }
  return <div className="aios-v2-guide-control">
    <button ref={trigger} type="button" aria-expanded={open} aria-controls="aios-v2-text-guide" onClick={() => setOpen(!open)}>Help</button>
    {open ? <section id="aios-v2-text-guide" aria-label="Workspace guide">
      <h2>A guide to AIOS</h2>
      <ol>{guidance.map((step) => <li key={step.title}><strong>{step.title}</strong><p>{step.description}</p></li>)}</ol>
      {error ? <p role="alert">{error}</p> : null}
      <button type="button" disabled={loading} onClick={start}>{loading ? "Loading guide…" : "Start guided highlights"}</button>
      <button type="button" onClick={() => { setOpen(false); trigger.current?.focus(); }}>Close help</button>
    </section> : null}
  </div>;
}
