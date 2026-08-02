"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { EmptyState } from "../../components/EmptyState";
import { InlineNotice } from "../../components/InlineNotice";
import { SectionTitle } from "../../components/SectionTitle";
import { StatusBadge } from "../../components/StatusBadge";
import { Topbar } from "../../components/Topbar";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import {
  ApplicationAuthorityChecklistItem,
  ApplicationRecord,
  AuthorityChecklistTemplate,
  applyAuthorityChecklistTemplate,
  createApplicationAuthorityChecklistItem,
  createAuthorityChecklistTemplate,
  deleteApplicationAuthorityChecklistItem,
  emitAuthorityChecklistReminders,
  listApplicationAuthorityChecklistItems,
  listApplications,
  listAuthorityChecklistTemplates,
  updateApplicationAuthorityChecklistItemStatus,
} from "../../lib/api";
import { titleCase } from "../../lib/utils";

const categories: ApplicationAuthorityChecklistItem["category"][] = ["document", "fee", "form", "step"];
const itemStatuses: ApplicationAuthorityChecklistItem["status"][] = ["pending", "completed", "not_applicable"];

const emptyTemplateForm = {
  authority_name: "",
  country: "",
  item_key: "",
  item_label: "",
  category: "document" as ApplicationAuthorityChecklistItem["category"],
  is_required: true,
  sort_order: "0",
};

const emptyApplyForm = {
  authority_name: "",
};

const emptyManualItemForm = {
  authority_name: "",
  item_key: "",
  item_label: "",
  category: "document" as ApplicationAuthorityChecklistItem["category"],
  is_required: true,
  notes: "",
};

