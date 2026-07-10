import { ReactNode } from "react";
import { HealthStatus } from "../lib/api";
import { Sidebar } from "./Sidebar";

export function WorkspaceShell({
  children,
  health,
}: {
  children: ReactNode;
  health: HealthStatus | null;
}) {
  return (
    <main className="app-frame">
      <Sidebar health={health} />
      <section className="workspace">{children}</section>
    </main>
  );
}
