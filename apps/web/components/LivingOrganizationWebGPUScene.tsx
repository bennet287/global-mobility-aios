"use client";
import { useEffect, useRef, useState } from "react";
import type { LivingSceneRenderModel } from "../lib/living-organization-scene-renderer";
import type { LivingOrganizationLensKey } from "../lib/living-organization-lenses";
import { FLOW_FIELD_TRIAL_GATES } from "../lib/living-organization-flow-trial";
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

export function LivingOrganizationWebGPUScene({
  renderModel,
  activeLens,
}: {
  renderModel: LivingSceneRenderModel;
  activeLens: LivingOrganizationLensKey;
}) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const controllerRef = useRef<LivingSceneRendererController | null>(null);
  const latestModelRef = useRef(renderModel);
  latestModelRef.current = renderModel;

  const [phase, setPhase] = useState<RendererPhase>("initializing");
  const [backend, setBackend] = useState<LivingSceneRendererBackend | null>(null);
  const [selection, setSelection] = useState<LivingSceneSelection | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [flowTrialEnabled, setFlowTrialEnabled] = useState(false);

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
        mounted.setFlowTrialEnabled(false);
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

  useEffect(() => {
    const enabled = activeLens === "flow" && flowTrialEnabled;
    controllerRef.current?.setFlowTrialEnabled(enabled);
  }, [activeLens, flowTrialEnabled]);

  return (
    <section
      className="living-webgpu-stage"
      aria-labelledby="living-webgpu-title"
      data-renderer-phase={phase}
      data-renderer-backend={backend ?? "pending"}
      data-scene-authoritative="false"
      data-active-lens={activeLens}
    >
      <header>
        <div>
          <span>M.7.4 · GPU FLOW field TRIAL · Iteration 1</span>
          <strong id="living-webgpu-title">Living spatial organization</strong>
        </div>
        <small>{phase === "ready" ? backendLabel(backend) : phase} · {activeLens.replaceAll("_", " ")} lens</small>
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
      {activeLens === "flow" ? (
        <section
          className="living-flow-trial-console"
          aria-labelledby="living-flow-trial-title"
          data-flow-trial-promotion={renderModel.flowTrial.promotionStatus}
          data-flow-trial-default-prominence={String(renderModel.flowTrial.defaultProminence)}
        >
          <header>
            <div>
              <span>TRIAL · Iteration 1 · not promoted</span>
              <strong id="living-flow-trial-title">GPU-rendered FLOW streamline field</strong>
            </div>
            <small>{backendLabel(backend)} · benchmark required</small>
          </header>
          <div className="living-flow-trial-controls" role="group" aria-label="FLOW representation comparison">
            <button
              type="button"
              aria-pressed={!flowTrialEnabled}
              onClick={() => setFlowTrialEnabled(false)}
            >
              Structured baseline only
            </button>
            <button
              type="button"
              aria-pressed={flowTrialEnabled}
              onClick={() => setFlowTrialEnabled(true)}
              disabled={phase !== "ready"}
            >
              Enable GPU field trial
            </button>
          </div>
          <div className="living-flow-trial-metrics">
            <div><strong>{renderModel.flowTrial.nodes.length}</strong><span>seeded WorkItems</span></div>
            <div><strong>{renderModel.flowTrial.paths.length}</strong><span>topology paths</span></div>
            <div><strong>{renderModel.flowTrial.dominantDerivedPathKey ? "1" : "0"}</strong><span>derived dominant cue</span></div>
            <div><strong>0</strong><span>authority paths</span></div>
          </div>
          <p>
            {renderModel.flowTrial.formula}. Animation is orientation/presentation only; it does not claim throughput,
            dependency, employee movement, or work routing authority.
          </p>
          <div className="living-flow-trial-gates">
            <span>Promotion blocked until benchmark evidence clears:</span>
            <small>≥{FLOW_FIELD_TRIAL_GATES.medianTimeImprovementPct}% faster median correct answer OR ≥{FLOW_FIELD_TRIAL_GATES.errorRateImprovementPct}% fewer errors</small>
            <small>≥{FLOW_FIELD_TRIAL_GATES.ordinaryFps} FPS ordinary · ≥{FLOW_FIELD_TRIAL_GATES.sustainedFpsFloor} FPS floor · p95 feedback ≤{FLOW_FIELD_TRIAL_GATES.p95FeedbackMs}ms</small>
            <small>≥{FLOW_FIELD_TRIAL_GATES.mainThreadComputeImprovementPct}% main-thread compute improvement OR capability that the control cannot sustain above the FPS floor</small>
          </div>
          <footer>{renderModel.flowTrial.canonicalBasis}</footer>
        </section>
      ) : null}
      {phase === "unavailable" ? (
        <div className="living-webgpu-fallback" role="status">
          <strong>Spatial renderer unavailable.</strong>
          <span>{failure ?? "The renderer could not initialize."}</span>
        </div>
      ) : null}
      <p className="living-webgpu-accessibility">
        Employee motion remains presentation-only workspace motion derived from canonical semantic state.
        M.4.1 motion discipline is preserved: presence and locomotion are not asserted. The M.7.4 FLOW field is a
        default-off derived presentation over the maintained Structured FLOW baseline. It is not promoted, does not claim
        throughput or dependency truth, cannot mutate work, and no lens/query/trial control can bypass AIOS governance.
        The Structured Cockpit remains available for every core operation.
      </p>
    </section>
  );
}
