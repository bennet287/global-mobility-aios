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
  assert.match(adapter, /new Raycaster\(\)/);
  assert.match(adapter, /intersectObjects\(pickTargets, false\)/);
  assert.match(adapter, /rendererAuthority = "none"/);
  assert.match(adapter, /sceneAuthoritative = "false"/);
  assert.match(adapter, /refuses an authoritative scene model/);
  assert.doesNotMatch(adapter, /fetch\(|XMLHttpRequest|synthesizeAustriaOwner|semantic_state|work_status|authority_level/);

  assert.match(rendererComponent, /M\.4\.0 · Renderer bootstrap gate/);
  assert.match(rendererComponent, /Structured Cockpit reference below remains available/);
  assert.match(rendererComponent, /aria-hidden="true"/);
  assert.match(rendererComponent, /Selection changes view focus only; it cannot mutate AIOS/);
  assert.match(sceneComponent, /LivingOrganizationWebGPUScene/);
  assert.match(sceneComponent, /STRUCTURED · permanent product surface/);
  assert.match(sceneComponent, /accessible, low-power, exact-record fallback for every core operation/);
});
