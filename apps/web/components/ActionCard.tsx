import { Tone } from "../lib/utils";

export type ActionItem = {
  label: string;
  title: string;
  detail: string;
  tone: Tone;
  href?: string;
};

export function ActionCard({ action }: { action: ActionItem }) {
  return (
    <a className={`action-card ${action.tone}`} href={action.href} target="_blank" rel="noreferrer">
      <span>{action.label}</span>
      <strong>{action.title}</strong>
      <p>{action.detail}</p>
    </a>
  );
}
