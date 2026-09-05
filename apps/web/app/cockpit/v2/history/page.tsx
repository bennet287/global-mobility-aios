import { Suspense } from "react";
import { V2HistoryWorkspace } from "../../../../components/v2/V2HistoryWorkspace";

export default function Page() {
  return <Suspense fallback={<p role="status">Loading workspace?</p>}><V2HistoryWorkspace /></Suspense>;
}
