import type { Metadata } from "next";


export const metadata: Metadata = {
  title: "GMAI | Employer & Partner Workspace",
  description: "A secure tenant-scoped view of corporate mobility cases and compliance activity.",
};

export default function PartnerPortalLayout({ children }: { children: React.ReactNode }) {
  return children;
}
