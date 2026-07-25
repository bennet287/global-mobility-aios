"use client";

import { Suspense } from "react";

import { EcosystemPortalPage } from "../../components/EcosystemPortalPage";


export default function PartnerPortalPage() {
  return (
    <Suspense fallback={<main className="ecosystem-portal"><div className="ecosystem-loading">Opening workspace...</div></main>}>
      <EcosystemPortalPage />
    </Suspense>
  );
}
