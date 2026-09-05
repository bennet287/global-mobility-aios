import { Suspense } from "react";
import { V2IntelligenceWorkspace } from "../../../../components/v2/V2IntelligenceWorkspace";

export default function Page() {
  return <Suspense fallback={<p role="status">Loading workspace?</p>}><V2IntelligenceWorkspace /></Suspense>;
}
