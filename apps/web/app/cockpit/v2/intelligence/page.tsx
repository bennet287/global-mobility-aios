import { Suspense } from "react";

import { V2IntelligenceWorkspace } from "../../../../components/v2/V2IntelligenceWorkspace";

export default function AiosV2IntelligencePage() {
  return (
    <Suspense fallback={<p role="status">Opening Intelligence…</p>}>
      <V2IntelligenceWorkspace />
    </Suspense>
  );
}
