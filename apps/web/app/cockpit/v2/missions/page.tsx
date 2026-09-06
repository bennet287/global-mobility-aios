import { Suspense } from "react";

import { V2MissionsWorkspace } from "../../../../components/v2/V2MissionsWorkspace";

export default function AiosV2MissionsPage() {
  return (
    <Suspense fallback={<p role="status">Opening Missions…</p>}>
      <V2MissionsWorkspace />
    </Suspense>
  );
}
