"use client";
import { useEffect, useRef, useState } from "react";
import type { LivingSceneRenderModel } from "../lib/living-organization-scene-renderer";
import type { LivingSceneRendererBackendPreference, LivingSceneRendererController, LivingSceneSelection } from "../lib/living-organization-webgpu-adapter";

type RendererPhase = "initializing" | "ready" | "unavailable";
function backendLabel(value: LivingSceneRendererBackendPreference | null): string {
  if (value === "webgpu-preferred") return "WebGPU preferred";
  if (value === "webgl2-fallback-required") return "WebGL2 fallback required";
  return "Detecting browser capability";
}
export function LivingOrganizationWebGPUScene({ renderModel }: { renderModel: LivingSceneRenderModel }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [phase, setPhase] = useState<RendererPhase>("initializing");
  const [backendPreference, setBackendPreference] = useState<LivingSceneRendererBackendPreference | null>(null);
  const [selection, setSelection] = useState<LivingSceneSelection | null>(null);
  const [failure, setFailure] = useState<string | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let cancelled = false;
    let controller: LivingSceneRendererController | null = null;
    setPhase("initializing");
    setFailure(null);
    setSelection(null);
    void (async () => {
      try {
        const { mountLivingOrganizationWebGPUScene } = await import("../lib/living-organization-webgpu-adapter");
        const mounted = await mountLivingOrganizationWebGPUScene({
          canvas, model: renderModel, onSelect: (nextSelection) => { if (!cancelled) setSelection(nextSelection); },
        });
        if (cancelled) { mounted.dispose(); return; }
        controller = mounted;
        setBackendPreference(mounted.backendPreference);
        setPhase("ready");
      } catch (error) {
        if (cancelled) return;
        setPhase("unavailable");
        setFailure(error instanceof Error ? error.message : "The optional spatial renderer could not initialize.");
      }
    })();
    return () => { cancelled = true; controller?.dispose(); };
  }, [renderModel]);

  return (
    <section className="living-webgpu-stage" aria-labelledby="living-webgpu-title" data-renderer-phase={phase} data-scene-authoritative="false">
      <header><div><span>M.4.0 · Renderer bootstrap gate</span><strong id="living-webgpu-title">Spatial renderer</strong></div><small>{phase === "ready" ? backendLabel(backendPreference) : phase}</small></header>
      <div className="living-webgpu-canvas-wrap">
        <canvas ref={canvasRef} className="living-webgpu-canvas" aria-hidden="true" data-testid="living-webgpu-canvas" />
        <div className="living-webgpu-overlay" aria-live="polite">
          <span>Pointer selection · optional</span>
          <strong>{selection?.label ?? "No spatial selection"}</strong>
          <small>{selection ? selection.entityType + " · " + selection.entityKey : "Selection changes view focus only; it cannot mutate AIOS."}</small>
        </div>
      </div>
      {phase === "unavailable" ? <div className="living-webgpu-fallback" role="status"><strong>Spatial renderer unavailable.</strong><span>{failure ?? "The renderer could not initialize."}</span></div> : null}
      <p className="living-webgpu-accessibility">This renderer is an enhancement. The Structured Cockpit reference below remains available for accessibility, low-power devices, unsupported graphics environments, and every core operation.</p>
    </section>
  );
}
