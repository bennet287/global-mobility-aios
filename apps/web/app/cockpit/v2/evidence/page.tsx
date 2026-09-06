import { Suspense } from "react";

import { V2EvidenceWorkspace } from "../../../../components/v2/V2EvidenceWorkspace";

export default function AiosV2EvidencePage() {
  return (
    <Suspense fallback={<p role="status">Opening Evidence…</p>}>
      <V2EvidenceWorkspace />
    </Suspense>
  );
}
