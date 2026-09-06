import { Suspense } from "react";

import { V2HistoryWorkspace } from "../../../../components/v2/V2HistoryWorkspace";

export default function AiosV2HistoryPage() {
  return (
    <Suspense fallback={<p role="status">Opening History…</p>}>
      <V2HistoryWorkspace />
    </Suspense>
  );
}
