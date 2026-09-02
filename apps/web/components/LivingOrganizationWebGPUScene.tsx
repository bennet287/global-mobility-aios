"use client";
import { useEffect, useRef, useState } from "react";
import type { LivingSceneRenderModel } from "../lib/living-organization-scene-renderer";
import type {
  LivingSceneRendererBackend,
  LivingSceneRendererController,
  LivingSceneSelection,
} from "../lib/living-organization-webgpu-adapter";

type RendererPhase = "initializing" | "ready" | "unavailable";

function backendLabel(value: LivingSceneRendererBackend | null): string {
  if (value === "webgpu") return "WebGPU";
  if (value === "webgl2") return "WebGL2 fallback";
  if (value === "unknown") return "Unknown renderer backend";
  return "Detecting renderer backend";
}

export function LivingOrganizationWebGPUScene({ renderModel }: { renderModel: LivingSceneRenderModel }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const controllerRef = useRef<LivingSceneRendererController | null>(null);
  const latestModelRef = useRef(renderModel);
  latestModelRef.current = renderModel;

  const [phase, setPhase] = useState<RendererPhase>("initializing");
  const [backend, setBackend] = useState<LivingSceneRendererBackend | null>(null);
  const [selection, setSelection] = useState<LivingSceneSelection | null>(null);
  const [failure, setFailure] = useState<string | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let cancelled = false;
    const initialModel = latestModelRef.current;

    setPhase("initializing");
    setBackend(null);
    setFailure(null);
    setSelection(null);

    void (async () => {
      try {
        const { mountLivingOrganizationWebGPUScene } = await import("../lib/living-organization-webgpu-adapter");
        const mounted = await mountLivingOrganizationWebGPUScene({
          canvas,
          model: initialModel,
          onSelect: (nextSelection) => {
            if (!cancelled) setSelection(nextSelection);
          },
        });
        if (cancelled) {
          mounted.dispose();
          return;
        }

        controllerRef.current = mounted;
        if (latestModelRef.current !== initialModel) {
          mounted.updateModel(latestModelRef.current);
        }
        setBackend(mounted.rendererBackend);
        setPhase("ready");
      } catch (error) {
        if (cancelled) return;
        setPhase("unavailable");
        setFailure(error instanceof Error ? error.message : "The optional spatial renderer could not initialize.");
      }
    })();

    return () => {
      cancelled = true;
      const controller = controllerRef.current;
      controllerRef.current = null;
      controller?.dispose();
    };
  }, []);

  useEffect(() => {
    latestModelRef.current = renderModel;
    const controller = controllerRef.current;
    if (!controller) return;

    try {
      controller.updateModel(renderModel);
      setFailure(null);
      setPhase("ready");
    } catch (error) {
      setPhase("unavailable");
      setFailure(error instanceof Error ? error.message : "The optional spatial renderer could not update.");
    }
  }, [renderModel]);

  return (
    <section
      className="living-webgpu-stage"
      aria-labelledby="living-webgpu-title"
      data-renderer-phase={phase}
      data-renderer-backend={backend ?? "pending"}
      data-scene-authoritative="false"
    >
      <header>
        <div>
          <span>M.4.1 · Animated Employees V1</span>
          <strong id="living-webgpu-title">Living spatial organization</strong>
        </div>
        <small>{phase === "ready" ? backendLabel(backend) : phase}</small>
      </header>
      <div className="living-webgpu-canvas-wrap">
        <canvas
          ref={canvasRef}
          className="living-webgpu-canvas"
          aria-hidden="true"
          data-testid="living-webgpu-canvas"
        />
        <div className="living-webgpu-overlay" aria-live="polite">
          <span>Pointer selection · optional</span>
          <strong>{selection?.label ?? "No spatial selection"}</strong>
          <small>{selection ? selection.entityType + " · " + selection.entityKey : "No view focus selected."}</small>
          <small data-selection-authority="none">Selection changes view focus only; it cannot mutate AIOS.</small>
        </div>
      </div>
      {phase === "unavailable" ? (
        <div className="living-webgpu-fallback" role="status">
          <strong>Spatial renderer unavailable.</strong>
          <span>{failure ?? "The renderer could not initialize."}</span>
        </div>
      ) : null}
      <p className="living-webgpu-accessibility">
        Employee motion is presentation-only workspace motion derived from canonical semantic state.
        Presence and locomotion are not asserted in M.4.1; walking, talking, room entry and handoffs remain disabled
        until later canonical collaboration/location semantics exist. The Structured Cockpit remains available for every core operation.
      </p>
    </section>
  );
}
