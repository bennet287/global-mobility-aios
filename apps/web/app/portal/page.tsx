"use client";

import Link from "next/link";
import { Suspense } from "react";
import { ClientPortalPage } from "../../components/ClientPortalPage";
import styles from "./mobility-convergence.module.css";

export default function PortalPage() {
  return (
    <div className={styles.shell}>
      <nav className={styles.navigation} aria-label="My Case workspace navigation">
        <Link href="/my-mobility">Overview</Link>
        <span aria-current="page">My Case</span>
        <Link href="/portal/documents">Documents</Link>
        <Link href="/portal/timeline">Timeline</Link>
        <Link href="/portal/messages">Messages</Link>
      </nav>
      <Suspense fallback={<main className="client-portal"><div className="portal-loading">Opening workspace...</div></main>}>
        <ClientPortalPage />
      </Suspense>
    </div>
  );
}
