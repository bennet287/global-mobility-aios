import { ApplicationQueue, TruthResolutionQueue } from "../lib/api";
import { EmptyState } from "./EmptyState";
import { StatusBadge } from "./StatusBadge";
import { titleCase } from "../lib/utils";

export function QueueStages({ queue }: { queue: TruthResolutionQueue | ApplicationQueue | null }) {
  const stages = Object.entries(queue?.stage_counts || {});
  if (!stages.length) {
    return <EmptyState title="No stage data" detail="Run demo seed data or create a lead to populate this workflow." />;
  }
  return (
    <div className="stage-list">
      {stages.slice(0, 6).map(([stage, count]) => (
        <div className="stage-row" key={stage}>
          <div>
            <strong>{titleCase(stage)}</strong>
            <span>
              {count} case{count === 1 ? "" : "s"}
            </span>
          </div>
          <StatusBadge value={stage} />
        </div>
      ))}
    </div>
  );
}
