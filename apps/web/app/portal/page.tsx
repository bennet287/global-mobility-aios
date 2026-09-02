"use client";

import { Suspense } from "react";
import { ClientPortalPage } from "../../components/ClientPortalPage";


export default function PortalPage() {
  return (
    <Suspense fallback={<main className="client-portal"><div className="portal-loading">Opening workspace...</div></main>}>
      <ClientPortalPage />
    </Suspense>
  );
}
