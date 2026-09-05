"use client";
import Link from "next/link";
import { useState } from "react";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import { workspaceNavigation } from "../../lib/workspace-navigation";
import { EmptyState, V2PageHeader, v2Styles as s } from "../../components/v2/V2Primitives";

export default function ToolsPage() {
  const { health } = useBackendStatus();
  const [query, setQuery] = useState("");
  const groups = workspaceNavigation.operator.map((group) => ({ ...group, items: group.items.filter((item) => item.label.toLowerCase().includes(query.toLowerCase())) }));
  return <WorkspaceShell health={health}>
    <V2PageHeader eyebrow="Professional workspace" title="Tools" description="Open the specialist tool your work requires. Each workflow keeps its own review and authority controls." />
    <div className={s.toolbar}><label>Find a tool<input type="search" value={query} onChange={(event) => setQuery(event.target.value)} /></label></div>
    {groups.some((group) => group.items.length) ? groups.filter((group) => group.items.length).map((group) => <section key={group.label} className={s.detail}><h2>{group.label}</h2><ul className={s.list}>{group.items.map((item) => <li key={item.href}><Link className={s.row} href={item.href}><strong>{item.label}</strong><span aria-hidden="true">→</span></Link></li>)}</ul></section>) : <EmptyState title="No tools match" detail="Try a shorter name or clear the search." />}
  </WorkspaceShell>;
}
