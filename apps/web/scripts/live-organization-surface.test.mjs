import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const read = (relativePath) => readFile(new URL(`../${relativePath}`, import.meta.url), "utf8");

test("Austria Live Organization Cockpit surface is persisted, bounded, and explicit about proof gaps", async () => {
  const [page, api, navigation, sceneComponent, sceneRenderer, cockpitLayout] = await Promise.all([
    read("app/cockpit/live-organization/page.tsx"),
    read("lib/live-organization.ts"),
    read("lib/workspace-navigation.ts"),
    read("components/LivingOrganizationScene.tsx"),
    read("lib/living-organization-scene-renderer.ts"),
    read("app/cockpit/layout.tsx"),
  ]);

  assert.match(navigation, /label: "Live Organization", href: "\/cockpit\/live-organization"/);
  assert.match(navigation, /pathname\.startsWith\("\/cockpit"\)/);

  assert.match(page, /getLatestAustriaLiveOrganization/);
  assert.match(page, /synthesizeAustriaOwner/);
  assert.match(page, /snapshot\.ready_for_owner_synthesis/);
  assert.match(page, /snapshot\.external_action_authorized/);
  assert.match(page, /snapshot\.provider_model_authority/);
  assert.match(page, /snapshot\.domain_evidence_refs/);
  assert.match(page, /snapshot\.verified_rule_refs/);
  assert.match(page, /specialist\.runtime_quality/);
  assert.match(page, /snapshot\.activities\.map/);
  assert.match(page, /Durable activity lineage/);
  assert.match(page, /Persisted organizational activity/);
  assert.match(page, /activity\.causation_activity_id/);
  assert.match(page, /Provider transcripts, tool logs, and donor event streams are not promoted to organizational truth/);
  assert.match(page, /Runtime economics & quality/);
  assert.match(page, /Persisted specialist runtime signals/);
  assert.match(page, /quality\.total_tokens/);
  assert.match(page, /quality\.estimated_cost_usd/);
  assert.match(page, /quality\.fresh_retrieval_provenance_present/);
  assert.match(page, /quality\.fallback_to_template/);
  assert.match(page, /Missing costs are not inferred as zero|missing costs are not inferred as zero/i);
  assert.match(page, /Telemetry is presentation evidence only/);
  assert.match(page, /does not create OrganizationActivity/);
  assert.match(page, /grant provider\/model authority/);
  assert.match(page, /authorize external action/);
  assert.match(page, /The Cockpit does not simulate a live organization cycle/);
  assert.match(page, /no Evidence is fabricated by the UI/);
  assert.match(page, /regulatory truth is not implied/);
  assert.match(page, /Board authentication required/);
  assert.match(page, /Board access not permitted/);
  assert.match(page, /Live organization unavailable/);
  assert.match(page, /does not infer whether a live cycle exists/);
  assert.match(page, /!loading && !error && !snapshot/);
  assert.doesNotMatch(page, /Math\.random|setInterval\(/);
  assert.doesNotMatch(page, /provider transcript.*OrganizationActivity/i);

  assert.match(api, /export type AustriaLiveRuntimeQuality/);
  assert.match(api, /runtime_quality: AustriaLiveRuntimeQuality \| null/);
  assert.match(api, /estimated_cost_usd: number \| null/);
  assert.match(api, /fresh_retrieval_provenance_present: boolean/);
  assert.match(api, /causation_activity_id: string \| null/);
  assert.match(api, /class LiveOrganizationRequestError extends Error/);
  assert.match(api, /this\.status = status/);
  assert.match(api, /throw new LiveOrganizationRequestError\(response\.status, detail\)/);
  assert.match(api, /createApiFetch\(CLIENT_API_CONFIG\)/);
  assert.match(api, /\/api\/v1\/organization\/transparency\/live-organization\/austria\/latest/);
  assert.match(api, /\/api\/v1\/organization\/live-organization\/austria\/\$\{encodeURIComponent\(rootWorkItemId\)\}\/owner-synthesis/);

  assert.match(page, /getLatestAustriaLivingScene/);
  assert.match(page, /LivingOrganizationSceneView/);
  assert.match(page, /scene\.root_work_item_id !== snapshot\.root_work_item_id/);
  assert.match(page, /does not render mixed canonical states/);
  assert.match(page, /does not synthesize one locally/);
  assert.match(api, /export type LivingSceneCoverage/);
  assert.match(api, /departments: LivingSceneDepartment\[\]/);
  assert.match(api, /missions: LivingSceneMission\[\]/);
  assert.match(api, /conversations: LivingSceneConversation\[\]/);
  assert.match(api, /incidents: LivingSceneIncident\[\]/);
  assert.match(api, /smart_objects: LivingSceneSmartObject\[\]/);
  assert.match(api, /export type LivingOrganizationScene/);
  assert.match(api, /\/api\/v1\/organization\/transparency\/live-organization\/scene\/austria\/latest/);
  assert.match(sceneComponent, /M\.3 · Canonical scene foundation/);
  assert.match(sceneComponent, /data-scene-plane="deterministic"/);
  assert.match(sceneComponent, /scene\.deterministic\.departments/);
  assert.match(sceneComponent, /scene\.deterministic\.missions/);
  assert.match(sceneComponent, /scene\.deterministic\.conversations/);
  assert.match(sceneComponent, /scene\.deterministic\.incidents/);
  assert.match(sceneComponent, /scene\.deterministic\.smart_objects/);
  assert.match(sceneComponent, /Mission Board/);
  assert.match(sceneComponent, /Presence/);
  assert.match(sceneComponent, /scene\.predictive\.enabled/);
  assert.match(sceneComponent, /scene\.environmental\.enabled/);
  assert.match(sceneComponent, /scene\.truth\.renderer_authoritative/);
  assert.match(sceneRenderer, /LIVING_SCENE_RENDERER_TARGET = "three-webgpu"/);
  assert.match(sceneRenderer, /sceneAuthoritative: false/);
  assert.doesNotMatch(sceneRenderer, /Math\.random|setInterval|fetch\(/);
  assert.match(cockpitLayout, /living-scene\.css/);

});
