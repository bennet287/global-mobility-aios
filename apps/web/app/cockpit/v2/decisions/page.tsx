import { Suspense } from "react";
import { V2DecisionsWorkspace } from "../../../../components/v2/V2DecisionsWorkspace";

export default function Page() {
  return <Suspense fallback={<p role="status">Loading workspace?</p>}><V2DecisionsWorkspace /></Suspense>;
}
