import { notFound } from "next/navigation";

import { V2OrganizationWingWorkspace } from "../../../../../../components/v2/V2OrganizationWingWorkspace";
import { isKnownWingKey } from "../../../../../../lib/v2/hq-visual-presentation";

export default async function AiosV2OrganizationWingPage({
  params,
}: {
  readonly params: Promise<{ wingKey: string }>;
}) {
  const { wingKey } = await params;
  if (!isKnownWingKey(wingKey)) notFound();

  return <V2OrganizationWingWorkspace wingKey={wingKey} />;
}
