"use client";
import { useMemo } from "react";
import { LivingOrganizationWebGPUScene } from "./LivingOrganizationWebGPUScene";
import type { LivingOrganizationScene } from "../lib/live-organization";
import {
  LIVING_SCENE_RENDERER_TARGET,
  buildLivingSceneRenderModel,
} from "../lib/living-organization-scene-renderer";
import { titleCase } from "../lib/utils";

function initials(value: string): string {
  const parts = value
    .split(/[_\s-]+/)
    .map((item) => item.trim())
    .filter(Boolean);
  if (!parts.length) return "AI";
  return parts.slice(0, 2).map((item) => item[0]?.toUpperCase()).join("");
}

function shortId(value: string | null): string {
  return value ? value.slice(0, 8) : "—";
}

function timestampLabel(value: string): string {
  return `${value.slice(0, 16).replace("T", " ")} UTC`;
}

export function LivingOrganizationSceneView({ scene }: { scene: LivingOrganizationScene }) {
  const renderModel = useMemo(() => buildLivingSceneRenderModel(scene), [scene]);
  const blockersByWork = new Map<string, number>();
  for (const blocker of scene.deterministic.blockers) {
    if (!blocker.work_item_id) continue;
    blockersByWork.set(blocker.work_item_id, (blockersByWork.get(blocker.work_item_id) ?? 0) + 1);
  }
  const openConversationsByParticipant = new Map<string, number>();
  for (const conversation of scene.deterministic.conversations) {
    if (conversation.status !== "open") continue;
    for (const positionKey of conversation.participant_position_keys) {
      openConversationsByParticipant.set(
        positionKey,
        (openConversationsByParticipant.get(positionKey) ?? 0) + 1,
      );
    }
  }

  return (
    <section className="living-scene-shell" aria-labelledby="living-scene-title">
      <header className="living-scene-header">
        <div>
          <span className="premium-label">M.5 · Canonical collaboration</span>
          <h3 id="living-scene-title">Living Organization Scene</h3>
          <p>
            A spatial projection of persisted AIOS organization state. Geometry is presentation-only;
            employee, work, blocker, decision, and relationship semantics come from the backend scene contract.
          </p>
        </div>
        <div className="living-scene-contract">
          <span>{scene.contract_version}</span>
          <strong>{LIVING_SCENE_RENDERER_TARGET}</strong>
          <small>advanced renderer target · not authority</small>
        </div>
      </header>

      <div className="living-scene-coverage" aria-label="Scene coverage">
        <div><span>Departments</span><strong>{scene.deterministic.departments.length}</strong><small>{titleCase(scene.coverage.departments)}</small></div>
        <div><span>Missions</span><strong>{scene.deterministic.missions.length}</strong><small>{titleCase(scene.coverage.missions)}</small></div>
        <div><span>Conversations</span><strong>{scene.deterministic.conversations.length}</strong><small>{titleCase(scene.coverage.conversations)}</small></div>
        <div><span>Handoffs</span><strong>{scene.deterministic.handoffs.length}</strong><small>{titleCase(scene.coverage.handoffs)}</small></div>
        <div><span>Incidents</span><strong>{scene.deterministic.incidents.length}</strong><small>{titleCase(scene.coverage.incidents)}</small></div>
      </div>

      <div className="living-scene-planes" aria-label="Living Organization projection planes">
        <div className="scene-plane deterministic">
          <span>Plane 1</span>
          <strong>Deterministic</strong>
          <small>canonical projection · non-authoritative view</small>
        </div>
        <div className="scene-plane reserved">
          <span>Plane 2</span>
          <strong>Phantom Futures</strong>
          <small>{scene.predictive.enabled ? titleCase(scene.predictive.status) : "Reserved for M.9 · disabled"}</small>
        </div>
        <div className="scene-plane reserved">
          <span>Plane 3</span>
          <strong>Environmental memory</strong>
          <small>{scene.environmental.enabled ? titleCase(scene.environmental.status) : "Reserved for M.9 · disabled"}</small>
        </div>
      </div>

      <LivingOrganizationWebGPUScene renderModel={renderModel} />

      <div className="living-structured-reference" id="living-structured-reference">
        <div>
          <span>STRUCTURED · permanent product surface</span>
          <strong>Canonical scene reference</strong>
        </div>
        <p>
          The Structured Cockpit remains the accessible, low-power, exact-record fallback for every core operation.
          The spatial renderer may improve orientation and selection, but it never replaces canonical inspection.
        </p>
      </div>

      <div className="living-scene-smart-strip" aria-label="Canonical department topology">
        {renderModel.departmentZones.map(({ department, employeeSlots, workItems, zoneIndex }) => (
          <article key={department.department_key} data-department-zone={department.department_key} data-zone-index={zoneIndex}>
            <span>Department zone</span>
            <strong>{department.label}</strong>
            <div><b>{employeeSlots.length}</b><small>employees · {workItems.length} WorkItems</small></div>
            <p>
              {employeeSlots.length
                ? employeeSlots.map(({ employee }) => employee.position_key.replaceAll("_", " ")).join(" · ")
                : "No projected employee in this department"}
            </p>
            <p>{department.active_blocker_count} active blockers · {department.canonical_basis}</p>
          </article>
        ))}
      </div>

      <div className="living-scene-floor" data-scene-plane="deterministic">
        <article className="living-scene-room mission-room">
          <header>
            <div>
              <span>Mission Room</span>
              <strong>{renderModel.missionRoom?.label ?? scene.objective_key}</strong>
            </div>
            <small>{renderModel.missionRoom ? titleCase(renderModel.missionRoom.state) : "No room projection"}</small>
          </header>

          <div className="living-scene-employee-grid">
            {renderModel.employeeSlots.map(({ employee, workItem, slot }) => {
              const blockerCount = employee.work_item_id ? blockersByWork.get(employee.work_item_id) ?? 0 : 0;
              const conversationCount = openConversationsByParticipant.get(employee.position_key) ?? 0;
              return (
                <article
                  key={employee.position_key}
                  className={`living-scene-employee state-${employee.semantic_state}`}
                  data-scene-slot={slot}
                  data-presence-state={employee.presence_state}
                  data-department={employee.department}
                >
                  <div className="scene-avatar" aria-hidden="true">{initials(employee.position_key)}</div>
                  <div className="scene-employee-copy">
                    <span>{employee.title}</span>
                    <strong>{employee.position_key.replaceAll("_", " ")}</strong>
                    <small>{titleCase(employee.semantic_state)} · {employee.authority_level}</small>
                  </div>
                  <div className="scene-work-chip">
                    <span>Work</span>
                    <strong>{workItem?.title ?? "No linked WorkItem"}</strong>
                    <small>
                      {workItem ? `${titleCase(workItem.status)} · ${shortId(workItem.work_item_id)}` : employee.state_reason}
                    </small>
                  </div>
                  <div className="scene-truth-row">
                    <span>Presence</span>
                    <strong>{titleCase(employee.presence_state)}</strong>
                  </div>
                  {blockerCount ? <span className="scene-blocker-badge">{blockerCount} blocker{blockerCount === 1 ? "" : "s"}</span> : null}
                  {conversationCount ? (
                    <span className="scene-conversation-badge">
                      Canonical conversation · {conversationCount}
                    </span>
                  ) : null}
                </article>
              );
            })}
          </div>

          <div className="scene-collaboration-grid">
            <section aria-labelledby="canonical-conversations-title">
              <header>
                <div>
                  <span>Mission collaboration</span>
                  <strong id="canonical-conversations-title">CANONICAL CONVERSATIONS</strong>
                </div>
                <small>{scene.deterministic.conversations.length}</small>
              </header>
              {scene.deterministic.conversations.length ? (
                <div className="scene-decision-list">
                  {scene.deterministic.conversations.map((conversation) => (
                    <details key={conversation.conversation_id}>
                      <summary>
                        <span>{titleCase(conversation.status)} · {conversation.participant_position_keys.length} participants</span>
                        <strong>{conversation.summary}</strong>
                        <small>Work {shortId(conversation.work_item_id)} · {timestampLabel(conversation.lifecycle_at)}</small>
                      </summary>
                      <div>
                        <span>Participants</span>
                        <strong>{conversation.participant_position_keys.map((value) => titleCase(value)).join(" · ")}</strong>
                        <small>Opened Activity {shortId(conversation.opened_activity_id)} · Latest Activity {shortId(conversation.latest_activity_id)}</small>
                        <small>{conversation.canonical_basis} · lifecycle {timestampLabel(conversation.lifecycle_at)}</small>
                        <small>Authority effect {conversation.authority_effect} · transcript {conversation.transcript_persisted ? "persisted" : "not persisted"}</small>
                      </div>
                    </details>
                  ))}
                </div>
              ) : (
                <p>No persisted conversation lifecycle is linked to these scene WorkItems.</p>
              )}
            </section>

            <section aria-labelledby="canonical-handoffs-title">
              <header>
                <div>
                  <span>Governed assignment history</span>
                  <strong id="canonical-handoffs-title">CANONICAL HANDOFFS</strong>
                </div>
                <small>{scene.deterministic.handoffs.length}</small>
              </header>
              {scene.deterministic.handoffs.length ? (
                <div className="scene-decision-list">
                  {scene.deterministic.handoffs.map((handoff) => (
                    <details key={handoff.activity_id}>
                      <summary>
                        <span>{titleCase(handoff.status)} · Work {shortId(handoff.work_item_id)}</span>
                        <strong>{titleCase(handoff.previous_position_key)} ↓ {titleCase(handoff.assigned_position_key)}</strong>
                        <small>{timestampLabel(handoff.occurred_at)}</small>
                      </summary>
                      <div>
                        <span>Activity {shortId(handoff.activity_id)}</span>
                        <strong>{handoff.causation_activity_id ? `Governed causation ${shortId(handoff.causation_activity_id)}` : "No governed causation Activity linked"}</strong>
                        <small>{timestampLabel(handoff.occurred_at)} · {handoff.canonical_basis}</small>
                      </div>
                    </details>
                  ))}
                </div>
              ) : (
                <p>No governed WorkItem reassignment is linked to this Mission Room.</p>
              )}
            </section>
          </div>

          <footer>
            <span>{scene.deterministic.missions[0]?.participant_position_keys.length ?? renderModel.employeeSlots.length} participants</span>
            <span>{scene.deterministic.relationships.length} canonical relationships</span>
          </footer>
        </article>

        <article className="living-scene-room evidence-room">
          <header>
            <div><span>Evidence Lab</span><strong>{renderModel.evidenceLab?.label ?? "Evidence Lab"}</strong></div>
            <small>{renderModel.evidenceLab ? titleCase(renderModel.evidenceLab.state) : "Unavailable"}</small>
          </header>
          <div className="scene-room-metric">
            <strong>{renderModel.evidenceLab?.metric_value ?? 0}</strong>
            <span>{renderModel.evidenceLab?.metric_label ?? "Evidence references"}</span>
          </div>
          <p>{renderModel.evidenceLab?.canonical_basis ?? "No Evidence Lab projection is available."}</p>
        </article>

        <article className={`living-scene-room board-room ${renderModel.boardRoom?.state === "attention" ? "attention" : ""}`}>
          <header>
            <div><span>Board Room</span><strong>{renderModel.boardRoom?.label ?? "Board Room"}</strong></div>
            <small>{renderModel.boardRoom ? titleCase(renderModel.boardRoom.state) : "Unavailable"}</small>
          </header>
          <div className="scene-room-metric">
            <strong>{renderModel.boardRoom?.metric_value ?? 0}</strong>
            <span>{renderModel.boardRoom?.metric_label ?? "Board decisions"}</span>
          </div>
          {scene.deterministic.decisions.length ? (
            <div className="scene-decision-list">
              {scene.deterministic.decisions.map((decision) => (
                <div key={decision.decision_id}>
                  <span>{decision.authority_level} · {titleCase(decision.status)}</span>
                  <strong>{decision.title}</strong>
                  <small>{decision.is_current ? "Current decision" : "Superseded"} · {shortId(decision.work_item_id)}</small>
                </div>
              ))}
            </div>
          ) : (
            <p>No ExecutiveDecision is linked to the current scene WorkItems.</p>
          )}
        </article>

        <article className="living-scene-room blocker-room">
          <header>
            <div><span>Friction lane</span><strong>Current blockers</strong></div>
            <small>{scene.deterministic.blockers.length}</small>
          </header>
          {scene.deterministic.blockers.length ? (
            <div className="scene-blocker-list">
              {scene.deterministic.blockers.map((blocker) => (
                <div key={blocker.blocker_id}>
                  <span>{titleCase(blocker.severity)} · {titleCase(blocker.status)}</span>
                  <strong>{blocker.title}</strong>
                  <small>{blocker.requires_human_action ? "Human action required" : "No human action flag"} · Work {shortId(blocker.work_item_id)}</small>
                </div>
              ))}
            </div>
          ) : (
            <p>No active blocker is projected into this scene.</p>
          )}
        </article>
      </div>

      <div className="living-scene-smart-strip" aria-label="Living Organization Smart Objects">
        {scene.deterministic.smart_objects.map((item) => (
          <article key={item.object_key}>
            <span>{titleCase(item.object_type)}</span>
            <strong>{item.label}</strong>
            <div><b>{item.metric_value}</b><small>{item.metric_label}</small></div>
            <p>{titleCase(item.state)} · {item.canonical_basis}</p>
          </article>
        ))}
      </div>

      <div className="living-scene-truth">
        <div>
          <span>Canonical authority</span>
          <strong>{scene.truth.canonical_authority}</strong>
        </div>
        <div>
          <span>Scene authority</span>
          <strong>{scene.truth.scene_authoritative ? "Present" : "None"}</strong>
        </div>
        <div>
          <span>Renderer authority</span>
          <strong>{scene.truth.renderer_authoritative ? "Present" : "None"}</strong>
        </div>
        <div>
          <span>Scene mutations</span>
          <strong>{scene.truth.scene_mutations_allowed ? "Allowed" : "Disabled"}</strong>
        </div>
      </div>
    </section>
  );
}
