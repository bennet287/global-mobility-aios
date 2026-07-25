import type { Metadata } from "next";


export const metadata: Metadata = {
  title: "GMAI | Private Client Workspace",
  description: "A secure, expiring view of your mobility case progress and document status.",
};

export default function PortalLayout({ children }: { children: React.ReactNode }) {
  return children;
}
