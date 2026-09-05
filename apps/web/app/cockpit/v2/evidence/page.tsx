import { Suspense } from "react";
import { V2EvidenceWorkspace } from "../../../../components/v2/V2EvidenceWorkspace";

export default function Page() {
  return <Suspense fallback={<p role="status">Loading workspace?</p>}><V2EvidenceWorkspace /></Suspense>;
}
