import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const read = (relativePath) => readFile(new URL(`../${relativePath}`, import.meta.url), "utf8");

test("M.4.0 WebGPU renderer remains a non-authoritative optional projection", async () => {
  const [adapter, rendererComponent, sceneComponent, packageJson, packageLock] = await Promise.all([
    read("lib/living-organization-webgpu-adapter.ts"),
    read("components/LivingOrganizationWebGPUScene.tsx"),
    read("components/LivingOrganizationScene.tsx"),
    read("package.json"),
    read("package-lock.json"),
  ]);

  assert.match(packageJson, /"three": "0\.185\.1"/);
  assert.match(packageLock, /"node_modules\/three"/);
  assert.match(packageLock, /three-0\.185\.1\.tgz/);
  assert.match(adapter, /from "three\/webgpu"/);
  assert.match(adapter, /new WebGPURenderer/);
  assert.match(adapter, /await renderer\.init\(\)/);
  assert.match(adapter, /resolveActualBackend/);
  assert.match(adapter, /isWebGPUBackend/);
  assert.match(adapter, /isWebGLBackend/);
  assert.match(adapter, /rendererBackend = backend/);
  assert.match(adapter, /rendererBackend: LivingSceneRendererBackend/);
  assert.match(adapter, /"webgpu" \| "webgl2" \| "unknown"/);
  assert.match(adapter, /new Raycaster\(\)/);
  assert.match(adapter, /intersectObjects\(pickTargets, false\)/);
  assert.match(adapter, /rendererAuthority = "none"/);
  assert.match(adapter, /sceneAuthoritative = "false"/);
  assert.match(adapter, /assertLivingSceneRendererModelNonAuthoritative\(model\)/);
  assert.match(adapter, /sceneAuthoritative = "false"/);
  assert.match(adapter, /acquireLivingSceneRendererCanvasLease\(canvas\)/);
  assert.match(adapter, /rendererActiveMounts = "1"/);
  assert.match(adapter, /rendererActiveMounts = "0"/);
  assert.match(adapter, /canvasLease\.release\(\)/);
  assert.match(adapter, /updateModel: \(model: LivingSceneRenderModel\) => void/);
  assert.match(adapter, /const clearProjection = \(\) =>/);
  assert.match(adapter, /rendererModelRevision/);
  assert.match(adapter, /rendererProjectionResources/);
  assert.match(adapter, /updateModel\(model\)/);
  assert.doesNotMatch(adapter, /fetch\(|XMLHttpRequest|synthesizeAustriaOwner|semantic_state|work_status|authority_level/);

  assert.match(rendererComponent, /Living spatial organization/);
  assert.match(rendererComponent, /data-renderer-backend/);
  assert.match(rendererComponent, /Unknown renderer backend/);
  assert.match(rendererComponent, /Structured Cockpit remains available for every core operation/);
  assert.match(rendererComponent, /aria-hidden="true"/);
  assert.match(rendererComponent, /Selection changes view focus only; it cannot mutate AIOS/);
  assert.match(rendererComponent, /data-selection-authority="none"/);
  assert.match(rendererComponent, /controller\.updateModel\(renderModel\)/);
  assert.match(rendererComponent, /useEffect\(\(\) => \{/);
  assert.match(sceneComponent, /LivingOrganizationWebGPUScene/);
  assert.match(sceneComponent, /STRUCTURED · permanent product surface/);
  assert.match(sceneComponent, /accessible, low-power, exact-record fallback for every core operation/);
});


test("M.4.1 employee animation consumes bounded presentation state", async () => {
  const [presentation, renderModel, adapter, rendererComponent] = await Promise.all([
    read("lib/living-organization-employee-presentation.ts"),
    read("lib/living-organization-scene-renderer.ts"),
    read("lib/living-organization-webgpu-adapter.ts"),
    read("components/LivingOrganizationWebGPUScene.tsx"),
  ]);

  assert.match(presentation, /focused_work/);
  assert.match(presentation, /blocked_wait/);
  assert.match(presentation, /awaiting_attention/);
  assert.match(presentation, /queued_wait/);
  assert.match(presentation, /settled_idle/);
  assert.match(presentation, /neutral_static/);
  assert.match(presentation, /locomotionAllowed: false/);
  assert.match(presentation, /presenceClaimed: false/);

  assert.match(renderModel, /deriveLivingEmployeePresentation/);
  assert.match(renderModel, /presentation: LivingEmployeePresentation/);

  assert.match(adapter, /SphereGeometry/);
  assert.match(adapter, /new Group\(\)/);
  assert.match(adapter, /setAnimationLoop\(animate\)/);
  assert.match(adapter, /animationScope = "workspace-representation"/);
  assert.match(adapter, /locomotionEnabled = "false"/);
  assert.match(adapter, /presenceClaimed = "false"/);
  assert.match(adapter, /animationProof = "motion-observed"/);
  assert.match(adapter, /employeeActors = \[\]/);
  assert.doesNotMatch(adapter, /conversation_state|handoff_state|walking_state|room_entry_state/);

  assert.match(rendererComponent, /M\.6 · Smart Objects \+ live Board Room/);
  assert.match(rendererComponent, /M\.4\.1 motion discipline is preserved/);
  assert.match(adapter, /smartObjectCount/);
  assert.match(adapter, /createLivingSceneSelection\("smart_object"/);
});
