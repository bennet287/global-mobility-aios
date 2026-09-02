export type EvidenceProvenanceTone = "good" | "warn" | "bad" | "neutral";

export type EvidenceProvenanceItem = {
  key: string;
  stage: string;
  title: string;
  state: string;
  detail: string;
  meta?: string;
  tone?: EvidenceProvenanceTone;
  current?: boolean;
};

export function EvidenceProvenance({
  title,
  detail,
  items,
  boundary,
}: {
  title: string;
  detail: string;
  items: EvidenceProvenanceItem[];
  boundary: string;
}) {
  return (
    <section className="evidence-provenance" aria-label={title}>
      <div className="evidence-provenance-heading">
        <div>
          <span className="page-kicker">Evidence provenance</span>
          <h3>{title}</h3>
          <p>{detail}</p>
        </div>
        <span className="evidence-provenance-count">{items.length} states</span>
      </div>

      <div className="evidence-provenance-grid" role="list">
        {items.map((item, index) => (
          <article
            className="evidence-provenance-card"
            data-tone={item.tone || "neutral"}
            data-current={item.current ? "true" : "false"}
            role="listitem"
            aria-current={item.current ? "true" : undefined}
            key={item.key}
          >
            <div className="evidence-provenance-topline">
              <span className="evidence-provenance-stage">
                {String(index + 1).padStart(2, "0")} · {item.stage}
              </span>
              <span className="evidence-provenance-state">{item.state}</span>
            </div>
            <strong>{item.title}</strong>
            <p>{item.detail}</p>
            {item.meta ? <small>{item.meta}</small> : null}
          </article>
        ))}
      </div>

      <div className="evidence-provenance-boundary" role="note">
        <strong>Evidence boundary</strong>
        <span>{boundary}</span>
      </div>
    </section>
  );
}