export default function AuthoritySubmissionChecklistPage() {
  const { health } = useBackendStatus();
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [templates, setTemplates] = useState<AuthorityChecklistTemplate[]>([]);
  const [items, setItems] = useState<ApplicationAuthorityChecklistItem[]>([]);
  const [selectedApplicationId, setSelectedApplicationId] = useState("");
  const [templateForm, setTemplateForm] = useState(emptyTemplateForm);
  const [applyForm, setApplyForm] = useState(emptyApplyForm);
  const [manualItemForm, setManualItemForm] = useState(emptyManualItemForm);
  const [itemNotes, setItemNotes] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [applicationRows, templateRows, itemRows] = await Promise.all([
        listApplications({ limit: 250 }),
        listAuthorityChecklistTemplates(),
        selectedApplicationId
          ? listApplicationAuthorityChecklistItems({ application_id: selectedApplicationId })
          : Promise.resolve([]),
      ]);
      setApplications(applicationRows);
      setTemplates(templateRows);
      setItems(itemRows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authority checklist workspace could not be loaded");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    if (!loading) void load();
  }, [selectedApplicationId]);

  const applicationNames = useMemo(
    () =>
      new Map(
        applications.map((app) => [
          app.id,
          `${app.domain.toUpperCase()} — ${app.target_country || "Unknown"} (${app.id.slice(0, 8)})`,
        ])
      ),
    [applications]
  );

  const templateAuthorities = useMemo(
    () => Array.from(new Set(templates.map((t) => t.authority_name))).sort(),
    [templates]
  );

  const groupedTemplates = useMemo(() => {
    const map = new Map<string, AuthorityChecklistTemplate[]>();
    for (const template of templates) {
      const list = map.get(template.authority_name) || [];
      list.push(template);
      map.set(template.authority_name, list);
    }
    for (const list of map.values()) {
      list.sort((a, b) => a.sort_order - b.sort_order || a.item_label.localeCompare(b.item_label));
    }
    return map;
  }, [templates]);

  const groupedItems = useMemo(() => {
    const map = new Map<string, ApplicationAuthorityChecklistItem[]>();
    for (const item of items) {
      const list = map.get(item.authority_name) || [];
      list.push(item);
      map.set(item.authority_name, list);
    }
    for (const list of map.values()) {
      list.sort((a, b) => a.item_label.localeCompare(b.item_label));
    }
    return map;
  }, [items]);

  async function submitTemplate(event: FormEvent) {
    event.preventDefault();
    if (!templateForm.authority_name || !templateForm.item_key || !templateForm.item_label) return;
    setWorking("template");
    setError(null);
    setMessage(null);
    try {
      await createAuthorityChecklistTemplate({
        authority_name: templateForm.authority_name,
        item_key: templateForm.item_key,
        item_label: templateForm.item_label,
        category: templateForm.category,
        is_required: templateForm.is_required,
        sort_order: Number(templateForm.sort_order) || 0,
        ...(templateForm.country ? { country: templateForm.country } : {}),
      });
      setTemplateForm(emptyTemplateForm);
      await load();
      setMessage(`Template item '${templateForm.item_label}' saved for ${templateForm.authority_name}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Template item could not be created");
    } finally {
      setWorking(null);
    }
  }

  async function applyTemplate(event: FormEvent) {
    event.preventDefault();
    if (!selectedApplicationId || !applyForm.authority_name) return;
    setWorking("apply");
    setError(null);
    setMessage(null);
    try {
      const created = await applyAuthorityChecklistTemplate(selectedApplicationId, applyForm.authority_name);
      setApplyForm(emptyApplyForm);
      await load();
      setMessage(`Applied ${created.length} checklist item(s) from ${applyForm.authority_name}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Template could not be applied");
    } finally {
      setWorking(null);
    }
  }

  async function submitManualItem(event: FormEvent) {
    event.preventDefault();
    if (
      !selectedApplicationId ||
      !manualItemForm.authority_name ||
      !manualItemForm.item_key ||
      !manualItemForm.item_label
    )
      return;
    setWorking("manual-item");
    setError(null);
    setMessage(null);
    try {
      await createApplicationAuthorityChecklistItem({
        application_id: selectedApplicationId,
        authority_name: manualItemForm.authority_name,
        item_key: manualItemForm.item_key,
        item_label: manualItemForm.item_label,
        category: manualItemForm.category,
        is_required: manualItemForm.is_required,
        ...(manualItemForm.notes ? { notes: manualItemForm.notes } : {}),
      });
      setManualItemForm(emptyManualItemForm);
      await load();
      setMessage("Manual checklist item added.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Checklist item could not be added");
    } finally {
      setWorking(null);
    }
  }

  async function changeItemStatus(item: ApplicationAuthorityChecklistItem, status: ApplicationAuthorityChecklistItem["status"]) {
    setWorking(item.id);
    setError(null);
    setMessage(null);
    try {
      await updateApplicationAuthorityChecklistItemStatus(
        item.id,
        status,
        itemNotes[item.id]?.trim() || undefined
      );
      setItemNotes((prev) => ({ ...prev, [item.id]: "" }));
      await load();
      setMessage(`'${item.item_label}' marked ${titleCase(status)}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Item status could not be updated");
    } finally {
      setWorking(null);
    }
  }

  async function removeItem(item: ApplicationAuthorityChecklistItem) {
    if (!confirm(`Delete '${item.item_label}' from the checklist?`)) return;
    setWorking(item.id);
    setError(null);
    setMessage(null);
    try {
      await deleteApplicationAuthorityChecklistItem(item.id);
      await load();
      setMessage(`'${item.item_label}' removed.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Checklist item could not be deleted");
    } finally {
      setWorking(null);
    }
  }

  async function sendReminders() {
    if (!selectedApplicationId) return;
    setWorking("reminders");
    setError(null);
    setMessage(null);
    try {
      const events = await emitAuthorityChecklistReminders(selectedApplicationId);
      await load();
      setMessage(`Emitted ${events.length} reminder event(s) for pending checklist items.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reminders could not be sent");
    } finally {
      setWorking(null);
    }
  }

  const loadStatus = health?.status === "ok" ? (loading ? "loading" : "ready") : "offline";

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title="Authority Submission Checklist"
        kicker="Per-authority templates and application checklists"
        loadStatus={loadStatus}
        onRefresh={() => void load()}
      />

      <div className="workspace-body">
        <div className="workspace-grid two-col">
          <section className="panel">
            <SectionTitle
              label="Templates"
              title="Manage authority checklist templates"
              detail="Define reusable documents, fees, forms, and procedural steps per authority. Templates are applied idempotently to applications."
            />
            <form onSubmit={submitTemplate} className="form-card">
              <label className="field">
                <span className="field-label">Authority name</span>
                <input
                  className="input"
                  type="text"
                  required
                  placeholder="German Consulate Mumbai"
                  value={templateForm.authority_name}
                  onChange={(e) => setTemplateForm((f) => ({ ...f, authority_name: e.target.value }))}
                />
              </label>

              <div className="form-row">
                <label className="field">
                  <span className="field-label">Item key</span>
                  <input
                    className="input"
                    type="text"
                    required
                    placeholder="passport_copy"
                    value={templateForm.item_key}
                    onChange={(e) => setTemplateForm((f) => ({ ...f, item_key: e.target.value }))}
                  />
                </label>

                <label className="field">
                  <span className="field-label">Sort order</span>
                  <input
                    className="input"
                    type="number"
                    min={0}
                    value={templateForm.sort_order}
                    onChange={(e) => setTemplateForm((f) => ({ ...f, sort_order: e.target.value }))}
                  />
                </label>
              </div>

              <label className="field">
                <span className="field-label">Item label</span>
                <input
                  className="input"
                  type="text"
                  required
                  placeholder="Passport copy (bio page)"
                  value={templateForm.item_label}
                  onChange={(e) => setTemplateForm((f) => ({ ...f, item_label: e.target.value }))}
                />
              </label>

              <div className="form-row">
                <label className="field">
                  <span className="field-label">Category</span>
                  <select
                    className="input"
                    value={templateForm.category}
                    onChange={(e) =>
                      setTemplateForm((f) => ({ ...f, category: e.target.value as ApplicationAuthorityChecklistItem["category"] }))
                    }
                  >
                    {categories.map((c) => (
                      <option key={c} value={c}>
                        {titleCase(c)}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="field">
                  <span className="field-label">Country</span>
                  <input
                    className="input"
                    type="text"
                    placeholder="Germany"
                    value={templateForm.country}
                    onChange={(e) => setTemplateForm((f) => ({ ...f, country: e.target.value }))}
                  />
                </label>
              </div>

              <label className="field checkbox">
                <input
                  type="checkbox"
                  checked={templateForm.is_required}
                  onChange={(e) => setTemplateForm((f) => ({ ...f, is_required: e.target.checked }))}
                />
                <span>Required by default</span>
              </label>

              <div className="form-actions">
                <button className="button primary" type="submit" disabled={working === "template"}>
                  {working === "template" ? <span className="button-spinner" aria-hidden="true" /> : "Save template item"}
                </button>
              </div>
            </form>

            <div className="panel-section">
              <h3>Template library</h3>
              {templates.length === 0 ? (
                <EmptyState title="No templates" detail="Create the first checklist template item using the form above." />
              ) : (
                <div className="template-groups">
                  {templateAuthorities.map((authority) => (
                    <div key={authority} className="template-group">
                      <h4>{authority}</h4>
                      <ul className="data-list compact">
                        {groupedTemplates.get(authority)?.map((template) => (
                          <li key={template.id} className="data-list-item">
                            <div className="data-list-row">
                              <div>
                                <strong className="data-list-title">{template.item_label}</strong>
                                <span className="data-list-meta">
                                  {titleCase(template.category)}
                                  {template.is_required ? " · Required" : " · Optional"}
                                  {template.country ? ` · ${template.country}` : null}
                                </span>
                              </div>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section className="panel">
            <SectionTitle
              label="Application checklist"
              title="Track items per application"
              detail="Select an application, apply an authority template, add manual items, and update statuses. Send reminders for pending required items."
            />

            <label className="field">
              <span className="field-label">Application</span>
              <select
                className="input"
                value={selectedApplicationId}
                onChange={(e) => setSelectedApplicationId(e.target.value)}
              >
                <option value="">Select an application…</option>
                {applications.map((app) => (
                  <option key={app.id} value={app.id}>
                    {applicationNames.get(app.id)}
                  </option>
                ))}
              </select>
            </label>

            {error && <InlineNotice label="Error" detail={error} tone="bad" />}
            {message && <InlineNotice label="Success" detail={message} tone="good" />}

            {selectedApplicationId && (
              <>
                <form onSubmit={applyTemplate} className="form-card inline">
                  <div className="form-row">
                    <label className="field">
                      <span className="field-label">Apply template authority</span>
                      <input
                        className="input"
                        type="text"
                        list="template-authorities"
                        required
                        placeholder="German Consulate Mumbai"
                        value={applyForm.authority_name}
                        onChange={(e) => setApplyForm((f) => ({ ...f, authority_name: e.target.value }))}
                      />
                      <datalist id="template-authorities">
                        {templateAuthorities.map((name) => (
                          <option key={name} value={name} />
                        ))}
                      </datalist>
                    </label>
                    <button className="button primary" type="submit" disabled={working === "apply"}>
                      {working === "apply" ? <span className="button-spinner" aria-hidden="true" /> : "Apply"}
                    </button>
                  </div>
                </form>

                <form onSubmit={submitManualItem} className="form-card inline">
                  <h4>Add manual item</h4>
                  <label className="field">
                    <span className="field-label">Authority name</span>
                    <input
                      className="input"
                      type="text"
                      required
                      placeholder="German Consulate Mumbai"
                      value={manualItemForm.authority_name}
                      onChange={(e) => setManualItemForm((f) => ({ ...f, authority_name: e.target.value }))}
                    />
                  </label>
                  <div className="form-row">
                    <label className="field">
                      <span className="field-label">Item key</span>
                      <input
                        className="input"
                        type="text"
                        required
                        placeholder="custom_item_1"
                        value={manualItemForm.item_key}
                        onChange={(e) => setManualItemForm((f) => ({ ...f, item_key: e.target.value }))}
                      />
                    </label>
                    <label className="field">
                      <span className="field-label">Category</span>
                      <select
                        className="input"
                        value={manualItemForm.category}
                        onChange={(e) =>
                          setManualItemForm((f) => ({ ...f, category: e.target.value as ApplicationAuthorityChecklistItem["category"] }))
                        }
                      >
                        {categories.map((c) => (
                          <option key={c} value={c}>
                            {titleCase(c)}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>
                  <label className="field">
                    <span className="field-label">Item label</span>
                    <input
                      className="input"
                      type="text"
                      required
                      placeholder="Additional letter of explanation"
                      value={manualItemForm.item_label}
                      onChange={(e) => setManualItemForm((f) => ({ ...f, item_label: e.target.value }))}
                    />
                  </label>
                  <label className="field checkbox">
                    <input
                      type="checkbox"
                      checked={manualItemForm.is_required}
                      onChange={(e) => setManualItemForm((f) => ({ ...f, is_required: e.target.checked }))}
                    />
                    <span>Required</span>
                  </label>
                  <label className="field">
                    <span className="field-label">Notes</span>
                    <textarea
                      className="input"
                      rows={2}
                      value={manualItemForm.notes}
                      onChange={(e) => setManualItemForm((f) => ({ ...f, notes: e.target.value }))}
                    />
                  </label>
                  <div className="form-actions">
                    <button className="button secondary" type="submit" disabled={working === "manual-item"}>
                      {working === "manual-item" ? <span className="button-spinner" aria-hidden="true" /> : "Add manual item"}
                    </button>
                  </div>
                </form>

                <div className="panel-section">
                  <div className="section-header">
                    <h3>Checklist items</h3>
                    <button
                      className="button small secondary"
                      type="button"
                      disabled={working === "reminders"}
                      onClick={() => void sendReminders()}
                    >
                      {working === "reminders" ? <span className="button-spinner" aria-hidden="true" /> : "Send reminders"}
                    </button>
                  </div>
                  {items.length === 0 ? (
                    <EmptyState
                      title="No checklist items"
                      detail="Apply a template or add manual items for this application."
                    />
                  ) : (
                    <div className="template-groups">
                      {Array.from(groupedItems.keys()).map((authority) => (
                        <div key={authority} className="template-group">
                          <h4>{authority}</h4>
                          <ul className="data-list compact">
                            {groupedItems.get(authority)?.map((item) => (
                              <li key={item.id} className="data-list-item">
                                <div className="data-list-row">
                                  <div>
                                    <strong className="data-list-title">{item.item_label}</strong>
                                    <span className="data-list-meta">
                                      {titleCase(item.category)}
                                      {item.is_required ? " · Required" : " · Optional"}
                                    </span>
                                  </div>
                                  <StatusBadge value={item.status} />
                                </div>
                                {item.notes ? <p className="data-list-detail">{item.notes}</p> : null}
                                <label className="field slim">
                                  <span className="field-label">Notes</span>
                                  <input
                                    className="input"
                                    type="text"
                                    placeholder="Update notes while changing status"
                                    value={itemNotes[item.id] || ""}
                                    onChange={(e) =>
                                      setItemNotes((prev) => ({ ...prev, [item.id]: e.target.value }))
                                    }
                                  />
                                </label>
                                <div className="data-list-actions">
                                  <div className="button-group">
                                    {itemStatuses.map((status) => (
                                      <button
                                        key={status}
                                        className={`button small ${item.status === status ? "secondary" : "ghost"}`}
                                        type="button"
                                        disabled={working === item.id}
                                        onClick={() => void changeItemStatus(item, status)}
                                      >
                                        {titleCase(status)}
                                      </button>
                                    ))}
                                  </div>
                                  <button
                                    className="button small bad"
                                    type="button"
                                    disabled={working === item.id}
                                    onClick={() => void removeItem(item)}
                                  >
                                    Delete
                                  </button>
                                </div>
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </section>
        </div>
      </div>
    </WorkspaceShell>
  );
}
