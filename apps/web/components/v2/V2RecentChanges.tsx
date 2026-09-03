import type { V2RecentChange } from "../../lib/v2/owner-organization";

function activityTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "time unavailable";
  return date.toISOString().slice(0, 16).replace("T", " ") + " UTC";
}

export function V2RecentChanges({
  changes,
  loading,
}: {
  changes: V2RecentChange[];
  loading: boolean;
}) {
  return (
    <section className="aios-v2-recent" aria-labelledby="aios-v2-recent-title">
      <header className="aios-v2-section-heading">
        <div>
          <span>Activity</span>
          <strong id="aios-v2-recent-title">Recent meaningful change</strong>
        </div>
      </header>

      {loading ? (
        <div className="aios-v2-empty-line" role="status">Loading canonical Activity…</div>
      ) : changes.length ? (
        <ol className="aios-v2-recent-list">
          {changes.map((change) => (
            <li key={change.id}>
              <div className="aios-v2-recent-marker" aria-hidden="true" />
              <div>
                <strong>{change.title}</strong>
                <p>{change.summary}</p>
                <small>
                  {change.activityClass.replaceAll("_", " ")}
                  {change.department ? " · " + change.department : ""}
                  {" · " + activityTime(change.occurredAt)}
                </small>
              </div>
            </li>
          ))}
        </ol>
      ) : (
        <div className="aios-v2-empty-line" role="status">No Activity records were returned.</div>
      )}
    </section>
  );
}
