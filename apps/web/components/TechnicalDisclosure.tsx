import { ReactNode, useId } from "react";

export function TechnicalDisclosure({
  children,
  label = "Technical provenance",
  detail,
  open = false,
}: {
  children: ReactNode;
  label?: string;
  detail?: string;
  open?: boolean;
}) {
  const contentId = useId();

  return (
    <details className="technical-disclosure" open={open}>
      <summary aria-controls={contentId}>
        <span>{label}</span>
        {detail ? <small>{detail}</small> : null}
      </summary>
      <div id={contentId} className="technical-disclosure-content">
        {children}
      </div>
    </details>
  );
}
