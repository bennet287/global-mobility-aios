"use client";
import { useMemo, useState } from "react";
import { LivingOrganizationWebGPUScene } from "./LivingOrganizationWebGPUScene";
import type { LivingOrganizationScene } from "../lib/live-organization";
import {
  LIVING_SCENE_RENDERER_TARGET,
  buildLivingSceneRenderModel,
} from "../lib/living-organization-scene-renderer";
import {
  OWNER_LENS_VIEW_COMMANDS,
  buildLivingOrganizationLenses,
  isLivingOrganizationLensFocused,
  isLivingOrganizationLensSelectable,
  smartObjectLensTags,
  type LivingOrganizationLensKey,
} from "../lib/living-organization-lenses";
import {
  OWNER_ANALYTICAL_QUERIES,
  buildStructuredFlowBaseline,
  evaluateOwnerAnalyticalQuery,
  type OwnerAnalyticalQueryKey,
} from "../lib/living-organization-analytics";
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

function durationLabel(value: number | null): string {
  if (value === null) return "Not recorded";
  const minutes = Math.floor(value / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  return remainder ? `${hours}h ${remainder}m` : `${hours}h`;
}

export function LivingOrganizationSceneView({ scene }: { scene: LivingOrganizationScene }) {
  const renderModel = useMemo(() => buildLivingSceneRenderModel(scene), [scene]);
  const [requestedLens, setRequestedLens] = useState<LivingOrganizationLensKey>("organization");
  const [activeQueryKey, setActiveQueryKey] = useState<OwnerAnalyticalQueryKey | null>(null);
  const lenses = useMemo(() => buildLivingOrganizationLenses(scene), [scene]);
  const flowBaseline = useMemo(() => buildStructuredFlowBaseline(scene), [scene]);
  const ownerQueryResults = useMemo(
    () => OWNER_ANALYTICAL_QUERIES.map((query) => evaluateOwnerAnalyticalQuery(scene, query.key)),
    [scene],
  );
  const activeQueryResult = activeQueryKey
    ? ownerQueryResults.find((result) => result.key === activeQueryKey) ?? null
    : null;
  const requestedLensDescriptor = lenses.find((lens) => lens.key === requestedLens);
  const activeLens = requestedLensDescriptor && isLivingOrganizationLensSelectable(requestedLensDescriptor)
    ? requestedLens
    : "organization";
  const activeLensDescriptor = lenses.find((lens) => lens.key === activeLens) ?? lenses[0];
  const focusClass = (tags: readonly LivingOrganizationLensKey[]) =>
    isLivingOrganizationLensFocused(activeLens, tags) ? "" : " lens-deemphasized";
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
    <section className="living-scene-shell" aria-labelledby="living-scene-title" data-active-lens={activeLens}>
      <header className="living-scene-header">
        <div>
          <span className="premium-label">M.7.2 · Structured FLOW + Owner analytical queries</span>
          <h3 id="living-scene-title">Living Organization Scene</h3>
          <p>
            A spatial projection of persisted AIOS organization state. Geometry is presentation-only;
            employee, work, blocker, decision, Owner-action, risk, and relationship semantics come from the backend scene contract.
            Lenses change local view emphasis only; structured FLOW and Owner queries are deterministic read models.
            They do not create organizational state, authority, or a second truth store.
          </p>
        </div>
        <div className="living-scene-contract">
          <span>{scene.contract_version}</span>
          <strong>{LIVING_SCENE_RENDERER_TARGET}</strong>
          <small>advanced renderer target · not authority</small>
        </div>
      </header>

      <section className="living-lens-console" aria-labelledby="living-lens-console-title">
        <header>
          <div>
            <span>Owner command mode · view-only foundation</span>
            <strong id="living-lens-console-title">Organization Lenses</strong>
          </div>
          <small>No POST · no canonical mutation</small>
        </header>
        <div className="living-lens-grid" role="toolbar" aria-label="Organization lenses">
          {lenses.map((lens) => {
            const selectable = isLivingOrganizationLensSelectable(lens);
            return (
              <button
                key={lens.key}
                type="button"
                data-lens-key={lens.key}
                data-lens-availability={lens.availability}
                aria-pressed={activeLens === lens.key}
                disabled={!selectable}
                onClick={() => {
                  setRequestedLens(lens.key);
                  setActiveQueryKey(null);
                }}
                title={lens.canonicalBasis}
              >
                <span>{lens.label}</span>
                <strong>{lens.count ?? "—"}</strong>
                <small>{titleCase(lens.availability)}</small>
              </button>
            );
          })}
        </div>
        <div className="living-owner-lens-commands" aria-label="Owner view commands">
          <span>Read-only Owner view commands</span>
          <div>
            {OWNER_LENS_VIEW_COMMANDS.map((command) => (
              <button
                key={command.label}
                type="button"
                onClick={() => {
                  setRequestedLens(command.lens);
                  setActiveQueryKey(null);
                }}
              >
                {command.label}
              </button>
            ))}
          </div>
        </div>
        <div className="living-owner-analytical-commands" aria-label="Owner analytical queries">
          <span>Deterministic Owner queries</span>
          <div>
            {ownerQueryResults.map((result) => (
              <button
                key={result.key}
                type="button"
                data-owner-query={result.key}
                data-query-status={result.status}
                aria-pressed={activeQueryKey === result.key}
                onClick={() => {
                  setActiveQueryKey(result.key);
                  const lens = lenses.find((item) => item.key === result.lens);
                  if (lens && isLivingOrganizationLensSelectable(lens)) setRequestedLens(result.lens);
                }}
              >
                <span>{result.label}</span>
                <small>{titleCase(result.status)}</small>
              </button>
            ))}
          </div>
        </div>
                <div className="living-lens-status" role="status" data-lens-availability={activeLensDescriptor.availability}>
          <span>Active lens · {activeLensDescriptor.label}</span>
          <strong>{activeLensDescriptor.summary}</strong>
          <small>{activeLensDescriptor.canonicalBasis}</small>
        </div>
        {activeQueryResult ? (
          <div
            className="living-owner-query-result"
            role="status"
            data-owner-query-result={activeQueryResult.key}
            data-query-status={activeQueryResult.status}
          >
            <span>{activeQueryResult.label} · {titleCase(activeQueryResult.status)}</span>
            <strong>{activeQueryResult.summary}</strong>
            {activeQueryResult.items.length ? (
              <ul>
                {activeQueryResult.items.map((item) => (
                  <li key={`${item.kind}:${item.id}`}>
                    <b>{item.label}</b>
                    <small>{item.detail} · {shortId(item.id)}</small>
                  </li>
                ))}
              </ul>
            ) : null}
            <small>{activeQueryResult.canonicalBasis}</small>
            {activeQueryResult.limitation ? <small>Limit: {activeQueryResult.limitation}</small> : null}
          </div>
        ) : null}
      </section>

      <div className="living-scene-coverage" aria-label="Scene coverage">
        <div><span>Departments</span><strong>{scene.deterministic.departments.length}</strong><small>{titleCase(scene.coverage.departments)}</small></div>
        <div><span>Missions</span><strong>{scene.deterministic.missions.length}</strong><small>{titleCase(scene.coverage.missions)}</small></div>
        <div><span>Blockers</span><strong>{scene.deterministic.blockers.length}</strong><small>{titleCase(scene.coverage.blockers)}</small></div>
        <div><span>Owner actions</span><strong>{scene.deterministic.human_actions.length}</strong><small>{titleCase(scene.coverage.human_actions)}</small></div>
        <div><span>Risks</span><strong>{scene.deterministic.risk_escalations.length}</strong><small>{titleCase(scene.coverage.risk_escalations)}</small></div>
        <div><span>Conversations</span><strong>{scene.deterministic.conversations.length}</strong><small>{titleCase(scene.coverage.conversations)}</small></div>
        <div><span>Handoffs</span><strong>{scene.deterministic.handoffs.length}</strong><small>{titleCase(scene.coverage.handoffs)}</small></div>
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

      <LivingOrganizationWebGPUScene renderModel={renderModel} activeLens={activeLens} />

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

      <section
        className={`living-flow-baseline${focusClass(["flow"])}`}
        aria-labelledby="living-flow-title"
        data-flow-authoritative="false"
      >
        <header>
          <div>
            <span>FLOW · maintained structured baseline</span>
            <strong id="living-flow-title">Directed work routing & bottleneck signals</strong>
          </div>
          <small>GPU fluid/field TRIAL not promoted</small>
        </header>
        <div className="living-flow-summary">
          <div><strong>{flowBaseline.workItemCount}</strong><span>WorkItems</span></div>
          <div><strong>{flowBaseline.activeWorkItemCount}</strong><span>Active</span></div>
          <div><strong>{flowBaseline.blockedWorkItemCount}</strong><span>Blocked</span></div>
          <div><strong>{flowBaseline.ownerAttentionWorkItemCount}</strong><span>Owner attention</span></div>
          <div><strong>{flowBaseline.overdueWorkItemCount}</strong><span>Overdue</span></div>
          <div><strong>{flowBaseline.handoffCount}</strong><span>Handoffs</span></div>
        </div>
        <div className="living-flow-columns">
          <section aria-labelledby="living-flow-work-title">
            <header><strong id="living-flow-work-title">Work nodes</strong><small>{flowBaseline.nodes.length}</small></header>
            <div className="living-flow-node-list">
              {flowBaseline.nodes.map((node) => (
                <article key={node.workItemId} data-flow-work={node.workItemId} data-overdue={String(node.overdue)}>
                  <span>{titleCase(node.status)} · {node.riskLevel} · {node.priority}</span>
                  <strong>{node.title}</strong>
                  <small>{node.assignedPositionKey.replaceAll("_", " ")} · age {durationLabel(node.elapsedSeconds)}</small>
                  <small>
                    {node.blockerCount} blockers
                    {node.oldestBlockerSeconds !== null ? ` · oldest ${durationLabel(node.oldestBlockerSeconds)}` : ""}
                    {" · "}{node.handoffCount} handoffs · {node.ownerAttentionCount} Owner signals
                  </small>
                </article>
              ))}
            </div>
          </section>
          <section aria-labelledby="living-flow-edge-title">
            <header><strong id="living-flow-edge-title">Directed topology</strong><small>{flowBaseline.parentEdgeCount}</small></header>
            <div className="living-flow-edge-list">
              {flowBaseline.edges.length ? flowBaseline.edges.map((edge) => (
                <div key={edge.edgeKey}>
                  <span>{shortId(edge.sourceWorkItemId)}</span>
                  <b>→</b>
                  <span>{shortId(edge.targetWorkItemId)}</span>
                  <small>Parent topology · not dependency truth</small>
                </div>
              )) : <p>No parent topology edge is projected.</p>}
            </div>
            <header className="living-flow-handoff-header"><strong>Governed handoff history</strong><small>{flowBaseline.handoffs.length}</small></header>
            <div className="living-flow-edge-list">
              {flowBaseline.handoffs.length ? flowBaseline.handoffs.map((handoff) => (
                <div key={handoff.activityId}>
                  <span>{titleCase(handoff.previousPositionKey)}</span>
                  <b>→</b>
                  <span>{titleCase(handoff.assignedPositionKey)}</span>
                  <small>Work {shortId(handoff.workItemId)} · {timestampLabel(handoff.occurredAt)}</small>
                </div>
              )) : <p>No governed handoff is projected.</p>}
            </div>
          </section>
        </div>
        <footer>{flowBaseline.canonicalBasis}</footer>
      </section>

      <div className="living-scene-smart-strip" aria-label="Canonical department topology">
        {renderModel.departmentZones.map(({ department, employeeSlots, workItems, zoneIndex }) => (
          <article
            key={department.department_key}
            className={focusClass(["mission", "flow"])}
            data-department-zone={department.department_key}
            data-zone-index={zoneIndex}
          >
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

      <div className="living-scene-floor" data-scene-plane="deterministic" data-active-lens={activeLens}>
        <article className={`living-scene-room mission-room${focusClass(["mission", "flow"])}`}>
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

        <article className={`living-scene-room evidence-room${focusClass(["evidence"])}`}>
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

        <article className={`living-scene-room board-room ${renderModel.boardRoom?.state === "attention" ? "attention" : ""}${focusClass(["decisions", "risk"])}`}>
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
                <details key={decision.decision_id}>
                  <summary>
                    <span>
                      {decision.authority_level} · {titleCase(decision.status)} ·
                      {decision.required_owner_action ? " Owner action required" : " No Owner action"}
                    </span>
                    <strong>{decision.title}</strong>
                    <small>
                      {decision.is_current ? "Current decision" : "Superseded"} · Work {shortId(decision.work_item_id)} · Evidence {decision.evidence_items.length}
                    </small>
                  </summary>
                  <div>
                    <span>Question</span>
                    <strong>{decision.question}</strong>
                    <span>Recommendation</span>
                    <strong>{decision.recommendation}</strong>
                    <small>
                      Owner {decision.decision_owner_position} · supersedes {shortId(decision.supersedes_decision_id)} · superseded by {shortId(decision.superseded_by_decision_id)}
                    </small>
                    <small>
                      Source {decision.source_object_type ?? "not recorded"} · {decision.source_object_id ?? "—"} · fingerprint {decision.record_fingerprint?.slice(0, 12) ?? "not recorded"}
                    </small>
                  </div>
                </details>
              ))}
            </div>
          ) : (
            <p>No ExecutiveDecision is linked to the current scene WorkItems.</p>
          )}
        </article>

        <article className={`living-scene-room owner-room${focusClass(["decisions", "blockers", "risk"])}`}>
          <header>
            <div><span>Owner inbox</span><strong>Required human actions</strong></div>
            <small>{scene.deterministic.human_actions.length}</small>
          </header>
          {scene.deterministic.human_actions.length ? (
            <div className="scene-decision-list">
              {scene.deterministic.human_actions.map((request) => (
                <details key={request.request_id}>
                  <summary>
                    <span>{titleCase(request.priority)} · {titleCase(request.status)} · {titleCase(request.request_type)}</span>
                    <strong>{request.title}</strong>
                    <small>{request.required_role} · Work {shortId(request.work_item_id)} · Blocker {shortId(request.blocker_id)}</small>
                  </summary>
                  <div>
                    <span>Instructions</span>
                    <strong>{request.instructions}</strong>
                    <small>Assigned human {request.assigned_human_id ?? "unassigned"} · Decision {shortId(request.decision_id)}</small>
                    <small>{request.canonical_basis}</small>
                  </div>
                </details>
              ))}
            </div>
          ) : (
            <p>No open OrganizationHumanActionRequest is linked to this scene.</p>
          )}
        </article>

        <article className={`living-scene-room risk-room${focusClass(["risk"])}`}>
          <header>
            <div><span>Escalation lane</span><strong>Open risk escalations</strong></div>
            <small>{scene.deterministic.risk_escalations.length}</small>
          </header>
          {scene.deterministic.risk_escalations.length ? (
            <div className="scene-blocker-list">
              {scene.deterministic.risk_escalations.map((risk) => (
                <div key={risk.risk_id}>
                  <span>
                    {titleCase(risk.severity)} · {titleCase(risk.category)} ·
                    {risk.requires_board_attention ? " Board attention" : " Delegated"}
                  </span>
                  <strong>{risk.title}</strong>
                  <small>{risk.description}</small>
                  <small>{risk.accountable_position_key} → {risk.escalated_to_position_key} · Evidence {risk.evidence_items.length}</small>
                </div>
              ))}
            </div>
          ) : (
            <p>No open RiskEscalation is linked to the current scene WorkItems.</p>
          )}
        </article>

        <article className={`living-scene-room blocker-room${focusClass(["blockers", "risk"])}`}>
          <header>
            <div><span>Friction lane</span><strong>Current blockers</strong></div>
            <small>{scene.deterministic.blockers.length}</small>
          </header>
          {scene.deterministic.blockers.length ? (
            <div className="scene-blocker-list">
              {scene.deterministic.blockers.map((blocker) => (
                <div key={blocker.blocker_id}>
                  <span>{titleCase(blocker.severity)} · {titleCase(blocker.status)} · {titleCase(blocker.blocker_type)}</span>
                  <strong>{blocker.title}</strong>
                  <small>{blocker.description}</small>
                  <small>
                    {blocker.requires_human_action ? "Human action required" : "No human action flag"} · Work {shortId(blocker.work_item_id)} · Accountable {blocker.accountable_position_key ?? "unassigned"}
                  </small>
                </div>
              ))}
            </div>
          ) : (
            <p>No active blocker is projected into this scene.</p>
          )}
        </article>
      </div>

      <div className="living-scene-smart-strip" aria-label="Living Organization Smart Objects">
        {scene.deterministic.smart_objects.map((item) => {
          const lensTags = smartObjectLensTags(item.object_type);
          return (
            <article
              key={item.object_key}
              className={focusClass(lensTags)}
              data-smart-object-state={item.state}
              data-lens-tags={lensTags.join(" ")}
            >
              <span>{titleCase(item.object_type)}</span>
              <strong>{item.label}</strong>
              <div><b>{item.metric_value ?? "—"}</b><small>{item.metric_label}</small></div>
              <p>{titleCase(item.state)} · {item.canonical_basis}</p>
            </article>
          );
        })}
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
