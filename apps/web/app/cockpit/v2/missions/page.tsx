import { Suspense } from "react";
import { V2MissionsWorkspace } from "../../../../components/v2/V2MissionsWorkspace";

export default function Page() {
  return <Suspense fallback={<p role="status">Loading workspace?</p>}><V2MissionsWorkspace /></Suspense>;
}
