import type { V2RecentChange } from "../../lib/v2/owner-organization";

function relativeTime(value: string): string {
  const timestamp = new Date(value).getTime();
  if (!Number.isFinite(timestamp)) return "time unavailable";
  const diffMinutes = Math.max(0, Math.round((Date.now() - timestamp) / 60000));
  if (diffMinutes < 1) return "just now";
  if (diffMinutes < 60) return String(diffMinutes) + "m ago";
  const hours = Math.round(diffMinutes / 60);
  if (hours < 24) return String(hours) + "h ago";
  const days = Math.round(hours / 24);
  return String(days) + "d ago";
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
                  {" · " + relativeTime(change.occurredAt)}
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
