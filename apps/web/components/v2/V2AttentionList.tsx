import Link from "next/link";

import type { V2AttentionItem } from "../../lib/v2/owner-organization";

function attentionLabel(kind: V2AttentionItem["kind"]): string {
  if (kind === "decision") return "Decision";
  if (kind === "human_action") return "Human action";
  if (kind === "blocker") return "Blocker";
  return "Risk";
}

export function V2AttentionList({
  items,
  loading,
}: {
  items: V2AttentionItem[];
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="aios-v2-attention-empty" role="status">
        <strong>Reading governed attention signals…</strong>
        <p>Board, human-action and blocker records are loading.</p>
      </div>
    );
  }

  if (!items.length) {
    return (
      <div className="aios-v2-attention-empty" role="status">
        <strong>No current attention item was returned.</strong>
        <p>This is a canonical zero state from the connected sources, not a placeholder success claim.</p>
      </div>
    );
  }

  return (
    <div className="aios-v2-attention-list" aria-label="Current organization attention">
      {items.slice(0, 5).map((item) => (
        <Link
          className="aios-v2-attention-object"
          data-kind={item.kind}
          data-urgency={item.urgency}
          href={item.href}
          key={item.id}
        >
          <span className="aios-v2-attention-object-meta">
            <span>{attentionLabel(item.kind)}</span>
            <span>{item.urgency}</span>
          </span>
          <strong>{item.title}</strong>
          <small>{item.detail}</small>
        </Link>
      ))}
    </div>
  );
}
